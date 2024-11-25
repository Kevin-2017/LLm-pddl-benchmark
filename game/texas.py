from openai import OpenAI
from pettingzoo.classic import texas_holdem_v4
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
You are playing a game of Texas Hold'em. Texas Hold'em is a poker game where each player is dealt two private cards and shares five community cards. The player with the best five-card hand wins. The game is played with a standard deck of 52 cards. The game consists of four rounds of betting: pre-flop, flop, turn, and river. The player with the best hand at the end of the game wins.
"""

second_player_initial_prompt = f"""
You are playing a game of Texas Hold'em. Texas Hold'em is a poker game where each player is dealt two private cards and shares five community cards. The player with the best five-card hand wins. The game is played with a standard deck of 52 cards. The game consists of four rounds of betting: pre-flop, flop, turn, and river. The player with the best hand at the end of the game wins.
"""

def gen_action_prompt(legal_actions):
	return f"""
Now it's your move. Please enter your action. You should serialize the output to a json object with the key "action" and the value as a string representing your action. Available actions are: {", ".join(legal_actions)}.
"""

# Function to parse card indices into human-readable format
def parse_cards(observation):
	suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
	ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
	cards = []
	
	# First 52 indices are for cards
	for i in range(4):
		for j in range(13):
			index = i * 13 + j
			if observation[index] == 1:
				cards.append(f"{ranks[j]} of {suits[i]}")
	return cards

# Function to parse raised chips information
def parse_raised_chips(observation):
	rounds = ['Round 1', 'Round 2', 'Round 3', 'Round 4']
	chips = []
	
	for i, round_name in enumerate(rounds):
		round_indices = range(52 + i * 5, 52 + (i + 1) * 5)
		chips_raised = [observation[idx] for idx in round_indices].index(1)
		chips.append(f"{round_name}: {chips_raised} chips raised")
	
	return chips

# Function to parse legal action mask
def parse_legal_actions(action_mask):
	actions = ['Call', 'Raise', 'Fold', 'Check']
	legal_actions = [actions[i] for i, legal in enumerate(action_mask) if legal == 1]
	return legal_actions if legal_actions else ["No legal actions available"]

# Main function to parse the observation and legal action mask into text
def parse_observation_to_text(observation_dict):
	observation = observation_dict['observation']
	action_mask = observation_dict['action_mask']
	
	# Parse the player's hand and community cards
	cards = parse_cards(observation)
	cards_text = "On your hand and community cards: " + ", ".join(cards) if cards else "No cards."
	
	# Parse the raised chips in each round
	chips_raised = parse_raised_chips(observation)
	chips_text = "Chips raised: " + ", ".join(chips_raised)
	
	# Parse the legal actions
	legal_actions = parse_legal_actions(action_mask)
	legal_actions_text = "Legal actions: " + ", ".join(legal_actions)
	
	# Combine everything into a text format
	game_state_text = f"{cards_text}\n{chips_text}\n{legal_actions_text}\n"
	
	return game_state_text, legal_actions

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

env = texas_holdem_v4.env(render_mode=None)
env.reset(seed=42)
cnt = 0
win = None
total_tokens = 0
player1_model = "gpt-4o-mini"
player2_model = "gpt-4o-mini"
game_log = []
for agent in env.agent_iter():
	cnt += 1
	print(agent)
	observation, reward, termination, truncation, info = env.last()
	observation["observation"] = observation["observation"].astype(int)
	rewards = env.rewards
	game_state_text, legal_actions = parse_observation_to_text(observation)
	print(parse_observation_to_text(observation)[0])
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
		"reward": env.rewards,
		"action_mask": observation["action_mask"].tolist(),
	})
	action = {"call": 0, "raise": 1, "fold": 2, "check": 3}[action]
	env.step(action)
env.close()



# save the chat log for two players
with open("texas_chat_log.json", "w") as f:
	json.dump({
		"status": win,
		"player1_model": player1_model,
		"player2_model": player2_model,
		"total_tokens": total_tokens,
		"game_log": game_log,
		"first_player_messages": first_player_messages,
		"second_player_messages": second_player_messages,
	}, f, indent=4)