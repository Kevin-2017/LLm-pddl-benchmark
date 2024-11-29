'''
import re
import argparse
import sys
import os
import logging
from contextlib import redirect_stderr
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect
from tarski.syntax.formulas import Atom

# 配置日志记录，仅显示 ERROR 级别及以上的日志
logging.basicConfig(level=logging.ERROR, format='%(levelname)s:%(message)s')

# Helper function to get term name with substitution
def get_term_name(term, var_mapping):
    if hasattr(term, 'symbol'):  # 'symbol' 用于标识参数符号
        term_name = term.symbol
        # 如果参数名称以 '?' 开头，则移除 '?'
        if term_name.startswith('?'):
            term_name = term_name[1:]
        substituted = var_mapping.get(term_name, term_name)
        return substituted
    else:
        return str(term)

# Function to load and parse PDDL domain and problem files
def load_pddl_files(domain_file, problem_file):
    reader = FstripsReader()
    try:
        with open(os.devnull, 'w') as devnull:
            with redirect_stderr(devnull):
                reader.parse_domain(domain_file)
    except Exception:
        # 如果解析域文件失败，静默退出
        sys.exit(1)
    try:
        with open(os.devnull, 'w') as devnull:
            with redirect_stderr(devnull):
                reader.read_problem(problem_file, instance=problem_file)
    except Exception:
        # 如果读取问题文件失败，静默退出
        sys.exit(1)
    return reader

# Initialize the state tracker from initial facts in the problem
def initialize_state_tracker(problem):
    predicates_state = set()
    functions_state = {}
    for fact in problem.init.as_atoms():
        if isinstance(fact, tuple):
            # Handle predicate tuples
            if len(fact) == 2 and isinstance(fact[0], str) and isinstance(fact[1], tuple):
                predicate, arguments = fact
                predicates_state.add((predicate, arguments))
            # Handle function assignments like ('=', ('total-cost',), 0.0)
            elif len(fact) == 3 and fact[0] == '=' and isinstance(fact[1], tuple):
                function = fact[1][0]  # Extract function name
                try:
                    value = float(fact[2])
                except (ValueError, TypeError):
                    value = fact[2]
                functions_state[function] = value
            else:
                pass  # Ignore other formats
        elif isinstance(fact, Atom):
            predicate = fact.predicate.symbol
            arguments = tuple(get_term_name(arg, {}) for arg in fact.subterms)
            predicates_state.add((predicate, arguments))
        else:
            pass  # Ignore other formats
    return predicates_state, functions_state

# Function to print the current state in the desired format
def print_current_state(step, predicates_state, functions_state):
    # Uncomment the next line if you want to display the step number as a comment
    # print(f"; Step {step}")
    
    for fact in sorted(predicates_state, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        # Format: (predicate arg1 arg2 ...)
        print(f"({predicate} {' '.join(args)})")
    
    for func, val in functions_state.items():
        # Format: (function-name value)
        print(f"({func} {val})")
    
    print()  # Add a newline for separation between steps or final state

# Function to load the plan file and extract actions
def load_plan_file(plan_file):
    actions = []
    try:
        with open(plan_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith(';') or not line:
                    continue
                match = re.match(r"\((\w+)\s+([^\)]+)\)", line)
                if match:
                    action_name = match.group(1)
                    params = match.group(2).strip().split()
                    actions.append((action_name, params))
                else:
                    pass  # Ignore unrecognized action formats silently
    except Exception:
        # 如果计划文件读取失败，静默退出
        sys.exit(1)
    return actions

# Function to apply an action to the current state
def apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping):
    for effect in action_obj.effects:
        # Add positive effects (AddEffect) to the state
        if isinstance(effect, AddEffect):
            predicate = effect.atom.predicate.symbol
            # Retrieve each subterm's name, handling variables
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            predicates_state.add((predicate, arguments))

        # Remove negative effects (DelEffect) from the state
        elif isinstance(effect, DelEffect):
            predicate = effect.atom.predicate.symbol
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            predicates_state.discard((predicate, arguments))

        # Handle function effects like (increase (total-cost) 5) or (assign (total-cost) 10)
        elif isinstance(effect, tuple) and len(effect) >= 3 and effect[0] in ('increase', 'decrease', 'assign'):
            operation = effect[0]
            function = effect[1][0]  # Assuming the function is the first element in the second tuple
            try:
                value = float(effect[2]) if isinstance(effect[2], (int, float, str)) else effect[2]
            except ValueError:
                value = effect[2]
            if function not in functions_state:
                functions_state[function] = 0.0  # Initialize if not present
            if operation == 'increase':
                functions_state[function] += value
            elif operation == 'decrease':
                functions_state[function] -= value
            elif operation == 'assign':
                functions_state[function] = value
        else:
            # Check if the effect is an equality Atom
            if isinstance(effect, Atom) and effect.predicate.symbol == '=':
                # Handle equality assignment
                if len(effect.subterms) == 2:
                    function_term, value_term = effect.subterms
                    function = get_term_name(function_term, var_mapping)
                    try:
                        value = float(value_term)
                    except ValueError:
                        value = get_term_name(value_term, var_mapping)
                    functions_state[function] = value
            else:
                pass  # Ignore other formats
    return predicates_state, functions_state

# Main function to execute the plan and print final state
def main(domain_file, problem_file, plan_file):
    reader = load_pddl_files(domain_file, problem_file)
    problem = reader.problem

    # Initialize state tracker
    predicates_state, functions_state = initialize_state_tracker(problem)

    # Load plan actions
    plan_actions = load_plan_file(plan_file)

    # Execute plan actions without printing intermediate steps
    for step, (action_name, params) in enumerate(plan_actions, start=1):
        # Access actions as a dictionary
        domain_actions = problem.actions
        if action_name in domain_actions:
            action_obj = domain_actions[action_name]

            # Obtain action variables using 'symbol'
            action_vars = [var.symbol for var in action_obj.parameters]

            # Build variable mapping between action parameters and plan arguments
            if len(action_vars) != len(params):
                var_mapping = {}
            else:
                var_mapping = {var.lstrip('?'): param for var, param in zip(action_vars, params)}

            # Apply the action with variable mapping
            predicates_state, functions_state = apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping)
        else:
            # 如果动作未在域中定义，忽略并继续
            pass

    # After all actions have been applied, print the final state if there are actions
    if plan_actions:
        print_current_state(len(plan_actions), predicates_state, functions_state)
    else:
        print("\nNo actions to execute.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDDL Plan Executor")
    parser.add_argument("domain_file", type=str, help="Path to PDDL domain file (domain.pddl)")
    parser.add_argument("problem_file", type=str, help="Path to PDDL problem file (problem.pddl)")
    parser.add_argument("plan_file", type=str, help="Path to plan file (plan.pddl)")

    args = parser.parse_args()

    main(args.domain_file, args.problem_file, args.plan_file)
'''
'''
import re
import argparse
import sys
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect
from tarski.syntax.formulas import Atom

# 移除或注释掉 logging 配置
# import logging
# logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')

# Helper function to get term name with substitution
def get_term_name(term, var_mapping):
    if hasattr(term, 'symbol'):  # 'symbol' is used to identify parameter symbols
        term_name = term.symbol
        # If the parameter name starts with '?', remove '?'
        if term_name.startswith('?'):
            term_name = term_name[1:]
        substituted = var_mapping.get(term_name, term_name)
        return substituted
    else:
        return str(term)

# Function to load and parse PDDL domain and problem files
def load_pddl_files(domain_file, problem_file):
    reader = FstripsReader()
    try:
        reader.parse_domain(domain_file)
    except Exception:
        # 如果解析域文件失败，静默退出
        sys.exit(1)
    try:
        reader.read_problem(problem_file, instance=problem_file)
    except Exception:
        # 如果读取问题文件失败，静默退出
        sys.exit(1)
    return reader

# Initialize the state tracker from initial facts in the problem
def initialize_state_tracker(problem):
    predicates_state = set()
    functions_state = {}
    for fact in problem.init.as_atoms():
        if isinstance(fact, tuple):
            # Handle predicate tuples
            if len(fact) == 2 and isinstance(fact[0], str) and isinstance(fact[1], tuple):
                predicate, arguments = fact
                predicates_state.add((predicate, arguments))
            # Handle function assignments like ('=', ('total-cost',), 0.0)
            elif len(fact) == 3 and fact[0] == '=' and isinstance(fact[1], tuple):
                function = fact[1][0]  # Extract function name
                try:
                    value = float(fact[2])
                except (ValueError, TypeError):
                    value = fact[2]
                functions_state[function] = value
            else:
                pass  # Ignore other formats
        elif isinstance(fact, Atom):
            predicate = fact.predicate.symbol
            arguments = tuple(get_term_name(arg, {}) for arg in fact.subterms)
            predicates_state.add((predicate, arguments))
        else:
            pass  # Ignore other formats
    return predicates_state, functions_state

# Function to print the current state in the desired format
def print_current_state(step, predicates_state, functions_state):
    # Uncomment the next line if you want to display the step number as a comment
    # print(f"; Step {step}")
    
    for fact in sorted(predicates_state, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        # Format: (predicate arg1 arg2 ...)
        print(f"({predicate} {' '.join(args)})")
    
    for func, val in functions_state.items():
        # Format: (function-name value)
        print(f"({func} {val})")
    
    print()  # Add a newline for separation between steps or final state

# Function to load the plan file and extract actions
def load_plan_file(plan_file):
    actions = []
    try:
        with open(plan_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith(';') or not line:
                    continue
                match = re.match(r"\((\w+)\s+([^\)]+)\)", line)
                if match:
                    action_name = match.group(1)
                    params = match.group(2).strip().split()
                    actions.append((action_name, params))
                else:
                    pass  # Ignore unrecognized action formats silently
    except Exception:
        # 如果计划文件读取失败，静默退出
        sys.exit(1)
    return actions

# Function to apply an action to the current state
def apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping):
    for effect in action_obj.effects:
        # Add positive effects (AddEffect) to the state
        if isinstance(effect, AddEffect):
            predicate = effect.atom.predicate.symbol
            # Retrieve each subterm's name, handling variables
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            predicates_state.add((predicate, arguments))

        # Remove negative effects (DelEffect) from the state
        elif isinstance(effect, DelEffect):
            predicate = effect.atom.predicate.symbol
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            predicates_state.discard((predicate, arguments))

        # Handle function effects like (increase (total-cost) 5) or (assign (total-cost) 10)
        elif isinstance(effect, tuple) and len(effect) >= 3 and effect[0] in ('increase', 'decrease', 'assign'):
            operation = effect[0]
            function = effect[1][0]  # Assuming the function is the first element in the second tuple
            try:
                value = float(effect[2]) if isinstance(effect[2], (int, float, str)) else effect[2]
            except ValueError:
                value = effect[2]
            if function not in functions_state:
                functions_state[function] = 0.0  # Initialize if not present
            if operation == 'increase':
                functions_state[function] += value
            elif operation == 'decrease':
                functions_state[function] -= value
            elif operation == 'assign':
                functions_state[function] = value
        else:
            # Check if the effect is an equality Atom
            if isinstance(effect, Atom) and effect.predicate.symbol == '=':
                # Handle equality assignment
                if len(effect.subterms) == 2:
                    function_term, value_term = effect.subterms
                    function = get_term_name(function_term, var_mapping)
                    try:
                        value = float(value_term)
                    except ValueError:
                        value = get_term_name(value_term, var_mapping)
                    functions_state[function] = value
            else:
                pass  # Ignore other formats
    return predicates_state, functions_state

# Main function to execute the plan and print final state
def main(domain_file, problem_file, plan_file):
    reader = load_pddl_files(domain_file, problem_file)
    problem = reader.problem

    # Initialize state tracker
    predicates_state, functions_state = initialize_state_tracker(problem)

    # Load plan actions
    plan_actions = load_plan_file(plan_file)

    # Execute plan actions
    for step, (action_name, params) in enumerate(plan_actions, start=1):
        # Access actions as a dictionary
        domain_actions = problem.actions
        if action_name in domain_actions:
            action_obj = domain_actions[action_name]

            # Obtain action variables using 'symbol'
            action_vars = [var.symbol for var in action_obj.parameters]

            # Build variable mapping between action parameters and plan arguments
            if len(action_vars) != len(params):
                var_mapping = {}
            else:
                var_mapping = {var.lstrip('?'): param for var, param in zip(action_vars, params)}

            # Apply the action with variable mapping
            predicates_state, functions_state = apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping)

            # Print the action being applied with its parameters
            action_str = f"({action_name} {' '.join(params)})"
            print(action_str)

            # Print the current state after applying the action
            print_current_state(step, predicates_state, functions_state)
        else:
            # 如果动作未在域中定义，忽略并继续
            pass

    # After all actions have been applied, print the final state if there are actions
    if plan_actions:
        print("Final State after all actions:")
        print_current_state(len(plan_actions), predicates_state, functions_state)
    else:
        print("\nNo actions to execute.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDDL Plan Executor")
    parser.add_argument("domain_file", type=str, help="Path to PDDL domain file (domain.pddl)")
    parser.add_argument("problem_file", type=str, help="Path to PDDL problem file (problem.pddl)")
    parser.add_argument("plan_file", type=str, help="Path to plan file (plan.pddl)")

    args = parser.parse_args()

    main(args.domain_file, args.problem_file, args.plan_file)

'''
import re
import argparse
import sys
import os
import logging
from contextlib import redirect_stderr
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect
from tarski.syntax.formulas import Atom

