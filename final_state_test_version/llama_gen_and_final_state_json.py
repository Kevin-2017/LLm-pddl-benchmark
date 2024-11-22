import llm_plan_bench as lpb
import json
from typing import List, Dict, Union, Optional, Any
import argparse
import os
from pathlib import Path
import openai
import subprocess
import re

from tarski.io import FstripsReader

# ========================
# Helper Functions
# ========================

def extract_json_from_response(response: str) -> str:
    """
    Clean and extract JSON content from the response.
    
    Args:
        response (str): Raw response from LLM
        
    Returns:
        str: Cleaned JSON string
    """
    # First try to detect if response is already in JSON format
    try:
        json.loads(response)
        return response
    except json.JSONDecodeError:
        # If not, try to extract between $$ markers
        try:
            start_idx = response.find("$$\n")
            end_idx = response.rfind("\n$$")
            
            if start_idx != -1 and end_idx != -1:
                return response[start_idx + 3:end_idx].strip()
            return response
        except Exception:
            return response

def extract_plan_from_response(response: str) -> str:
    """
    Extract the plan from the LLM response.
    
    Args:
        response (str): Raw response from LLM
        
    Returns:
        str: Extracted plan or error message
    """
    try:
        # First extract content between $$ markers if present
        json_str = extract_json_from_response(response)
        
        # Parse the JSON response
        response_json = json.loads(json_str)
        return response_json.get("plan", "No plan found in response")
    except json.JSONDecodeError:
        return "Error: Could not parse response as JSON"

def extract_init_content(content: str) -> Optional[str]:
    """
    从 PDDL 内容中提取 (:init ...) 块，确保正确匹配括号。
    """
    start = content.find('(:init')
    if start == -1:
        return None
    stack = []
    for i in range(start, len(content)):
        if content[i] == '(':
            stack.append('(')
        elif content[i] == ')':
            if stack:
                stack.pop()
                if not stack:
                    init_block = content[start:i+1]
                    print("Extracted :init block:")
                    print(init_block)
                    return init_block
    return None

def get_initial_state(problem_path: str) -> Dict[str, Any]:
    """
    从 PDDL 问题文件中提取初始状态。
    
    Args:
        problem_path (str): PDDL 问题文件路径
        
    Returns:
        Dict[str, Any]: 包含 predicates 和 functions 的字典
    """
    try:
        with open(problem_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        init_block = extract_init_content(content)
        if not init_block:
            print("No :init section found or unmatched parentheses.")
            return {"predicates": [], "functions": []}
        
        # 移除 '(:init' 和最外层的括号
        init_content = init_block[len('(:init'): -1].strip()
        
        # 初始化谓词和函数列表
        predicates = []
        functions = []
        
        # 分析每一行，区分谓词和函数
        for line in init_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('(') and not line.startswith('(='):
                # 谓词
                predicates.append(line)
            elif line.startswith('(='):
                # 函数
                match = re.match(r'\=\s*\(([^)]+)\)\s*([^\s\)]+)', line)
                if match:
                    func_name, func_value = match.groups()
                    functions.append(f"{func_name} = {func_value}")
        
        initial_state = {
            "predicates": predicates,
            "functions": functions
        }
        return initial_state
    except FileNotFoundError:
        print(f"Problem file not found: {problem_path}")
        return {"predicates": [], "functions": []}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"predicates": [], "functions": []}

def read_pddl_domain(domain_path: str, spaces_per_tab: int =4) -> str:
    """
    读取 PDDL 域文件并替换制表符为空格。
    
    Args:
        domain_path (str): PDDL 域文件路径
        spaces_per_tab (int): 每个制表符替换为的空格数
        
    Returns:
        str: 处理后的 PDDL 域内容
    """
    with open(domain_path, 'r', encoding='utf-8') as file:
        domain_content = file.read()
    # Replace each tab with the specified number of spaces
    domain_content = domain_content.replace('\t', ' ' * spaces_per_tab)
    return domain_content

