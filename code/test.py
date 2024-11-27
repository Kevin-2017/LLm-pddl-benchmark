import requests
import json
import sys
import os
import copy
import time
sys.path.append(os.path.abspath(".."))
import llm_plan_bench as lpb
model_name = "ollama-qwen2.5-coder:32b"
lang = "py.py3"
max_trial_times = 5
model = lpb.BlackboxLLM(model_name)

username = "yao"  # Replace with your username
password = "yaojianzhu"  # Replace with your password
web_ip = "http://cnyaojz.com:25568"

# Step 1: Log in to get the session cookie
login_url = f"{web_ip}/login"
login_data = {
	"uname": username,
	"password": password,
	"rememberme": True
}
session = requests.Session()
login_response = session.post(login_url, json=login_data)

if login_response.status_code != 200:
	print("Login failed:", login_response.text)
	exit()

import regex
json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}', regex.DOTALL)
code_to_status = {
	0: "Waiting",
	1: "Accepted",
	2: "Wrong Answer",
	3: "Time Limit Exceeded",
	4: "Memory Limit Exceeded",
	5: "Output Limit Exceeded",
	6: "Runtime Error",
	7: "Compile Error",
	8: "System Error",
	9: "Canceled",
	10: "ETC",
	11: "Hacked",
	20: "Judging",
	21: "Compiling",
	22: "Fetched",
	30: "Ignored",
	31: "Format Error",
	32: "Hack Successful",
	33: "Hack Unsuccessful"
}

def append_user_message(player_messages, player_store_message, user_message):
	# check the role of the last message
	if len(player_messages) == 0 or player_messages[-1]["role"] == "assistant":
		player_messages.append({
			"role": "user",
			"content": user_message
		})
		player_store_message.append({
			"role": "user",
			"content": user_message
		})
	elif player_messages[-1]["role"] == "user":
		player_messages[-1]["content"] += "\n" + user_message
		player_store_message[-1]["content"] += "\n" + user_message

def append_assistant_message(player_messages, player_store_message, assistant_message):
	player_messages.append({
		"role": "assistant",
		"content": assistant_message
	})
	player_store_message.append({
		"role": "assistant",
		"content": assistant_message
	})

def parse_problem_text(pdoc):
	content = pdoc['content']
	title = pdoc['title']
	tag = pdoc['tag']
	config = pdoc['config']
	problem_text = "Please solve the following problem:\n\n"
	problem_text += f"Title: {title}\n"
	problem_text += f"Tag: {tag}\n\n"
	problem_text += f"Content: {content}\n\n"
	problem_text += f"Config: {config}\n\n"
	return problem_text

def parse_feedback_text(rdoc):
	score = rdoc['score']
	time = rdoc['time']
	memory = rdoc['memory']
	judge_texts = rdoc['judgeTexts']
	compiler_texts = rdoc['compilerTexts']
	test_cases = rdoc['testCases']
	feedback_text = f"Score: {score}\n"
	feedback_text += f"Time: {time}\n"
	feedback_text += f"Memory: {memory}\n\n"
	feedback_text += "Judges:\n"
	for judge_text in judge_texts:
		feedback_text += f"{judge_text}\n"
	feedback_text += "\n"
	feedback_text += "Compiler:\n"
	for compiler_text in compiler_texts:
		feedback_text += f"{compiler_text}\n"
	feedback_text += "\n"
	# "testCases": [
	#         {
	#             "id": 2,
	#             "subtaskId": 1,
	#             "status": 2,
	#             "score": 0,
	#             "time": 0,
	#             "memory": 6628,
	#             "message": "User output longer than standard answer."
	#         },
	feedback_text += "Test cases:\n"
	for test_case in test_cases:
		feedback_text += f"Test case {test_case['id']}: {test_case['message']}\n"
		feedback_text += f"Status: {code_to_status[test_case['status']]}\n"
		feedback_text += f"Score: {test_case['score']}\n"
		feedback_text += f"Time: {test_case['time']}\n"
		feedback_text += f"Memory: {test_case['memory']}\n\n"
	return feedback_text

total_score = 0