# 全局禁用所有日志记录
logging.disable(logging.CRITICAL)

# Helper function to get term name with substitution
def get_term_name(term, var_mapping):
    if hasattr(term, 'symbol'):  # 'symbol' 用于标识参数符号
        term_name = term.symbol
        # 如果参数名称以 '?' 开头，则移除 '?'
        if term_name.startswith('?'):
            term_name = term_name[1:]
        substituted = var_mapping.get(term_name, term_name)
        return substituted
    else:
        return str(term)

# Function to load and parse PDDL domain and problem files
def load_pddl_files(domain_file, problem_file):
    reader = FstripsReader()
    try:
        with open(os.devnull, 'w') as devnull:
            with redirect_stderr(devnull):
                reader.parse_domain(domain_file)
    except Exception:
        # 如果解析域文件失败，静默退出
        sys.exit(1)
    try:
        with open(os.devnull, 'w') as devnull:
            with redirect_stderr(devnull):
                reader.read_problem(problem_file, instance=problem_file)
    except Exception:
        # 如果读取问题文件失败，静默退出
        sys.exit(1)
    return reader

# Initialize the state tracker from initial facts in the problem
def initialize_state_tracker(problem):
    predicates_state = set()
    functions_state = {}
    for fact in problem.init.as_atoms():
        if isinstance(fact, tuple):
            # Handle predicate tuples
            if len(fact) == 2 and isinstance(fact[0], str) and isinstance(fact[1], tuple):
                predicate, arguments = fact
                predicates_state.add((predicate, arguments))
            # Handle function assignments like ('=', ('total-cost',), 0.0)
            elif len(fact) == 3 and fact[0] == '=' and isinstance(fact[1], tuple):
                function = fact[1][0]  # Extract function name
                try:
                    value = float(fact[2])
                except (ValueError, TypeError):
                    value = fact[2]
                functions_state[function] = value
            else:
                pass  # Ignore other formats
        elif isinstance(fact, Atom):
            predicate = fact.predicate.symbol
            arguments = tuple(get_term_name(arg, {}) for arg in fact.subterms)
            predicates_state.add((predicate, arguments))
        else:
            pass  # Ignore other formats
    return predicates_state, functions_state

