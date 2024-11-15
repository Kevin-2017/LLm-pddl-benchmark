# LLM PLAN BENCH 
A developing branch to benchmark LLM ability on planning

## Updates 
* Dataset from IPC2023 Numeric Track available at: https://github.com/ipc2023-numeric/ipc2023-dataset/
* Additional updates can be added here
## submodules 

## Installation val
```bash
cd submodule/VAL
make clean
sed -i 's/-Werror //g' Makefile
make -j2
#the validate file should be generated after make
```

### Fast Downward
```bash
cd submodule/downward
./build.py
cd ../..
```
### Install this repo 
```bash
cd <path to this repo>
pip install -e . 
```
# Commands 
Prompt generation 
```bash
python llm_plan_bench/models/prompt_generation/plan_solver_prompt.py
```
LLM Plan generation 
for model_path currently just use llama (/ssd1/kevin/huggingface/Llama-3.1-8B-Instruct)
```bash
python generate_plans.py \ 
--input ./data/inputs/solve_plan/blocksworld.json \ 
--output experiments/<output folder name> \ 
--model_path <>
```
Classical planner generation (currently only support fast downward)
```bash
python classic_planner.py \ --input ./data/pddl \ 
--output experiments/<output folder name>
```
Validator 
```bash
python validate_plans.py \ 
--data_path ./data/pddl \ 
--solutions_path ./experiments/<output folder name>
--domain <Specific domain to validate (empty for all domains)>
```

### data
currently all the data is in the data folder, but this would change later when we scaled up. 

### Acknowledgement 
The pddl data is from https://github.com/ipc2023-numeric/ipc2023-dataset/ 

### Domain Description Document
https://docs.google.com/document/d/1kTAL6AVW-7GO9Wak7cgrXwb4GYShBeTeMkZnhTD1wqE/edit?usp=sharing


The llm engine is based on textgrad 


