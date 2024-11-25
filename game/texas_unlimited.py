from openai import OpenAI
from pettingzoo.classic import texas_holdem_no_limit_v6
import matplotlib.pyplot as plt
import os
import re
import json
import sys
json_pattern = re.compile(r"(\{(.|\n)*\})")
client = OpenAI(
	api_key=os.environ["OPENAI_API_KEY"],
)


first_player_initial_prompt = f"""
You are playing a game of Texas Hold'em with no limit. Texas Hold'em is a poker game where each player is dealt two private cards and shares five community cards. The player with the best five-card hand wins. The game is played with a standard deck of 52 cards. The game consists of four rounds of betting: pre-flop, flop, turn, and river. The player with the best hand at the end of the game wins. You are player 0.
"""

second_player_initial_prompt = f"""
You are playing a game of Texas Hold'em with no limit. Texas Hold'em is a poker game where each player is dealt two private cards and shares five community cards. The player with the best five-card hand wins. The game is played with a standard deck of 52 cards. The game consists of four rounds of betting: pre-flop, flop, turn, and river. The player with the best hand at the end of the game wins. You are player 1.
"""

def gen_action_prompt(legal_actions):
	return f"""
Now it's your move. Please enter your action. You should serialize the output to a json object with the key "action" and the value as a string representing your action. Available actions are: {", ".join(legal_actions)}. Check means Check and Call.
"""

def parse_observation_to_text(observation_dict, agent_name):
	"""
	Parse observation and legal actions mask into a text format for better understanding.
	
	:param observation_dict: Dictionary containing 'observation' and 'action_mask'.
	:param agent_name: Name of the current agent ('player_0' or 'player_1').
	:return: String with human-readable description of the observation and legal actions.
	"""
	obs = observation_dict['observation']
	action_mask = observation_dict['action_mask']

	# Card indices by suit
	suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
	values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
	
	# Cards held by the current player
	hand = []
	for i, suit in enumerate(suits):
		for j in range(13):
			card_index = i * 13 + j
			if obs[card_index] == 1:
				hand.append(f"{values[j]} of {suit}")
	
	# Chip counts
	player_0_chips = obs[52]
	player_1_chips = obs[53]

	# Parse legal actions
	legal_actions_text = []
	action_names = ["Fold", "Check", "Raise Half Pot", "Raise Full Pot", "All In"]
	for i, legal in enumerate(action_mask):
		if legal == 1:
			legal_actions_text.append(action_names[i])
	
	# Generate a text description
	description = f"Player 0 Chips: {player_0_chips}, Player 1 Chips: {player_1_chips}\n"
	description += f"Your Hand and Community Cards: {', '.join(hand) if hand else 'None'}\n"
	# description += f"Community Cards: {', '.join(community_cards) if community_cards else 'None'}\n"
	description += f"Legal Actions: {', '.join(legal_actions_text) if legal_actions_text else 'None'}\n"

	return description, legal_actions_text


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


env = texas_holdem_no_limit_v6.env(render_mode="human")
env.reset(seed=4)
cnt = 0
win = None
total_tokens = 0
player1_model = "gpt-4o"
player2_model = "gpt-4o-mini"
game_log = []
for agent in env.agent_iter():
	cnt += 1
	print(agent)
	observation, reward, termination, truncation, info = env.last()
	observation["observation"] = observation["observation"].astype(int)
	rewards = env.rewards
	print(rewards)
	game_state_text, legal_actions = parse_observation_to_text(observation, agent)
	print(game_state_text)
	if win == None:
		if len(list(rewards.keys())) == 1 and rewards[list(rewards.keys())[0]] == 0:
			print("Draw!")
			win = "Draw"
			break
		elif rewards["player_0"] != 0 or rewards["player_1"] != 0:
			win = rewards
			break
	if termination or truncation:
		action = None
	else:
		if agent == 'player_0':
			# first_player
			first_player_messages.append({
				"role": "user", 
				"content": "Now it's your turn, the game status is: \n" + game_state_text + gen_action_prompt(legal_actions)
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
		elif agent == 'player_1':
			# second_player
			second_player_messages.append({
				"role": "user", 
				"content": "Now it's your turn, the game status is: \n" + game_state_text + gen_action_prompt(legal_actions)
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
	action = action.lower()
	if action != None:
		print("Action is", action)
	game_log.append({
		"agent": agent,
		"action": action,
		"observation": observation["observation"].tolist(),
		"reward": {k: int(env.rewards[k]) for k in env.rewards.keys()},
		"action_mask": observation["action_mask"].tolist(),
	})
	# ["Fold", "Check & Call", "Raise Half Pot", "Raise Full Pot", "All In"]
	action = {"fold": 0, "check": 1, "raise half pot": 2, "raise full pot": 3, "all in": 4}[action]
	env.step(action)
env.close()

# save the chat log for two players
with open("texas_unlimited_chat_log.json", "w") as f:
	json.dump({
		"status": {k: int(win[k]) for k in win.keys()},
		"player1_model": player1_model,
		"player2_model": player2_model,
		"total_tokens": total_tokens,
		"game_log": game_log,
		"first_player_messages": first_player_messages,
		"second_player_messages": second_player_messages,
	}, f, indent=4)
