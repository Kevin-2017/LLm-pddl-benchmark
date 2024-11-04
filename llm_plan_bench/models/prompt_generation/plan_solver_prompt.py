from llm_plan_bench.models.prompt_generation import PromptGenerator, read_file
import argparse
import os
import json



class PlanningPromptGenerator(PromptGenerator):
    def forward(self) -> str:
        """
        Generate a prompt for PDDL planning.
        
        Returns:
            str: Generated prompt asking for a PDDL format plan
        """
        prompt = f"A planning problem is described as domain PDDL file {self.domain_pddl} and the task is {self.task_pddl}\n"
        prompt += "return a pddl format plan without any extra text."
        return prompt
    def save_json(self, output_path: str, domain_path: str, task_path: str):
        """
        Save the prompt to a JSON file with index structure.
        
        Args:
            output_path (str): Path to save the JSON file
            domain_path (str): Path to the domain PDDL file
            task_path (str): Path to the task PDDL file
        """
        prompt = self.forward()
        
        # Create index structure
        data = {
            "prompts": [
                {
                    "domain_file": domain_path,
                    "problem_file": task_path,
                    "prompt": prompt
                }
            ]
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # If file exists, update it, otherwise create new
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r') as f:
                    existing_data = json.load(f)
                    # Check if this domain/problem combination already exists
                    for item in existing_data["prompts"]:
                        if item["domain_file"] == domain_path and item["problem_file"] == task_path:
                            item["prompt"] = prompt
                            break
                    else:  # If not found, append new
                        existing_data["prompts"].append(data["prompts"][0])
                    data = existing_data
            except json.JSONDecodeError:
                pass  # If JSON is invalid, overwrite with new data

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Generate prompts from PDDL files')
    parser.add_argument('--domain', type=str, default='/ssd1/kevin/projects/llm_plan_bench/data/pddl/blocksworld/domain.pddl',
                        help='Path to domain PDDL file')
    parser.add_argument('--task', type=str, 
                        default='/ssd1/kevin/projects/llm_plan_bench/data/pddl/blocksworld/p01.pddl',
                        help='Path to task PDDL file')
    parser.add_argument('--output', type=str, default='/ssd1/kevin/projects/llm_plan_bench/data/inputs/blocksworld.json',
                        help='Path to save the generated prompt')
    
    args = parser.parse_args()
    # TODO change it to another way, store other information in the json? 
    try:
        # Read PDDL files
        domain_content = read_file(args.domain)
        task_content = read_file(args.task)

        # Create generator instance
        generator = PlanningPromptGenerator(domain_content, task_content)

        # Generate and save prompt as JSON
        generator.save_json(args.output, args.domain, args.task)
        
        print(f"Prompt generated and saved to: {args.output}")
        print("\nGenerated JSON content preview:")
        print("-" * 50)
        with open(args.output, 'r') as f:
            data = json.load(f)
            print(json.dumps(data, indent=2)[:500] + "..." if len(json.dumps(data, indent=2)) > 500 else json.dumps(data, indent=2))
        print("-" * 50)

    except FileNotFoundError as e:
        print(f"Error: Could not find file - {e}")
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")



