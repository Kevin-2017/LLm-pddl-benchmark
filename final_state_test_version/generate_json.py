
import json
import random
import subprocess
import os
import re

# Function to read the PDDL domain from a file
def read_pddl_domain(domain_path):
    with open(domain_path, 'r') as file:
        return file.read()

# Function to read the PDDL problem from a file
def read_pddl_problem(problem_path):
    with open(problem_path, 'r') as file:
        return file.read()

# Function to get first 2 actions from the solution and generate a PDDL file
def generate_pddl_with_first_two_actions(solution_path, output_pddl_path):
    with open(solution_path, 'r') as file:
        actions = file.readlines()
    first_two_actions = actions[:2]  # Get the first two actions
    first_two_actions = [action.strip() for action in first_two_actions]
    
    # PDDL file content
    # Assuming that actions in solution_path are in a format that can be directly written to a PDDL action sequence
    # If not, you may need to adjust the formatting accordingly
    pddl_content = "; Solution in PDDL format\n\n" + "\n".join(first_two_actions) + "\n"
    
    # Write to the output PDDL file
    with open(output_pddl_path, 'w') as pddl_file:
        pddl_file.write(pddl_content)
    
    # Return the name of the generated PDDL file (so it can be used in the next function)
    return output_pddl_path

# Function to get initial state from the problem file and store as a list of string
def get_initial_state(problem_path):
    try:
        with open(problem_path, 'r') as file:
            problem_content = file.read()

        # Use a regular expression to find the initial state section
        # Adjusted regex to correctly capture multiple init facts
        match = re.search(r'\(:init\s*(.*?)\)', problem_content, re.DOTALL)
        if match:
            # Extract the content inside the (:init ...) block
            init_state_content = match.group(1)

            # Split the content into individual statements and remove extra whitespace
            # This assumes that each fact is enclosed in parentheses
            initial_state = re.findall(r'\([^\)]+\)', init_state_content)

            return initial_state
        else:
            print("No initial state found in the problem file.")
            return []

    except FileNotFoundError:
        print(f"Problem file not found: {problem_path}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

# Function to get states after actions by running state_print.py with the sequence of actions
def get_states_after_actions(domain_path, problem_path, pddl_file_path):
    states = []
    try:
        # Run state_print.py and pass the generated PDDL file as an argument
        # Ensure that state_print.py is correctly handling the input files
        state = subprocess.check_output(['python3', 'state_print.py', domain_path, problem_path, pddl_file_path]).decode('utf-8')
        states.append(state.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error executing state_print.py: {e}")
    return states

def generate_json(domain_path, problem_path, solution_path):
    # Read the PDDL domain and problem
    pddl_domain = read_pddl_domain(domain_path)
    pddl_problem = read_pddl_problem(problem_path)
    
    # Get the initial state as a list of strings
    initial_state = get_initial_state(problem_path) 
    
    # Generate the PDDL file with the first two actions and get the file path
    pddl_file = generate_pddl_with_first_two_actions(solution_path, 'temp_pddl_file.pddl')
    
    # Get the states after actions by passing the generated PDDL file
    states_after_actions = get_states_after_actions(domain_path, problem_path, pddl_file)
    
    # Read the generated PDDL file content to include in JSON
    try:
        with open(pddl_file, 'r') as file:
            action_sequence_content = file.read()
    except FileNotFoundError:
        print(f"Generated PDDL file not found: {pddl_file}")
        action_sequence_content = ""
    
    # Prepare the final JSON structure
    data = {
        "prompt": "We are solving problems in PDDL format. Based on the PDDL domain, what will be the states after each action? Generate your answer without explanation and in txt format like this: \nabove(f0, f1)\nabove(f0, f2)\nabove(f0, f3)",
        "pddl_domain": pddl_domain,  # Store as string without JSON parsing
        "initial_state": initial_state,  # Now directly using the list of strings for initial state
        "action_sequence": action_sequence_content,  # Store the actions content instead of file path
        "states_after_actions": states_after_actions
    }
    
    # Write the data to a JSON file
    with open('output.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

def main():
    # Paths to the PDDL domain, problem, and solution files
    domain_path = 'domain-barman-sequencial-optimal.pddl'
    problem_path = 'instance-1-barman-sequential-optimal.pddl'
    solution_path = 'solution-barman-sequential-optimal.pddl'

    # Ensure the paths are correct and the files exist
    if not os.path.exists(domain_path):
        print(f"Domain file not found: {domain_path}")
        return

    if not os.path.exists(problem_path):
        print(f"Problem file not found: {problem_path}")
        return

    if not os.path.exists(solution_path):
        print(f"Solution file not found: {solution_path}")
        return

    # Call the function to generate the JSON output
    generate_json(domain_path, problem_path, solution_path)

if __name__ == "__main__":
    main()
