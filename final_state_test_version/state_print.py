'''
import re
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect  # Import specific effect classes

# Function to load and parse PDDL domain and problem files
def load_pddl_files(domain_file, problem_file):
    reader = FstripsReader()
    reader.parse_domain(domain_file)
    reader.read_problem(problem_file, instance=problem_file)
    return reader

# Initialize the state tracker from initial facts in the problem
def initialize_state_tracker(problem):
    initial_state = set()
    for fact in problem.init.as_atoms():
        initial_state.add((fact.predicate.symbol, tuple(arg.name for arg in fact.subterms)))
    return initial_state

# Function to print the current state
def print_current_state(step, state_tracker):
    print(f"Step {step}:")
    for fact in sorted(state_tracker, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        print(f"  {predicate}({', '.join(args)})")
    print()

# Function to load the plan file and extract actions
def load_plan_file(plan_file):
    actions = []
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
    return actions

# Function to apply an action to the current state
def apply_action_to_state(state_tracker, action_name, problem):
    print("DEBUG: Checking actions in problem...")
    print(problem.actions)  # Debug output to see what `problem.actions` contains

    # Access actions as a dictionary
    domain_actions = problem.actions
    if action_name in domain_actions:
        action_obj = domain_actions[action_name]
        for effect in action_obj.effects:
            print(f"DEBUG: Effect object structure: {effect}")  # Print effect structure for inspection
            
            # Add positive effects (AddEffect) to the state
            if isinstance(effect, AddEffect):
                predicate = effect.atom.predicate.symbol
                # Retrieve each subterm's name, handling cases where it's a Variable or constant
                arguments = tuple(arg.symbol if hasattr(arg, 'symbol') else arg.name for arg in effect.atom.subterms)
                state_tracker.add((predicate, arguments))
            
            # Remove negative effects (DelEffect) from the state
            elif isinstance(effect, DelEffect):
                predicate = effect.atom.predicate.symbol
                arguments = tuple(arg.symbol if hasattr(arg, 'symbol') else arg.name for arg in effect.atom.subterms)
                state_tracker.discard((predicate, arguments))
    else:
        print(f"Action '{action_name}' not found in problem actions.")
    return state_tracker

# Main function to execute the plan and print states
def main(domain_file, problem_file, plan_file):
    reader = load_pddl_files(domain_file, problem_file)
    problem = reader.problem

    # Initialize state tracker
    state_tracker = initialize_state_tracker(problem)
    print("Initial State:")
    print_current_state(0, state_tracker)
    
    # Load plan actions
    plan_actions = load_plan_file(plan_file)

    # Execute plan actions
    for step, (action_name, params) in enumerate(plan_actions, start=1):
        state_tracker = apply_action_to_state(state_tracker, action_name, problem)
        print(f"\nApplying action: {action_name} with parameters {params}")
        print_current_state(step, state_tracker)

# Define file paths (Ensure these paths are correct and files exist)
domain_file = "/Users/haisuzhouslocalfolder/Downloads/domain_7.pddl"
problem_file = "/Users/haisuzhouslocalfolder/Downloads/instance_20_1.pddl"
plan_file = "/Users/haisuzhouslocalfolder/Solution2.pddl"

if __name__ == "__main__":
    main(domain_file, problem_file, plan_file)
'''


