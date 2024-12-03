import os
from collections import defaultdict
from collections import OrderedDict
# import google.generativeai as genai
import sys
print(os.getenv("OPENAI_API_KEY"))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import llm_plan_bench as lpb

current_dir = os.path.dirname(os.path.abspath(__file__))
# ollama list
# NAME                                                     ID              SIZE      MODIFIED       
# qwen2.5:72b                                              424bad2cc13f    47 GB     49 minutes ago    
# qwen2.5-coder:32b                                        4bd6cbf2d094    19 GB     57 minutes ago    
# qwen2.5:latest                                           845dbda0ea48    4.7 GB    11 hours ago      
# mistral:latest                                           f974a74358d6    4.1 GB    11 hours ago      
# qwen2.5-coder:latest                                     2b0496514337    4.7 GB    11 hours ago      
# llama3.2:latest                                          a80c4f17acd5    2.0 GB    11 hours ago      
# hf.co/bartowski/Llama-3-Groq-70B-Tool-Use-GGUF:Q5_K_S    2a4595cb3862    48 GB     3 weeks ago       
# llama3.1:70b-text-fp16                                   391fbe608631    141 GB    4 weeks ago       
# llama3.1:70b-instruct-fp16                               80d34437631f    141 GB    4 weeks ago       
# llama3.1:70b-instruct-q4_0                               c0df3564cfe8    39 GB     4 weeks ago       
# llama3:70b-instruct                                      786f3184aec0    39 GB     4 weeks ago       
# llama3.1:70b                                             c0df3564cfe8    39 GB     5 weeks ago       
# llama3.1:latest                                          42182419e950    4.7 GB    5 weeks ago


model_dict = OrderedDict()

def get_chat(model, messages):
	# messages = [
	# 	{
	# 		"role": "user/assistant",
	# 		"content": "Hello, Claude"
	# 	}
	# ]
	# save messages to a random file name
	# random_file_name = os.path.join(current_dir, str(random.randint(1,1000)) + ".json")
	# with open(random_file_name, "w") as f:
	# 	json.dump(messages, f)

	if model in model_dict:
		model_dict.move_to_end(model)
	else:
		if len(model_dict) >= 2:
			old_model, old_instance = model_dict.popitem(last=False)
			del old_instance
		model_dict[model] = lpb.BlackboxLLM(model)

	return model_dict[model](messages), 0

	# if model[:2] == "ge":
	# 	new_messages = [{
	# 		"role": message["role"] if message["role"] == "user" else "model",
	# 		"parts": message["content"],
	# 	} for message in messages[:-1]]
	# 	assert new_messages[-1]["role"] == "model"
	# 	# print(Gemini_model)
	# 	chat = Gemini_model.start_chat(history=new_messages)
	# 	response = chat.send_message(messages[-1]["content"])
	# 	used_token = response._result.usage_metadata.total_token_count
	# 	return response.text, used_token
	# elif model[:2] == "gp":
	# 	chat_completion = client.chat.completions.create(
	# 		messages=messages,
	# 		model=model,
	# 		top_p=0.95,
	# 	)
	# 	used_token = chat_completion.usage.to_dict()["total_tokens"]
	# 	return chat_completion.choices[0].message.content, used_token
	# elif model[:2] == "cl":
	# 	message = anthropic_client.messages.create(
	# 		model=model,
	# 		messages = messages,
	# 		max_tokens=1024,
	# 		top_p=0.95,
	# 	)
	# 	used_token = message.usage.input_tokens + message.usage.output_tokens
	# 	return message.content[0].text, used_token