# Function to print the current state in the desired format
def print_current_state(step, predicates_state, functions_state):
    # Uncomment the next line if you want to display the step number as a comment
    # print(f"; Step {step}")
    
    for fact in sorted(predicates_state, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        # Format: (predicate arg1 arg2 ...)
        print(f"({predicate} {' '.join(args)})")
    
    for func, val in functions_state.items():
        # Format: (function-name value)
        print(f"({func} {val})")
    
    print()  # Add a newline for separation between steps or final state

# Function to load the plan file and extract actions
def load_plan_file(plan_file):
    actions = []
    try:
        with open(plan_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith(';') or not line:
                    continue
                match = re.match(r"\((\w+)\s+([^\)]+)\)", line)
                if match:
                    action_name = match.group(1)
                    params = match.group(2).strip().split()
                    actions.append((action_name, params))
                else:
                    pass  # Ignore unrecognized action formats silently
    except Exception:
        # 如果计划文件读取失败，静默退出
        sys.exit(1)
    return actions

# Function to apply an action to the current state
def apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping):
    for effect in action_obj.effects:
        # Add positive effects (AddEffect) to the state
        if isinstance(effect, AddEffect):
            predicate = effect.atom.predicate.symbol
            # Retrieve each subterm's name, handling variables
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            predicates_state.add((predicate, arguments))

        # Remove negative effects (DelEffect) from the state
        elif isinstance(effect, DelEffect):
            predicate = effect.atom.predicate.symbol
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            predicates_state.discard((predicate, arguments))

        # Handle function effects like (increase (total-cost) 5) or (assign (total-cost) 10)
        elif isinstance(effect, tuple) and len(effect) >= 3 and effect[0] in ('increase', 'decrease', 'assign'):
            operation = effect[0]
            function = effect[1][0]  # Assuming the function is the first element in the second tuple
            try:
                value = float(effect[2]) if isinstance(effect[2], (int, float, str)) else effect[2]
            except ValueError:
                value = effect[2]
            if function not in functions_state:
                functions_state[function] = 0.0  # Initialize if not present
            if operation == 'increase':
                functions_state[function] += value
            elif operation == 'decrease':
                functions_state[function] -= value
            elif operation == 'assign':
                functions_state[function] = value
        else:
            # Check if the effect is an equality Atom
            if isinstance(effect, Atom) and effect.predicate.symbol == '=':
                # Handle equality assignment
                if len(effect.subterms) == 2:
                    function_term, value_term = effect.subterms
                    function = get_term_name(function_term, var_mapping)
                    try:
                        value = float(value_term)
                    except ValueError:
                        value = get_term_name(value_term, var_mapping)
                    functions_state[function] = value
            else:
                pass  # Ignore other formats
    return predicates_state, functions_state

# Main function to execute the plan and print final state
def main(domain_file, problem_file, plan_file):
    reader = load_pddl_files(domain_file, problem_file)
    problem = reader.problem

    # Initialize state tracker
    predicates_state, functions_state = initialize_state_tracker(problem)

    # Load plan actions
    plan_actions = load_plan_file(plan_file)

    # Execute plan actions without printing intermediate steps
    for step, (action_name, params) in enumerate(plan_actions, start=1):
        # Access actions as a dictionary
        domain_actions = problem.actions
        if action_name in domain_actions:
            action_obj = domain_actions[action_name]

            # Obtain action variables using 'symbol'
            action_vars = [var.symbol for var in action_obj.parameters]

            # Build variable mapping between action parameters and plan arguments
            if len(action_vars) != len(params):
                var_mapping = {}
            else:
                var_mapping = {var.lstrip('?'): param for var, param in zip(action_vars, params)}

            # Apply the action with variable mapping
            predicates_state, functions_state = apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping)
        else:
            # 如果动作未在域中定义，忽略并继续
            pass

    # After all actions have been applied, print the final state if there are actions
    if plan_actions:
        print_current_state(len(plan_actions), predicates_state, functions_state)
    else:
        print("\nNo actions to execute.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDDL Plan Executor")
    parser.add_argument("domain_file", type=str, help="Path to PDDL domain file (domain.pddl)")
    parser.add_argument("problem_file", type=str, help="Path to PDDL problem file (problem.pddl)")
    parser.add_argument("plan_file", type=str, help="Path to plan file (plan.pddl)")

    args = parser.parse_args()

    main(args.domain_file, args.problem_file, args.plan_file)