'''
import re
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect  # Import specific effect classes

# Helper function to get term name with substitution
def get_term_name(term, var_mapping):
    if hasattr(term, 'symbol'):  # 'symbol' is used as identifier for parameters
        term_name = term.symbol
        # Remove '?' from parameter names if it exists
        if term_name.startswith('?'):
            term_name = term_name[1:]
        substituted = var_mapping.get(term_name, term_name)
        print(f"DEBUG: Substituting variable {term.symbol} with {substituted}")
        return substituted
    else:
        return str(term)

# Function to load and parse PDDL domain and problem files
def load_pddl_files(domain_file, problem_file):
    reader = FstripsReader()
    reader.parse_domain(domain_file)
    reader.read_problem(problem_file, instance=problem_file)
    return reader

# Initialize the state tracker from initial facts in the problem
def initialize_state_tracker(problem):
    initial_state = set()
    for fact in problem.init.as_atoms():
        predicate = fact.predicate.symbol
        arguments = tuple(get_term_name(arg, {}) for arg in fact.subterms)
        initial_state.add((predicate, arguments))
    return initial_state

# Function to print the current state
def print_current_state(step, state_tracker):
    print(f"Step {step}:")
    for fact in sorted(state_tracker, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        print(f"  {predicate}({', '.join(args)})")
    print()

# Function to load the plan file and extract actions
def load_plan_file(plan_file):
    actions = []
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
    return actions

# Function to apply an action to the current state
def apply_action_to_state(state_tracker, action_obj, var_mapping):
    print(f"DEBUG: Applying action: {action_obj.name} with mapping: {var_mapping}")
    for effect in action_obj.effects:
        print(f"DEBUG: Effect object structure: {effect}")  # Print effect structure for inspection

        # Add positive effects (AddEffect) to the state
        if isinstance(effect, AddEffect):
            predicate = effect.atom.predicate.symbol
            # Retrieve each subterm's name, handling variables
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            print(f"DEBUG: Adding to state: {predicate}({arguments})")
            state_tracker.add((predicate, arguments))
        
        # Remove negative effects (DelEffect) from the state
        elif isinstance(effect, DelEffect):
            predicate = effect.atom.predicate.symbol
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            print(f"DEBUG: Removing from state: {predicate}({arguments})")
            state_tracker.discard((predicate, arguments))
    return state_tracker

# Main function to execute the plan and print states
def main(domain_file, problem_file, plan_file):
    reader = load_pddl_files(domain_file, problem_file)
    problem = reader.problem

    # Initialize state tracker
    state_tracker = initialize_state_tracker(problem)
    print("Initial State:")
    print_current_state(0, state_tracker)
    
    # Load plan actions
    plan_actions = load_plan_file(plan_file)

    # Execute plan actions
    for step, (action_name, params) in enumerate(plan_actions, start=1):
        print(f"\nApplying action: {action_name} with parameters {params}")
        # Access actions as a dictionary
        domain_actions = problem.actions
        if action_name in domain_actions:
            action_obj = domain_actions[action_name]

            # Obtain action variables using 'symbol'
            action_vars = [var.symbol for var in action_obj.parameters]
            print("DEBUG: Action variables:", action_vars)
            
            # Build variable mapping between action parameters and plan arguments
            if len(action_vars) != len(params):
                print(f"Warning: Action '{action_name}' expects {len(action_vars)} parameters but got {len(params)}")
                var_mapping = {}
            else:
                var_mapping = {var.lstrip('?'): param for var, param in zip(action_vars, params)}
            print("DEBUG: Variable mapping:", var_mapping)

            # Apply the action with variable mapping
            state_tracker = apply_action_to_state(state_tracker, action_obj, var_mapping)
        else:
            print(f"Action '{action_name}' not found in problem actions.")
        # Print the state
        print_current_state(step, state_tracker)

# Define file paths (Ensure these paths are correct and files exist)
domain_file = "/Users/haisuzhouslocalfolder/Downloads/domain.pddl"
problem_file = "/Users/haisuzhouslocalfolder/Downloads/p01.pddl"
plan_file = "/Users/haisuzhouslocalfolder/pddl_verify/pddl_p01_check.pddl"


if __name__ == "__main__":
    main(domain_file, problem_file, plan_file)
'''