def load_pddl_files(domain_file: str, problem_file: str) -> FstripsReader:
    """
    加载并解析 PDDL 域和问题文件。
    
    Args:
        domain_file (str): PDDL 域文件路径
        problem_file (str): PDDL 问题文件路径
        
    Returns:
        FstripsReader: 解析后的读取器对象
    """
    reader = FstripsReader()
    reader.parse_domain(domain_file)
    reader.read_problem(problem_file, instance=problem_file)
    return reader

def initialize_state_tracker(problem) -> (set, Dict[str, Any]):
    """
    从问题的初始事实中初始化状态追踪器。
    
    Args:
        problem: 解析后的 PDDL 问题对象
        
    Returns:
        Tuple[set, Dict[str, Any]]: predicates_state 和 functions_state
    """
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
                pass  # 忽略其他格式
        elif isinstance(fact, Atom):
            predicate = fact.predicate.symbol
            arguments = tuple(get_term_name(arg, {}) for arg in fact.subterms)
            predicates_state.add((predicate, arguments))
        else:
            pass  # 忽略其他格式
    return predicates_state, functions_state

def get_term_name(term, var_mapping: Dict[str, str]) -> str:
    """
    获取术语名称，并应用变量映射。
    
    Args:
        term: PDDL 术语对象
        var_mapping (Dict[str, str]): 变量映射
        
    Returns:
        str: 术语名称
    """
    if hasattr(term, 'symbol'):  # 'symbol' 是用于标识参数的标识符
        term_name = term.symbol
        # 如果参数名称以 '?' 开头，则移除 '?'
        if term_name.startswith('?'):
            term_name = term_name[1:]
        substituted = var_mapping.get(term_name, term_name)
        return substituted
    else:
        return str(term)

def print_current_state(step: int, predicates_state: set, functions_state: Dict[str, Any]) -> None:
    """
    打印当前状态。
    
    Args:
        step (int): 当前步骤
        predicates_state (set): 当前谓词状态
        functions_state (Dict[str, Any]): 当前函数状态
    """
    output = f"Step {step}:\n"
    for fact in sorted(predicates_state, key=lambda x: str(x)):
        predicate, args = fact[0], fact[1]
        output += f"  {predicate}({', '.join(args)})\n"
    for func, val in functions_state.items():
        output += f"  {func} = {val}\n"
    output += "\n"
    print(output, end='')  # 使用 end='' 避免额外换行

def load_plan_file(plan_file: str) -> List[tuple]:
    """
    加载计划文件并提取动作。
    
    Args:
        plan_file (str): 计划文件路径
        
    Returns:
        List[tuple]: 动作名称和参数的列表
    """
    actions = []
    with open(plan_file, 'r', encoding='utf-8') as file:
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

def apply_action_to_state(predicates_state: set, functions_state: Dict[str, Any], action_obj, var_mapping: Dict[str, str]) -> (set, Dict[str, Any]):
    """
    将动作应用到当前状态。
    
    Args:
        predicates_state (set): 当前谓词状态
        functions_state (Dict[str, Any]): 当前函数状态
        action_obj: 动作对象
        var_mapping (Dict[str, str]): 变量映射
        
    Returns:
        Tuple[set, Dict[str, Any]]: 更新后的 predicates_state 和 functions_state
    """
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
                pass  # 忽略其他格式
    return predicates_state, functions_state

# ========================
# Core Functions
# ========================

