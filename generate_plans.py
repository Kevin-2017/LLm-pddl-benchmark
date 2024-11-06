import llm_plan_bench as lpb
import json
from typing import List, Dict, Union, Optional,Any
import argparse
import os
from pathlib import Path
import openai 



def extract_json_from_response(response: str) -> str:
    """
    Extract JSON content between $$ markers from the response.
    
    Args:
        response (str): Raw response from LLM
        
    Returns:
        str: JSON string between $$ markers or the original string if no markers found
    """
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

def process_domain(domain_data: Dict[str, Any], output_base: Path, model) -> None:
    """
    Process all instances in a domain and save solutions.
    
    Args:
        domain_data: Domain data from the JSON file
        output_base: Base path for output
        model: the BlackboxLLM engine with initialized model
    """
    domain_name = domain_data["domain"]
    
    # Create directories for plans and full answers
    domain_output = output_base / domain_name
    domain_output.mkdir(parents=True, exist_ok=True)
    
    full_answers_dir = output_base / "full_answers" / domain_name
    full_answers_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing domain: {domain_name}")
    
    for prompt_data in domain_data["prompts"]:
        instance_name = prompt_data["instance"]
        output_file = domain_output / f"{Path(instance_name).stem}.sol"
        full_answer_file = full_answers_dir / f"{Path(instance_name).stem}.json"
        
        print(f"  Processing instance: {instance_name}")
        
        try:
            # Send prompt to LLM
            response = model(prompt_data["prompt"])
            
            # Extract JSON content from response
            json_str = extract_json_from_response(response)
            
            # Save full JSON response
            with open(full_answer_file, 'w') as f:
                f.write(json_str)
            
            # Extract and save plan
            plan = extract_plan_from_response(response)
            with open(output_file, 'w') as f:
                f.write(plan)
                
            print(f"    Saved solution to: {output_file}")
            print(f"    Saved full answer to: {full_answer_file}")
            
        except Exception as e:
            print(f"    Error processing {instance_name}: {str(e)}")
            # Write error to both files
            error_msg = f"Error: {str(e)}"
            with open(output_file, 'w') as f:
                f.write(error_msg)
            with open(full_answer_file, 'w') as f:
                f.write(error_msg)


def read_json_input(input_path: str) -> Dict[str, Any]:
    """
    Read and parse input JSON file, handling both all_domains.json and single domain JSON.
    
    Args:
        input_path: Path to the JSON file
        
    Returns:
        dict: Dictionary containing domain data
    """
    with open(input_path, 'r') as f:
        data = json.load(f)
        
    # Check if this is all_domains.json or single domain JSON
    if "domain" in data:
        # Single domain JSON
        return {"single_domain": data}
    else:
        # all_domains.json format
        return data

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
    

    
    # try:
        # Read input JSON
    with open(args.input, 'r') as f:
        all_domains = json.load(f)
    
    # Process each domain
    model = lpb.BlackboxLLM(args.model_path,device = 'cuda:1')
    domains_data = read_json_input(args.input)

    for domain_name, domain_data in domains_data.items():
        process_domain(domain_data, output_base, model)
        
    print("\nProcessing complete!")
    print(f"Solutions saved to: {output_base}")




if __name__ == "__main__":
    # Example JSON path
    # /ssd1/kevin/huggingface/Llama-3.1-8B-Instruct

    main()