"""
import re
import os
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect  # Import specific effect classes
'''
# Preprocess function to flatten the type hierarchy in the domain file
def preprocess_pddl_types(domain_file, output_file):
    with open(domain_file, 'r') as file:
        lines = file.readlines()

    # Step 1: Parse types and build type hierarchy
    type_hierarchy = {}
    inside_type_section = False

    for line in lines:
        if "(:types" in line:
            inside_type_section = True
            # Extract types and hierarchy
            type_matches = re.findall(r"(\w+)\s*-\s*(\w+)", line)
            for child, parent in type_matches:
                type_hierarchy[child] = parent
        elif inside_type_section and ")" in line:
            inside_type_section = False
        elif inside_type_section:
            # Handle multiline type definitions
            type_matches = re.findall(r"(\w+)\s*-\s*(\w+)", line)
            for child, parent in type_matches:
                type_hierarchy[child] = parent

    # Step 2: Flatten the type hierarchy to get each type's base type
    def get_base_type(t):
        while t in type_hierarchy:
            t = type_hierarchy[t]
        return t

    flat_type_map = {t: get_base_type(t) for t in type_hierarchy}

    # Step 3: Generate simplified type definition line
    simplified_types = {}
    for t, base in flat_type_map.items():
        if base not in simplified_types:
            simplified_types[base] = []
        simplified_types[base].append(t)
    
    # Construct the new type line
    new_type_line = "(:types "
    for base, types in simplified_types.items():
        new_type_line += " ".join(types) + f" - {base} "
    new_type_line += ")\n"

    # Step 4: Write modified content with the simplified type line
    modified_lines = []
    inside_type_section = False
    for line in lines:
        if "(:types" in line:
            modified_lines.append(new_type_line)
            inside_type_section = True
        elif inside_type_section and ")" in line:
            inside_type_section = False
        elif not inside_type_section:
            modified_lines.append(line)

    with open(output_file, 'w') as file:
        file.writelines(modified_lines)

    print(f"Domain file preprocessed and saved to {output_file}")
'''
    
import re
import os
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect  # Import specific effect classes
from tarski.syntax.formulas import Atom, Eq  # Adjusted import based on Tarski's latest version

# Helper function to get term name with substitution
def get_term_name(term, var_mapping):
    if hasattr(term, 'name'):
        term_name = term.name
        # Substitute if present
        substituted = var_mapping.get(term_name, term_name)
        print(f"DEBUG: Substituting variable {term_name} with {substituted}")
        return substituted
    else:
        return str(term)

# Function to load and parse PDDL domain and problem files without preprocessing
def load_pddl_files(domain_file, problem_file):
    reader = FstripsReader()
    reader.parse_domain(domain_file)
    reader.read_problem(problem_file, instance=problem_file)
    return reader

# Initialize the state tracker from initial facts in the problem
def initialize_state_tracker(problem):
    predicates_state = set()
    functions_state = {}
    for fact in problem.init.as_atoms():
        print(f"DEBUG: fact = {fact}, type = {type(fact)}")
        if isinstance(fact, Atom):
            predicate = fact.predicate.name
            arguments = tuple(arg.name for arg in fact.arguments)
            predicates_state.add((predicate, arguments))
        elif isinstance(fact, Eq):
            # Handle function assignments like (= (total-cost) 0)
            function = fact.left.functor.name
            try:
                value = float(fact.right)
            except ValueError:
                value = fact.right
            functions_state[function] = value
        else:
            print(f"Unexpected fact format: {fact}")
    return predicates_state, functions_state

# Function to print the current state
def print_current_state(step, predicates_state, functions_state):
    print(f"Step {step}:")
    for fact in sorted(predicates_state, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        print(f"  {predicate}({', '.join(args)})")
    for func, val in functions_state.items():
        print(f"  {func} = {val}")
    print()

# Function to load the plan file and extract actions
def load_plan_file(plan_file):
    actions = []
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
    return actions

# Function to apply an action to the current state
def apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping):
    print(f"DEBUG: Applying action: {action_obj.name} with mapping: {var_mapping}")
    for effect in action_obj.effects:
        print(f"DEBUG: Effect object structure: {effect}")

        if isinstance(effect, AddEffect):
            predicate = effect.atom.predicate.name
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.arguments)
            print(f"DEBUG: Adding to state: {predicate}({', '.join(arguments)})")
            predicates_state.add((predicate, arguments))

        elif isinstance(effect, DelEffect):
            predicate = effect.atom.predicate.name
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.arguments)
            print(f"DEBUG: Removing from state: {predicate}({', '.join(arguments)})")
            predicates_state.discard((predicate, arguments))

        elif hasattr(effect, 'op') and hasattr(effect, 'function') and hasattr(effect, 'value'):
            # Handle function effects like (increase (total-cost) 5)
            function = effect.function.name
            value_change = effect.value
            if effect.op == 'increase':
                functions_state[function] += value_change
                print(f"DEBUG: Increased {function} by {value_change}, new value: {functions_state[function]}")
            elif effect.op == 'decrease':
                functions_state[function] -= value_change
                print(f"DEBUG: Decreased {function} by {value_change}, new value: {functions_state[function]}")
            elif effect.op == 'assign':
                functions_state[function] = value_change
                print(f"DEBUG: Assigned {function} to {value_change}")
            else:
                print(f"DEBUG: Unsupported operation {effect.op} on function {function}")

        else:
            print(f"DEBUG: Unsupported effect type: {effect}")
    return predicates_state, functions_state

# Main function to execute the plan and print states
def main(domain_file, problem_file, plan_file):
    reader = load_pddl_files(domain_file, problem_file)
    problem = reader.problem

    # Initialize state tracker
    predicates_state, functions_state = initialize_state_tracker(problem)
    print("Initial State:")
    print_current_state(0, predicates_state, functions_state)
    
    # Load plan actions
    plan_actions = load_plan_file(plan_file)

    # Execute plan actions
    for step, (action_name, params) in enumerate(plan_actions, start=1):
        print(f"\nApplying action: {action_name} with parameters {params}")
        domain_actions = problem.actions
        if action_name in domain_actions:
            action_obj = domain_actions[action_name]
            if hasattr(action_obj, 'parameters'):
                action_vars = [var.name for var in action_obj.parameters]
                print("DEBUG: Action variables:", action_vars)
                if len(action_vars) != len(params):
                    print(f"Warning: Action '{action_name}' expects {len(action_vars)} parameters but got {len(params)}")
                    var_mapping = {}
                else:
                    var_mapping = {var.name.lstrip('?'): param for var, param in zip(action_obj.parameters, params)}
                print("DEBUG: Variable mapping:", var_mapping)
                predicates_state, functions_state = apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping)
            else:
                print(f"Error: Action '{action_name}' does not have 'parameters' attribute.")
        else:
            print(f"Action '{action_name}' not found in problem actions.")
        print_current_state(step, predicates_state, functions_state)

# Define file paths (Ensure these paths are correct and files exist)
domain_file = "/Users/haisuzhouslocalfolder/Downloads/domain.pddl"
problem_file = "/Users/haisuzhouslocalfolder/Downloads/p01.pddl"
plan_file = "/Users/haisuzhouslocalfolder/pddl_verify/pddl_p01_check.pddl"

if __name__ == "__main__":
    main(domain_file, problem_file, plan_file)

"""



