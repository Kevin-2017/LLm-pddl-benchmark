
import re
import json

# Function to extract initial states from a PDDL problem file and convert to JSON
def extract_initial_state_from_pddl(problem_file):
    # Regular expression to match different types of facts
    init_pattern = r"\(:init(.*?)\)", re.DOTALL
    fact_pattern = r"\((.*?)\)"
    
    # Open and read the PDDL problem file
    with open(problem_file, 'r') as f:
        content = f.read()

    # Find the init section
    match = re.search(init_pattern, content)
    if not match:
        raise ValueError("No init section found in the PDDL problem file.")
    
    init_content = match.group(1).strip()

    # Initialize dictionaries to store predicates and functions
    predicates = []
    functions = []

    # Find all facts in the init section
    for fact in re.findall(fact_pattern, init_content):
        fact = fact.strip()

        # Handle function assignments (e.g., (= (total-cost) 0))
        if fact.startswith("= "):
            parts = fact[2:].strip()
            function_name = parts.split()[0]
            value = " ".join(parts.split()[1:])
            functions.append({
                "function": function_name,
                "value": value
            })
        
        # Handle predicates (e.g., (ontable shaker1))
        else:
            predicates.append(fact)

    # Create a structured JSON format
    initial_state = {
        "predicates": predicates,
        "functions": functions
    }

    return initial_state

# Function to save the initial state to a JSON file
def save_initial_state_to_json(initial_state, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(initial_state, json_file, indent=4)
    print(f"Initial state saved to {output_file}")

# Main function to load PDDL problem, extract initial state, and save it to JSON
def main(problem_file, output_file):
    # Extract initial state from PDDL problem file
    initial_state = extract_initial_state_from_pddl(problem_file)
    
    # Save the initial state to a JSON file
    save_initial_state_to_json(initial_state, output_file)

# Define the PDDL problem file and output JSON file
problem_file = "instance-1-barman.pddl"
output_file = "initial_state.json"

if __name__ == "__main__":
    main(problem_file, output_file)
