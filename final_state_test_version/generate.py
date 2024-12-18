import subprocess
import os
import time
import glob

# Generate sas plan
def generate_plan(domain_file, problem_file, downward_path='/Users/qing/downward/fast-downward.py', timeout=300):
    plan_file = "sas_plan"
    
    # Command to run Fast Downward with a default heuristic (seq-sat-lama-2011)
    cmd = [
        "python3", downward_path,
        "--alias", "seq-sat-lama-2011",  # The heuristic for Fast Downward
        "--plan-file", plan_file,  # Output the plan to a file named "sas_plan"
        domain_file,  # Path to domain file
        problem_file  # Path to problem file
    ]

    print("Starting generate_plan...")

    try:
        start_time = time.time()
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
            while True:
                # Check if the process has finished
                retcode = process.poll()

                # Read line by line to track progress
                output = process.stdout.readline()
                if output:
                    print("Fast Downward Output:", output.strip())  # Print each line of output as it arrives

                # If process finished, break out of the loop
                if retcode is not None:
                    print("Fast Downward process ended.")
                    break

                # Check for timeout
                if time.time() - start_time > timeout:
                    process.terminate()  # Stop Fast Downward if it's still running
                    print("Plan generation timed out.")
                    return None

        # Check if plan file exists after the process ends
        plan_files = glob.glob("sas_plan*")  # Find all files matching "sas_plan*"
        if plan_files:
            first_plan_file = plan_files[0]  # Use the first plan found (we expect only one)
            print("Plan generated successfully:", first_plan_file)
            return first_plan_file
        else:
            print("No plan files found.")
            return None

    except Exception as e:
        print(f"An error occurred during Fast Downward execution: {e}")
        return None

# Example of usage
# change
domain_file = "domain-barman-sequencial-optimal.pddl"
problem_file = "instance-2-barman-sequential-optimal.pddl"
plan = generate_plan(domain_file, problem_file)

if plan:
    print(f"Generated plan: {plan}")
else:
    print("Failed to generate a plan.")
