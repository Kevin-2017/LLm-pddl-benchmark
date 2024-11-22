import json
import subprocess
import re
import os
from tarski.io import FstripsReader

# Function to read the PDDL domain from a file and replace tabs with spaces
def read_pddl_domain(domain_path, spaces_per_tab=4):
    with open(domain_path, 'r', encoding='utf-8') as file:
        domain_content = file.read()
    # Replace each tab with the specified number of spaces
    domain_content = domain_content.replace('\t', ' ' * spaces_per_tab)
    return domain_content


import re

def extract_init_content(content):
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
                    return content[start:i+1]
    return None

def get_initial_state(problem_path):
    try:
        with open(problem_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        init_block = extract_init_content(content)
        if not init_block:
            print("No :init section found or unmatched parentheses.")
            return {"predicates": [], "functions": []}
        
        # 移除 '(:init' 和最外层的括号
        init_content = init_block[len('(:init'): -1].strip()
        
        # 分析每一行，区分谓词和函数
        predicates = []
        functions = []
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
            "predicates": predicates
        }
        return initial_state
    except FileNotFoundError:
        print(f"Problem file not found: {problem_path}")
        return {"predicates": [], "functions": []}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"predicates": [], "functions": []}


# Function to get first 2 actions from the solution and generate a plan file
def generate_plan_with_first_two_actions(solution_path, output_plan_path):
    with open(solution_path, 'r', encoding='utf-8') as file:
        actions = file.readlines()
    first_two_actions = actions[:2]  # 获取前两个动作
    first_two_actions = [action.strip() for action in first_two_actions if action.strip()]
    
    # 写入计划文件，每个动作作为列表元素
    with open(output_plan_path, 'w', encoding='utf-8') as plan_file:
        for action in first_two_actions:
            plan_file.write(action + "\n")
    
    return first_two_actions  # 返回动作列表

# Function to get states after actions by running state_print.py with the sequence of actions
def get_states_after_actions(domain_path, problem_path, plan_file_path):
    try:
        # 运行 state_print.py 并传递域文件、问题文件和计划文件路径
        output = subprocess.check_output(['python3', 'state_print.py', domain_path, problem_path, plan_file_path], stderr=subprocess.STDOUT).decode('utf-8')
        # 因为现在 state_print.py 只输出最终状态，我们可以直接将其作为一个字符串存储
        return [output.strip()]  # 只返回最终状态
    except subprocess.CalledProcessError as e:
        print(f"Error executing state_print.py: {e.output.decode('utf-8')}")
        return []

def generate_json(domain_path, problem_path, solution_path):
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
    
    # 写入 JSON 文件
    with open('output.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    print("JSON 文件已生成：output.json")

def main():
    # Paths to the PDDL domain, problem, and solution files
    domain_path = 'domain-barman-sequencial-optimal.pddl'
    problem_path = 'instance-1-barman-sequential-optimal.pddl'
    solution_path = 'solution-barman-sequential-optimal.pddl'

    # 确保路径正确且文件存在
    if not os.path.exists(domain_path):
        print(f"Domain file not found: {domain_path}")
        return

    if not os.path.exists(problem_path):
        print(f"Problem file not found: {problem_path}")
        return

    if not os.path.exists(solution_path):
        print(f"Solution file not found: {solution_path}")
        return

    # 调用生成 JSON 的函数
    generate_json(domain_path, problem_path, solution_path)

if __name__ == "__main__":
    main()
