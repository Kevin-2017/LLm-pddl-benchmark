import sys
import os
sys.path.append(os.path.abspath(".."))
import json
import time
import llm_plan_bench as lpb
import regex
# Regex pattern for recursive matching
json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}', regex.DOTALL)
model = lpb.BlackboxLLM("gpt-4o-mini")

import json, regex
json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}', regex.DOTALL)
def get_translation(content):
    content = model(f"Translate All the Chinese characters in this string into english (this is a json file, you should translate both the keys and the values): <start>{content}<end> The result should be a json object with a single key 'translation' and a string value as the translation. You can only output english.")
    # print(content)
    try:
        matches = json_pattern.findall(content)
        for match in matches:
            try:
                parsed_json = json.loads(match)
            except Exception as e:
                print("Invalid JSON Found:", match)
        translation = parsed_json["translation"]
    except Exception as e:
        print(e)
    try:
        return translation
    except Exception as e:
        print(e)
        return None
    

from tqdm import tqdm
base_path = "loj/"
while True:
    cnt = 0
    all_json_files = [f for f in os.listdir(base_path) if f.endswith('.json')]
    all_json_files = sorted(all_json_files)
    for filename in tqdm(all_json_files):
        if "_en.json" in filename:
            continue
        new_file_name = filename.split(".")[0] + "_en.json"
        if new_file_name in all_json_files:
            continue
        file_str = open(base_path + filename, "r").read()
        print(f"Translating {filename}")
        new_file = get_translation(file_str) # str
        if new_file is None:
            print(f"Failed to translate {filename}")
            continue
        # change new file to json
        new_file_name = filename.split(".")[0] + "_en.json"
        json.dump(new_file, open(base_path + new_file_name, "w"), indent=4, ensure_ascii=False)
        cnt += 1
        # print(f"Translated {filename} to {new_file_name}")
    time.sleep(60)
    # if cnt == 0:
    #     break