import re
import argparse  # 引入 argparse 模块
from tarski.io import FstripsReader
from tarski.fstrips import AddEffect, DelEffect  # 导入特定的效果类
from tarski.syntax.formulas import Atom  # 移除了 Eq，因为它不存在

# Helper function to get term name with substitution
def get_term_name(term, var_mapping):
    if hasattr(term, 'symbol'):  # 'symbol' 是用于标识参数的标识符
        term_name = term.symbol
        # 如果参数名称以 '?' 开头，则移除 '?'
        if term_name.startswith('?'):
            term_name = term_name[1:]
        substituted = var_mapping.get(term_name, term_name)
        print(f"DEBUG: Substituting variable {term.symbol} with {substituted}")
        return substituted
    else:
        return str(term)

# Function to load and parse PDDL domain and problem files
def load_pddl_files(domain_file, problem_file):
    reader = FstripsReader()
    reader.parse_domain(domain_file)
    reader.read_problem(problem_file, instance=problem_file)
    return reader

# Initialize the state tracker from initial facts in the problem
def initialize_state_tracker(problem):
    predicates_state = set()
    functions_state = {}
    for fact in problem.init.as_atoms():
        print(f"DEBUG: fact = {fact}, type = {type(fact)}")
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
                print(f"DEBUG: Function assignment: {function} = {value}")
            else:
                print(f"DEBUG: Unexpected tuple format: {fact}")
        elif isinstance(fact, Atom):
            predicate = fact.predicate.symbol
            arguments = tuple(get_term_name(arg, {}) for arg in fact.subterms)
            predicates_state.add((predicate, arguments))
        else:
            print(f"DEBUG: Unexpected fact format: {fact}")
    return predicates_state, functions_state

