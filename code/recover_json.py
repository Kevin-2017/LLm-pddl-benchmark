import sys
import os
sys.path.append(os.path.abspath(".."))
import json
import time
import llm_plan_bench as lpb
import regex
# Regex pattern for recursive matching
json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}', regex.DOTALL)
model = lpb.BlackboxLLM("gpt-4o")

skip_file_list = json.load(open("skip_file_list.json", "r"))
# skip_file_list = ["#103_en.json"]
for filename in skip_file_list:
    data = open("loj/" + filename, "r").read()
    new_data = model(f"\n{data}\n\nPlease convert the above incorrect JSON data to correct JSON data. Usually you should fix the format error: Invalid escape character in string, If there is a single \\ with no meaning(usually a latex syntax), you should add another \\ after it. Notice, you should take care of the latex syntax and keep it. The result should be a json object with a single key 'json' and a string value as the correct json.")
    print(new_data)
    try:
        matches = json_pattern.findall(new_data)
        for match in matches:
            try:
                parsed_json = json.loads(match)
            except Exception as e:
                print("Invalid JSON Found:", match)
        translation = parsed_json["json"]
    except Exception as e:
        print(e)
        continue
    try:
        translation = json.loads(translation)
    except Exception as e:
        print(e)
        continue
    json.dump(translation, open("loj/" + filename, "w"), indent=4, ensure_ascii=False)