import argparse
import glob
import os
import subprocess
import time

from domain import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM-Planner")
    parser.add_argument('--domain', type=str, choices=DOMAINS, default="tyreworld")
    parser.add_argument('--run', type=str, default="run1")
    args = parser.parse_args()
    domain = eval(args.domain.capitalize())()
    domain_pddl_file = domain.get_domain_pddl_file()
    if args.domain == "tyreworld":
        domain_pddl_file = domain_pddl_file.split('.pddl')[0] + "_validation.pddl"

    counter = 0
    

    for task in range(len(domain)):
        output_path = os.path.join(f"experiments/{args.run}/plans/llm_ic_pddl/{args.domain}/", "validation.txt")
        output_file = open(output_path, "w")
        output = ""

        task_nl_file, task_pddl_file = domain.get_task_file(task) 
        suffix = domain.get_task_suffix(task)
        plan_path = os.path.join(f"experiments/{args.run}/plans/", suffix + "*")
        plan_files = glob.glob(plan_path)
        plan_files = [plan for plan in plan_files if not plan.endswith('sas')]
        plan_valid = 0
        for plan in plan_files:
            # command = f"validate {domain_pddl_file} {task_pddl_file} {plan}"
            result = subprocess.run(["validate", "-v", domain_pddl_file, task_pddl_file, plan], stdout=subprocess.PIPE)
            output += result.stdout.decode('utf-8')

            if "Plan valid" in result.stdout.decode('utf-8'):
                plan_valid = 1
        counter += plan_valid
        output_file.write(output)
        print (f"{counter} plans are valid")
        # print (f"{counter/}")