# Function to print the current state
def print_current_state(step, predicates_state, functions_state):
    print(f"Step {step}:")
    for fact in sorted(predicates_state, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        print(f"  {predicate}({', '.join(args)})")
    for func, val in functions_state.items():
        print(f"  {func} = {val}")
    print()

# Function to load the plan file and extract actions
def load_plan_file(plan_file):
    actions = []
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
    return actions

# Function to apply an action to the current state
def apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping):
    print(f"DEBUG: Applying action: {action_obj.name} with mapping: {var_mapping}")
    for effect in action_obj.effects:
        print(f"DEBUG: Effect object structure: {effect}")  # Print effect structure for inspection

        # Add positive effects (AddEffect) to the state
        if isinstance(effect, AddEffect):
            predicate = effect.atom.predicate.symbol
            # Retrieve each subterm's name, handling variables
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            print(f"DEBUG: Adding to state: {predicate}({', '.join(arguments)})")
            predicates_state.add((predicate, arguments))

        # Remove negative effects (DelEffect) from the state
        elif isinstance(effect, DelEffect):
            predicate = effect.atom.predicate.symbol
            arguments = tuple(get_term_name(arg, var_mapping) for arg in effect.atom.subterms)
            print(f"DEBUG: Removing from state: {predicate}({', '.join(arguments)})")
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
                print(f"DEBUG: Increased {function} by {value}, new value: {functions_state[function]}")
            elif operation == 'decrease':
                functions_state[function] -= value
                print(f"DEBUG: Decreased {function} by {value}, new value: {functions_state[function]}")
            elif operation == 'assign':
                functions_state[function] = value
                print(f"DEBUG: Assigned {function} to {value}")
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
                    print(f"DEBUG: Function assignment via equality: {function} = {value}")
            else:
                print(f"DEBUG: Unsupported effect type: {effect}")
    return predicates_state, functions_state

# Main function to execute the plan and print states
def main(domain_file, problem_file, plan_file):
    reader = load_pddl_files(domain_file, problem_file)
    problem = reader.problem

    # Initialize state tracker
    predicates_state, functions_state = initialize_state_tracker(problem)

    # Load plan actions
    plan_actions = load_plan_file(plan_file)

    # Execute plan actions
    for step, (action_name, params) in enumerate(plan_actions, start=1):
        print(f"\nApplying action: {action_name} with parameters {params}")
        # Access actions as a dictionary
        domain_actions = problem.actions
        if action_name in domain_actions:
            action_obj = domain_actions[action_name]

            # Obtain action variables using 'symbol'
            action_vars = [var.symbol for var in action_obj.parameters]
            print("DEBUG: Action variables:", action_vars)

            # Build variable mapping between action parameters and plan arguments
            if len(action_vars) != len(params):
                print(f"Warning: Action '{action_name}' expects {len(action_vars)} parameters but got {len(params)}")
                var_mapping = {}
            else:
                var_mapping = {var.lstrip('?'): param for var, param in zip(action_vars, params)}
            print("DEBUG: Variable mapping:", var_mapping)

            # Apply the action with variable mapping
            predicates_state, functions_state = apply_action_to_state(predicates_state, functions_state, action_obj, var_mapping)
        else:
            print(f"Action '{action_name}' not found in problem actions.")

    # After all actions have been applied, print the final state
    final_step = len(plan_actions)
    print("\nFinal State after all actions:")
    print_current_state(final_step, predicates_state, functions_state)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDDL Plan Executor")
    parser.add_argument("domain_file", type=str, help="路径到 PDDL 域文件 (domain.pddl)")
    parser.add_argument("problem_file", type=str, help="路径到 PDDL 问题文件 (problem.pddl)")
    parser.add_argument("plan_file", type=str, help="路径到计划文件 (plan.pddl)")

    args = parser.parse_args()

    main(args.domain_file, args.problem_file, args.plan_file)