# for problem_id in range(102, 182):
for problem_id in range(103, 113):
	fetch_url = f"{web_ip}/p/{problem_id}"
	headers = {
	"Accept": "application/json"
	}
	problem_text = None
	try:
		fetch_response = session.get(fetch_url, headers=headers)
		if fetch_response.status_code != 200:
			print("Fetch problem failed:", fetch_response.text)
			exit()
		problem = fetch_response.json()
		problem_text = parse_problem_text(problem["pdoc"])
		json.dump(problem, open(f"problem-{problem_id}.json", "w"), ensure_ascii=False, indent=4)
	except Exception as e:
		print("Fetch problem failed:", e)
		continue
	print(problem_text)
	sleep_time = problem["pdoc"]["config"]["timeMax"] * (len(problem["pdoc"]["data"]) / 2) / 1000
	messages = [
		{
			"role": "user",
			"content": problem_text
		}
	]
	# Chain of Thought, ask as user, ask the bot to generate any useful information, experience, tricks, knowledge related to solving this problem
	append_user_message(messages, copy.deepcopy(messages), "Please first tell me any related information, experience, tricks, knowledge which is useful for solving this problem. Please explain every knowledge in detail.")
	content = model(messages)
	append_assistant_message(messages, copy.deepcopy(messages), content)
	append_user_message(messages, copy.deepcopy(messages), f"""Now please explain your solution in detail, and generate the finalized code solution for this problem. I will upload the code to the online judge and then give you the feedback. Please format your response in a json file. The output must be in json format. The first key should be 'explanation', the second key should be 'lang' (compiler specified above in config), and the third key should be 'code'. The value should all be string. Please use the programming language lang = {lang}. Thank you very much! You should generate a whole and complete program that can be compiled and run directly in code.""")
	this_score = 0
	for trial_times in range(max_trial_times):
		while True:
			content = model(messages)
			try:
				matches = json_pattern.findall(content)
				for match in matches:
					try:
						parsed_json = json.loads(match)
						break
					except Exception as e:
						print(e)
						continue
			except Exception as e:
				print(e)
				continue
			if "explanation" in parsed_json.keys() and "lang" in parsed_json.keys() and "code" in parsed_json.keys():
				break
		print(content)
		append_assistant_message(messages, copy.deepcopy(messages), content)
		code = parsed_json["code"]
		submit_url = f"{web_ip}/p/{problem_id}/submit"
		submit_data = {
			"lang": lang,
			"code": code,
		}
		headers = {
			"Accept": "application/json"
		}
		submit_response = session.post(submit_url, json=submit_data, headers=headers)
		rid = None

		# Step 3: Check submission response
		if submit_response.status_code == 200:
			print("Submission successful")
			print("Response:", submit_response.json())
			rid = submit_response.json()["rid"]
			print("rid:",submit_response.json()["rid"])
		else:
			print("Submission failed")
			print("Status code:", submit_response.status_code)
			print("Response:", submit_response.text)
			# log
			continue
		# /record/:rid
		time.sleep(sleep_time)
		if rid is None:
			print("No record ID found, exiting...")
			# log
			continue
		# rid = "672836121431fba1f87ae7cc"  # Use the actual record ID
		result_url = f"{web_ip}/record/{rid}"
		headers = {
			"Accept": "application/json"
		}
		response = session.get(result_url, headers=headers)
		if response.status_code == 200:
			result = response.json()
		else:
			print("Failed to retrieve result:", response.status_code)
		feedback_text = parse_feedback_text(result["rdoc"])
		this_score = max(this_score, result["rdoc"]["score"])
		if result["rdoc"]["score"] == 100:
			print("Passed")
			break
		else:
			append_user_message(messages, copy.deepcopy(messages), feedback_text)
			append_user_message(messages, copy.deepcopy(messages), f"""Please explain the error in your code and try to fix it. Please format your response in a json file. The output must be in json format. The first key should be 'explanation', the second key should be 'lang' (compiler specified above in config), and the third key should be 'code'. The value should all be string. Please lang = {lang}. Thank you very much! You should generate a whole and complete program that can be compiled and run directly in code.""")
			continue
	# log
	print("Finish problem", problem_id)
	json.dump({
		"problem_id": problem_id,
		"model_name": model_name,
		"trial_times": trial_times+1,
		"scores": this_score,
		"lang": lang,
		"messages": messages,
	}, open(f"problem-{problem_id}-messages-{model_name}-{lang}.json", "w"), ensure_ascii=False, indent=4)
	total_score += this_score

print("Finish all problems")
print("Model:", model_name)
print("Total score:", total_score)