def process_domain(domain_data: Dict[str, Any], output_base: Path, model: lpb.BlackboxLLM) -> None:
    """
    处理域中的所有实例并保存解决方案。
    
    Args:
        domain_data (Dict[str, Any]): 域数据
        output_base (Path): 输出的基路径
        model (lpb.BlackboxLLM): 初始化的 LLM 模型
    """
    domain_name = domain_data["domain"]
    
    # 创建计划和完整答案的目录
    domain_output = output_base / "pddl" / domain_name
    domain_output.mkdir(parents=True, exist_ok=True)
    
    full_answers_dir = output_base / "full_answers" / domain_name
    full_answers_dir.mkdir(parents=True, exist_ok=True)
    
    llama_output_dir = output_base / "llama_outputs" / domain_name
    llama_output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing domain: {domain_name}")
    
    for prompt_data in domain_data["prompts"]:
        instance_name = prompt_data["instance"]
        output_file = domain_output / f"{Path(instance_name).stem}.sol"
        full_answer_file = full_answers_dir / f"{Path(instance_name).stem}.json"
        llama_output_file = llama_output_dir / f"{Path(instance_name).stem}_llama.json"
        
        print(f"  Processing instance: {instance_name}")
        
        try:
            # 读取 PDDL 文件路径
            pddl_domain_path = prompt_data.get("domain_path", 'domain-barman-sequencial-optimal.pddl')
            pddl_problem_path = prompt_data.get("problem_path", 'instance-1-barman-sequential-optimal.pddl')
            
            # 读取并处理 PDDL 域文件
            pddl_domain = read_pddl_domain(pddl_domain_path, spaces_per_tab=4)
            pddl_domain_lines = pddl_domain.strip().split('\n')
            
            # 获取初始状态
            initial_state = get_initial_state(pddl_problem_path)
            
            # 构建 Prompt
            prompt = prompt_data["prompt"]
            combined_prompt = f"{prompt}\n\nDomain:\n{pddl_domain}\n\nProblem:\n{open(pddl_problem_path, 'r', encoding='utf-8').read()}"
            
            # 发送 Prompt 到 LLM
            llama_response = model(combined_prompt)
            
            # 提取 JSON 内容
            json_str = extract_json_from_response(llama_response)
            
            # 保存完整的 JSON 响应
            with open(full_answer_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            # 提取计划并保存
            plan = extract_plan_from_response(llama_response)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(plan)
            
            # 保存 LLM 的完整输出到单独的 JSON 文件
            llama_output = {
                "prompt": combined_prompt,
                "response": llama_response
            }
            with open(llama_output_file, 'w', encoding='utf-8') as f:
                json.dump(llama_output, f, indent=4, ensure_ascii=False)
            
            print(f"    Saved solution to: {output_file}")
            print(f"    Saved full answer to: {full_answer_file}")
            print(f"    Saved llama output to: {llama_output_file}")
            
        except Exception as e:
            print(f"    Error processing {instance_name}: {str(e)}")
            # 写入错误信息到所有文件
            error_msg = f"Error: {str(e)}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(error_msg)
            with open(full_answer_file, 'w', encoding='utf-8') as f:
                f.write(error_msg)
            with open(llama_output_file, 'w', encoding='utf-8') as f:
                f.write(error_msg)

def read_json_input(input_path: str) -> Dict[str, Any]:
    """
    读取并解析输入的 JSON 文件，支持 all_domains.json 和单个域的 JSON 格式。
    
    Args:
        input_path (str): JSON 文件路径
        
    Returns:
        Dict[str, Any]: 包含域数据的字典
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # 检查是否为单个域的 JSON
    if "domain" in data:
        # 单个域的 JSON
        return {"single_domain": data}
    else:
        # all_domains.json 格式
        return data

def generate_json(domain_path: str, problem_path: str, solution_path: str) -> Dict[str, Any]:
    """
    生成 JSON 结构，包括 prompt, pddl_domain, initial_state, action_sequence, states_after_actions。
    
    Args:
        domain_path (str): PDDL 域文件路径
        problem_path (str): PDDL 问题文件路径
        solution_path (str): 解决方案计划文件路径
        
    Returns:
        Dict[str, Any]: 生成的 JSON 数据
    """
    # 读取并处理 PDDL 域文件，替换制表符为4个空格
    pddl_domain = read_pddl_domain(domain_path, spaces_per_tab=4)
    
    # 将 pddl_domain 转换为字符串列表
    pddl_domain_lines = pddl_domain.strip().split('\n')
    
    # 获取初始状态
    initial_state = get_initial_state(problem_path)
    
    # 生成包含前两个动作的计划文件，并获取动作列表
    first_two_actions = generate_plan_with_first_two_actions(solution_path, 'temp_plan_file.plan')
    
    # 获取应用动作后的状态
    states_output = get_states_after_actions(domain_path, problem_path, 'temp_plan_file.plan')
    
    # 将每个状态转换为字符串列表（这里只包含最终状态）
    states_after_actions = []
    for state in states_output:
        state_lines = state.strip().split('\n')
        states_after_actions.append(state_lines)
    
    # 准备最终的 JSON 结构
    data = {
        "prompt": "We are solving problems in PDDL format. Based on the PDDL domain, what will be the states after each action? Generate your answer without explanation and in txt format like this: \nabove(f0, f1)\nabove(f0, f2)\nabove(f0, f3)",
        "pddl_domain": pddl_domain_lines,  # 使用字符串列表，已替换制表符
        "initial_state": initial_state,  # 包含 predicates 和 functions 的字典
        "action_sequence": first_two_actions,  # 作为动作列表存储
        "states_after_actions": states_after_actions  # 作为状态列表存储
    }
    
    return data

def generate_plan_with_first_two_actions(solution_path: str, output_plan_path: str) -> List[str]:
    """
    从解决方案计划文件中获取前两个动作，并生成计划文件。
    
    Args:
        solution_path (str): 解决方案计划文件路径
        output_plan_path (str): 输出的计划文件路径
        
    Returns:
        List[str]: 前两个动作的列表
    """
    with open(solution_path, 'r', encoding='utf-8') as file:
        actions = file.readlines()
    first_two_actions = actions[:2]  # 获取前两个动作
    first_two_actions = [action.strip() for action in first_two_actions if action.strip()]
    
    # 写入计划文件，每个动作作为列表元素
    with open(output_plan_path, 'w', encoding='utf-8') as plan_file:
        for action in first_two_actions:
            plan_file.write(action + "\n")
    
    return first_two_actions  # 返回动作列表

def get_states_after_actions(domain_path: str, problem_path: str, plan_file_path: str) -> List[str]:
    """
    通过运行 state_print.py 并传递域文件、问题文件和计划文件路径来获取动作后的状态。
    
    Args:
        domain_path (str): PDDL 域文件路径
        problem_path (str): PDDL 问题文件路径
        plan_file_path (str): 计划文件路径
        
    Returns:
        List[str]: 状态输出列表（这里只包含最终状态）
    """
    try:
        # 运行 state_print.py 并传递域文件、问题文件和计划文件路径
        output = subprocess.check_output(['python3', 'state_print.py', domain_path, problem_path, plan_file_path], stderr=subprocess.STDOUT).decode('utf-8')
        # 因为现在 state_print.py 只输出最终状态，我们可以直接将其作为一个字符串存储
        return [output.strip()]  # 只返回最终状态
    except subprocess.CalledProcessError as e:
        print(f"Error executing state_print.py: {e.output.decode('utf-8')}")
        return []

# ========================
# Main Function
# ========================

def main():
    parser = argparse.ArgumentParser(description='Generate solutions for PDDL problems')
    parser.add_argument('--input', required=True,
                        help='Path to domains.json')
    parser.add_argument('--output', required=True,
                        help='Base path for output directories')
    parser.add_argument('--model_path', default="/ssd1/kevin/huggingface/Llama-3.1-8B-Instruct", help='Model identifier for LLM')
    args = parser.parse_args()
    output_base = Path(args.output)
    output_base.mkdir(parents=True, exist_ok=True)
    
    # 读取输入 JSON 文件
    all_domains = read_json_input(args.input)
    
    # 初始化 LLM 模型
    model = lpb.BlackboxLLM(args.model_path, device='cuda:1')
    
    # 处理每个域
    for domain_name, domain_data in all_domains.items():
        process_domain(domain_data, output_base, model)
        
    print("\nProcessing complete!")
    print(f"Solutions saved to: {output_base}")

if __name__ == "__main__":
    main()
