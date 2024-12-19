from openai import OpenAI
from pettingzoo.classic import rps_v2
import os
import re
import json
import sys
json_pattern = re.compile(r"(\{(.|\n)*\})")
client = OpenAI(
	api_key=os.environ["OPENAI_API_KEY"],
)

max_cycles = 15


first_player_initial_prompt = f"""
You are playing a game called Rock Paper Scissors Spock Lizard. Rock, Paper, Scissors Spock Lizard is a 2-player hand game where each player chooses either rock, paper, scissors, spock or lizard and reveals their choices simultaneously. If both players make the same choice, then it is a draw. However, if their choices are different, the winner is determined as follows: Scissors cuts Paper covers Rock crushes Lizard poisons Spock smashes Scissors decapitates Lizard eats Paper disproves Spock vaporizes Rock crushes Scissors. The game is played in a series of rounds (a total of {max_cycles}). The player who wins the most rounds wins the game. You are player 0.
"""

second_player_initial_prompt = f"""
You are playing a game called Rock Paper Scissors Spock Lizard. Rock, Paper, Scissors Spock Lizard is a 2-player hand game where each player chooses either rock, paper, scissors, spock or lizard and reveals their choices simultaneously. If both players make the same choice, then it is a draw. However, if their choices are different, the winner is determined as follows: Scissors cuts Paper covers Rock crushes Lizard poisons Spock smashes Scissors decapitates Lizard eats Paper disproves Spock vaporizes Rock crushes Scissors. The game is played in a series of rounds (a total of {max_cycles}). The player who wins the most rounds wins the game. You are player 0.
"""

action_prompt = f"""
Now it's your move for the new round. Please enter your action. You should serialize the output to a json object with the key "action" and the value as a number representing your action. Available actions are: rock:0, paper:1, scissors:2, lizard:3, spock:4.
"""

first_player_messages = [
	{
		"role": "user",
		"content": first_player_initial_prompt,
	},
	{
		"role": "assistant",
		"content": "Sure, let's start. "
	},
] 
second_player_messages = [
	{
		"role": "user",
		"content": second_player_initial_prompt,
	},
	{
		"role": "assistant",
		"content": "Sure, let's start. "
	},
]


env = rps_v2.env(num_actions=5, max_cycles=max_cycles, render_mode=None)
env.reset()
cnt = 0
win = None
total_tokens = 0
player1_model = "gpt-4o-mini"
player2_model = "gpt-4o"
game_log = []
total_reward = {"player_0": 0, "player_1": 0}
for agent in env.agent_iter():
	cnt += 1
	observation, reward, termination, truncation, info = env.last()
	rewards = env.rewards
	print(observation)
	print(agent)
	print(env.rewards)
	for k in rewards:
		total_reward[k] += rewards[k]
	if termination or truncation:
		action = None
	else:
		if agent == 'player_0':
			# first_player
			first_player_messages.append({
				"role": "user", 
				"content": "In the last round, your opponent plays a : \n" + ["rock", "paper", "scissors", "lizard", "spock", "none"][observation] + "\n" + action_prompt
			})
			chat_completion = client.chat.completions.create(
				messages=first_player_messages,
				model=player1_model,
			)
			print(chat_completion.choices[0].message.content)
			first_player_messages.append({
				"role": "assistant",
				"content": chat_completion.choices[0].message.content
			})
			total_tokens += chat_completion.usage.to_dict()["total_tokens"]
			action = json.loads(re.search(json_pattern, chat_completion.choices[0].message.content).group())["action"]
			print("Action is ", action)
		elif agent == 'player_1':
			# second_player
			second_player_messages.append({
				"role": "user", 
				"content": "In the last round, your opponent plays a : \n" + ["rock", "paper", "scissors", "lizard", "spock", "none"][observation] + "\n" + action_prompt
			})
			chat_completion = client.chat.completions.create(
				messages=second_player_messages,
				model=player2_model,
			)
			print(chat_completion.choices[0].message.content)
			second_player_messages.append({
				"role": "assistant",
				"content": chat_completion.choices[0].message.content
			})
			total_tokens += chat_completion.usage.to_dict()["total_tokens"]
			action = json.loads(re.search(json_pattern, chat_completion.choices[0].message.content).group())["action"]
			print("Action is ", action)
	game_log.append({
		"agent": agent,
		"action": action,
		"observation": observation.tolist(),
		"reward": env.rewards,
	})
	print("action:", "rock" if action == 0 else "paper" if action == 1 else "scissors" if action == 2 else "lizard" if action == 3 else "spock" if action == 4 else "none")
	env.step(action)
env.close()


# save the chat log for two players
with open("rps_chat_log.json", "w") as f:
	json.dump({
		"status": total_reward,
		"player1_model": player1_model,
		"player2_model": player2_model,
		"total_tokens": total_tokens,
		"game_log": game_log,
		"first_player_messages": first_player_messages,
		"second_player_messages": second_player_messages,
	}, f, indent=4)

