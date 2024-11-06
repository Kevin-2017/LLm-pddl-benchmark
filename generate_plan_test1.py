import llm_plan_bench as lpb
import json
from typing import List, Dict, Union, Optional



def read_prompts_from_json(json_path: str, 
                          domain_file: Optional[str] = None, 
                          problem_file: Optional[str] = None) -> Union[str, List[Dict], None]:
    """
    Read prompts from a JSON file. Can return either a specific prompt or all prompts.
    
    Args:
        json_path (str): Path to the JSON file containing prompts
        domain_file (str, optional): Path to specific domain file to match
        problem_file (str, optional): Path to specific problem file to match
        
    Returns:
        Union[str, List[Dict], None]: 
            - If domain_file and problem_file are provided: returns matching prompt string
            - If no specific files are provided: returns full list of prompt dictionaries
            - Returns None if no matching prompt is found or if JSON is invalid
    
    Example:
        # Get specific prompt
        prompt = read_prompts_from_json(
            "prompts.json",
            domain_file="/path/to/domain.pddl",
            problem_file="/path/to/problem.pddl"
        )
        
        # Get all prompts
        all_prompts = read_prompts_from_json("prompts.json")
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Validate JSON structure
        if not isinstance(data, dict) or "prompts" not in data:
            print(f"Error: Invalid JSON structure in {json_path}")
            return None
        
        # If specific files are provided, find matching prompt
        if domain_file and problem_file:
            for prompt_data in data["prompts"]:
                if (prompt_data["domain_file"] == domain_file and 
                    prompt_data["problem_file"] == problem_file):
                    return prompt_data["prompt"]
            print(f"No matching prompt found for domain: {domain_file} and problem: {problem_file}")
            return None
        
        # If no specific files provided, return all prompts
        return data["prompts"]
    
    except FileNotFoundError:
        print(f"Error: File not found - {json_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_path}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")
        return None

if __name__ == "__main__":
    # Example JSON path
    json_path = "/ssd1/kevin/projects/llm_plan_bench/data/inputs/solve_plan/blocksworld.json"
    # model = lpb.BlackboxLLM("meta-llama/Llama-3.1-8B-Instruct",device = 'cuda:1'
    # )
    model = lpb.BlackboxLLM("/ssd1/kevin/huggingface/Llama-3.1-8B-Instruct",device = 'cuda:1'
    )
    # /ssd1/kevin/huggingface/Llama-3.1-8B-Instruct

    questions = read_prompts_from_json(json_path)
    if questions:
        print("Number of prompts:", len(questions))
        print("\nFirst prompt example:")
        print(questions[0]['prompt'])

    answer = model(questions[0]['prompt'])
    print(answer)