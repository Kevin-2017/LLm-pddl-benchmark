from openai import OpenAI
import os
import json
import google.generativeai as genai
import anthropic

anthropic_client = anthropic.Anthropic(
    api_key = os.environ["ANTHROPIC_API_KEY"]
)

genai.configure(api_key=os.environ["GENAI_API_KEY"])
# for m in genai.list_models():
# 	print(m.name)
Gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
client = OpenAI(
	api_key=os.environ["OPENAI_API_KEY"],
)

def get_chat(model, messages):
	# messages = [
	# 	{
	# 		"role": "user/assistant",
	# 		"content": "Hello, Claude"
	# 	}
	# ]
	if model[:2] == "ge":
		new_messages = [{
			"role": message["role"] if message["role"] == "user" else "model",
			"parts": message["content"],
		} for message in messages[:-1]]
		assert new_messages[-1]["role"] == "model"
		# print(Gemini_model)
		chat = Gemini_model.start_chat(history=new_messages)
		response = chat.send_message(messages[-1]["content"])
		used_token = response._result.usage_metadata.total_token_count
		return response.text, used_token
	elif model[:2] == "gp":
		chat_completion = client.chat.completions.create(
			messages=messages,
			model=model,
			top_p=0.95,
		)
		used_token = chat_completion.usage.to_dict()["total_tokens"]
		return chat_completion.choices[0].message.content, used_token
	elif model[:2] == "cl":
		message = anthropic_client.messages.create(
			model=model,
			messages = messages,
			max_tokens=1024,
			top_p=0.95,
		)
		used_token = message.usage.input_tokens + message.usage.output_tokens
		return message.content[0].text, used_token