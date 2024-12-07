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

# def get_initial_state(problem_path):
#     try:
#         with open(problem_path, 'r', encoding='utf-8') as file:
#             content = file.read()
        
#         init_block = extract_init_content(content)
#         if not init_block:
#             print("No :init section found or unmatched parentheses.")
#             return {"predicates_state": set(), "functions_state": {}}
        
#         init_content = init_block[len('(:init'): -1].strip()
#         predicates = [line.strip() for line in init_content.split('\n') if line.strip()]

#         predicates_state = set()
#         functions_state = {}

#         for predicate in predicates:
#             # Check for numeric function assignment (e.g., (= (total-cost) 0))
#             if predicate.startswith("(="):
#                 try:
#                     function_part = predicate[len("(="):].strip()[:-1].strip()  # Strip `(= ` and closing `)`
#                     function, value = function_part.split()  # Split into function name and value
#                     function_name = function[1:-1]  # Remove surrounding parentheses
#                     functions_state[function_name] = float(value)
#                 except ValueError:
#                     print(f"Failed to parse function from predicate: {predicate}")
#             else:
#                 # Add normal predicates to the state
#                 predicates_state.add(predicate)

#         return {"predicates_state": predicates_state, "functions_state": functions_state}

#     except FileNotFoundError:
#         print(f"Problem file not found: {problem_path}")
#         return {"predicates_state": set(), "functions_state": {}}
#     except Exception as e:
#         print(f"Unexpected error: {e}")
#         return {"predicates_state": set(), "functions_state": {}}


def generate_plan_with_first_two_actions(solution_path, output_plan_path):
    with open(solution_path, 'r', encoding='utf-8') as file:
        actions = file.readlines()
    first_two_actions = [action.strip() for action in actions[:2] if action.strip()]
    with open(output_plan_path, 'w', encoding='utf-8') as plan_file:
        for action in first_two_actions:
            plan_file.write(action + "\n")
    return first_two_actions

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

# Main function to generate JSON and call the LLM
# def generate_json_and_call_llm(domain_path, problem_path, solution_path, model_path):
#     # Prepare input data for the LLM
#     pddl_domain = read_pddl_domain(domain_path)
#     initial_state = get_initial_state(problem_path)
#     first_two_actions = generate_plan_with_first_two_actions(solution_path, 'temp_plan_file.plan')
#     states_after_actions = get_states_after_actions(domain_path, problem_path, 'temp_plan_file.plan')
    
#     # 将数据存储到初始 JSON 文件
#     input_data = {
#         "prompt": "We are solving problems in PDDL format. Based on the PDDL domain, what will be the states after each action? Directly generate your answer without any explanation and in txt format like this: \n(empty shot4)\n(handempty left)\n(handempty right)",
#         "pddl_domain": pddl_domain.split('\n'),
#         "initial_state": initial_state,
#         "action_sequence": first_two_actions,
#         "states_after_actions": states_after_actions  # 模型生成前的状态
#     }
    
#     with open('input.json', 'w', encoding='utf-8') as f:
#         json.dump(input_data, f, ensure_ascii=False, indent=4)
#     print("Input JSON saved as input.json")
    
#     # Initialize the LLM model
#     model = lpb.BlackboxLLM(model_path, device='cuda:6')
#     # model = lpb.BlackboxLLM(model_path, device='cuda:7', attn_implementation="flash_attention_2")

    
#     # 调用 LLM 模型，并将结果保存到新的 JSON 文件
#     call_llm_with_json_input('input.json', model, 'llm_output.json')

def generate_json_and_call_llm(domain_path, problem_path, solution_path, model_path):
    # Prepare input data for the LLM
    pddl_domain = read_pddl_domain(domain_path)
    initial_state = get_initial_state(problem_path)
    first_two_actions = generate_plan_with_first_two_actions(solution_path, 'temp_plan_file.plan')
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
        "action_sequence": first_two_actions,
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
    #domain_path = '/ssd1/haisu/project/LLm-pddl-benchmark/final_state_test_version/domain-elevator-strips-simple-typed.pddl'
    #problem_path = '/ssd1/haisu/project/LLm-pddl-benchmark/final_state_test_version/instance-10-elevator-strips-simple-typed.pddl'
    #solution_path = '/ssd1/haisu/project/LLm-pddl-benchmark/final_state_test_version/solution-10-elevator-strips-simple-typed.pddl'



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
