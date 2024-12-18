import json
import os
from pathlib import Path
import subprocess
import re
import llm_plan_bench as lpb

import torch
print(torch.cuda.is_available())  # Should return True if a CUDA-enabled GPU is available
print(torch.cuda.device_count())  # Should return the number of GPUs
print(torch.cuda.current_device())  # Should return the ID of the current GPU


# Function to read the PDDL domain
def read_pddl_domain(domain_path, spaces_per_tab=4):
    with open(domain_path, 'r', encoding='utf-8') as file:
        domain_content = file.read()
    domain_content = domain_content.replace('\t', ' ' * spaces_per_tab)
    return domain_content

# Function to extract the init section from the PDDL problem
def extract_init_content(content):
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
        init_content = init_block[len('(:init'): -1].strip()
        predicates = [line.strip() for line in init_content.split('\n') if line.strip()]
        return {"predicates": predicates}
    except FileNotFoundError:
        print(f"Problem file not found: {problem_path}")
        return {"predicates": []}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"predicates": []}


def generate_plan_with_user_actions(solution_path, output_plan_path, num_actions):
    with open(solution_path, 'r', encoding='utf-8') as file:
        actions = file.readlines()
    selected_actions = [action.strip() for action in actions[:num_actions] if action.strip()]
    with open(output_plan_path, 'w', encoding='utf-8') as plan_file:
        for action in selected_actions:
            plan_file.write(action + "\n")
    return selected_actions

# Function to get states after actions
def get_states_after_actions(domain_path, problem_path, plan_file_path):
    try:
        output = subprocess.check_output(['python3', 'state_print.py', domain_path, problem_path, plan_file_path], stderr=subprocess.STDOUT).decode('utf-8')
        return output.strip().split('\n')  # Split by newline to get a list of states
    except subprocess.CalledProcessError as e:
        print(f"Error executing state_print.py: {e.output.decode('utf-8')}")
        return []

# Function to call LLM and save the output to a JSON file
# def call_llm_with_json_input(input_json_path, model, output_file):
#     try:
#         # 读取最初生成的JSON文件
#         with open(input_json_path, 'r', encoding='utf-8') as json_file:
#             data = json.load(json_file)
        
#         # 从JSON中取出除 states_after_actions 外的部分
#         llama_input = {
#             "prompt": data["prompt"],
#             "pddl_domain": data["pddl_domain"],
#             "initial_state": data["initial_state"],
#             "action_sequence": data["action_sequence"]
#         }

#         print("Sending input to LLM...")
#         response = model(json.dumps(llama_input, ensure_ascii=False, indent=4))  # 调用模型
        
#         # 将模型响应保存到指定文件
#         with open(output_file, 'w', encoding='utf-8') as f:
#             f.write(response)
#         print(f"Model output saved to: {output_file}")
#     except Exception as e:
#         print(f"Error during LLM call: {e}")
# Function to call LLM and save the output to a TXT file
def call_llm_with_json_input(input_json_path, model, output_file):
    try:
        # Read the input JSON file
        with open(input_json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        
        # Extract necessary input for the model
        llama_input = {
            "prompt": data["prompt"],
            "pddl_domain": data["pddl_domain"],
            "initial_state": data["initial_state"],
            "action_sequence": data["action_sequence"]
        }

        print("Sending input to LLM...")
        response = model(json.dumps(llama_input, ensure_ascii=False, indent=4))  # Call the model
        
        # Save the model's output to a TXT file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response)
        print(f"Model output saved to: {output_file}")
    except Exception as e:
        print(f"Error during LLM call: {e}")


def generate_json_and_call_llm(domain_path, problem_path, solution_path, model_path):
    # User inputs the number of actions
    while True:
        try:
            num_actions = int(input("Enter the number of actions you want to generate the plan: "))
            if num_actions <= 0:
                raise ValueError("Number of actions must be a positive integer.")
            break
        except ValueError as e:
            print(f"Invalid input: {e}. Please try again.")
    # Prepare input data for the LLM
    pddl_domain = read_pddl_domain(domain_path)
    initial_state = get_initial_state(problem_path)
    first_actions = generate_plan_with_user_actions(solution_path, 'temp_plan_file.plan', num_actions)
    states_after_actions = get_states_after_actions(domain_path, problem_path, 'temp_plan_file.plan')
    
    # Store data in the input JSON file
    input_data = {
        "prompt": (
            "We are solving problems in PDDL format. Based on the PDDL domain, "
            "what will be the states after final action? Directly generate your "
            "answer without any explanation and in txt format like the initial state. "
            "Here is a completed example, learn how this works and give me answers in the same format:"
            "initial_state"
            "predicates: "
            "(above f0 f1)"
            "(above f0 f2)"
            "(above f0 f3)"
            "(above f1 f2)"
            "(above f1 f3)"
            "(above f2 f3)"
            "(origin p0 f3)"
            "(destin p0 f2)"
            "(origin p1 f2)"
            "(destin p1 f0)"
            "(lift-at f0)"
            "action_sequence: #"
            "(up f0 f3)"
            "(board f3 p0)"
            "states_after_actions: "
            "(above f0 f1)"
            "(above f0 f2)"
            "(above f0 f3)"
            "(above f1 f2)"
            "(above f1 f3)"
            "(above f2 f3)"
            "(boarded p0)"
            "(destin p0 f2)"
            "(destin p1 f0)"
            "(lift-at f3)"
            "(origin p0 f3)"
            "(origin p1 f2)" 
        ),
        "pddl_domain": pddl_domain.split('\n'),
        "initial_state": initial_state,
        "action_sequence": first_actions,
        "states_after_actions": states_after_actions
    }
    
    with open('input.json', 'w', encoding='utf-8') as f:
        json.dump(input_data, f, ensure_ascii=False, indent=4)
    print("Input JSON saved as input.json")
    
    # Initialize the LLM model
    model = lpb.BlackboxLLM(model_path)
    
    # Call the LLM model and save the result as a TXT file
    call_llm_with_json_input('input.json', model, 'llm_output.txt')


def main():
    domain_path = 'domain-barman-sequencial-optimal.pddl'
    problem_path = 'instance-1-barman-sequential-optimal.pddl'
    solution_path = 'solution-barman-sequential-optimal.pddl'

    #model_path = "/ssd1/kevin/huggingface/Llama-3.1-8B-Instruct"
    model_path = 'gpt-4'
    
    if not os.path.exists(domain_path):
        print(f"Domain file not found: {domain_path}")
        return
    if not os.path.exists(problem_path):
        print(f"Problem file not found: {problem_path}")
        return
    if not os.path.exists(solution_path):
        print(f"Solution file not found: {solution_path}")
        return
    
    generate_json_and_call_llm(domain_path, problem_path, solution_path, model_path)

if __name__ == "__main__":
    main()
