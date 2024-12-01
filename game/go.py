from openai import OpenAI
import numpy as np
import os
import re
import json
from pettingzoo.classic import go_v5
import sys
import regex
# Regex pattern for recursive matching
json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}', regex.DOTALL)
from chat_service import get_chat
from play_service import (
	play,
	create_hook_functions,
)

board_size = 5
komi = 7.5
# generate text format board index
def generate_board_index(board_size):
	board_index = "  "
	for i in range(board_size):
		board_index += str(i) + " "
	board_index += "\n"
	for i in range(board_size):
		board_index += str(i) + " "
		for j in range(board_size):
			board_index += ". "
		board_index += str(i) + "\n"
	board_index += "  "
	for i in range(board_size):
		board_index += str(i) + " "
	return board_index
board_index = generate_board_index(board_size)

def generate_action_prompt(legal_moves):

	action_prompt = f"""

	board index map:

	{board_index}

	Now it's your move. Please enter the index of the cell where you would like to place your stone [x, y] 0 <= x,y <= {board_size-1}, you should enter two numbers between 0 and {board_size-1} based on the cell index shown above. Note that x represents rows and y represents columns. You can't put a stone where there is a stone already at that place. If there is no place you can put the stone or you want to skip your round, please enter ({board_size}, {board_size}) to pass. You should serialize the output to a json object with the key "reason" and the value string as the detailed reasoning or planning for your action, and the key "action" and the value as a tuple (length of two) where you would like to place your mark. Your output should be in this format: {{'reason': string, 'action': [x, y]}}, and you can only use json valid characters.
	"""
	return action_prompt

def observation_to_text(observation, agent):
    obs = observation['observation']
    obs = obs.astype(int)
    action_mask = observation['action_mask']

    N = obs.shape[0]

    plane_current = obs[:, :, 0]
    plane_opponent = obs[:, :, 1]

    # Determine the current player
    current_player = 'Black' if agent == "black_0" else 'White'
    if current_player == 'Black':
        our_cell = 'O'
        opponent_cell = 'X'
    elif current_player == 'White':
        our_cell = 'X'
        opponent_cell = 'O'
    
    # Build the board representation
    board = []
    our_tokens = []
    opponent_tokens = []
    for i in range(N):
        row = []
        for j in range(N):
            if plane_current[i, j] == 1:
                cell = our_cell  # Current player's stone
                our_tokens.append((i, j))
            elif plane_opponent[i, j] == 1:
                cell = opponent_cell  # Opponent's stone
                opponent_tokens.append((i, j))
            else:
                cell = '.'  # Empty cell
            row.append(cell)
        board.append(row)

    # Build legal actions
    legal_actions = np.where(action_mask == 1)[0]
    legal_moves = []
    for action in legal_actions:
        if action == N * N:
            legal_moves.append('pass')
        else:
            x = action // N
            y = action % N
            legal_moves.append(f'({x}, {y})')

    # Build the text output
    output = []
    output.append("Board State:")
    # Add column numbers
    col_numbers = '   ' + ' '.join(str(j) for j in range(N))
    output.append(col_numbers)
    for i in range(N):
        row_str = ' '.join(board[i])
        output.append(f"{i}  {row_str}  {i}")
    output.append(col_numbers)
    
    # Add token coordinates
    output.append("\nCurrent Player's Token Coordinates:")
    output.append(', '.join(str(coord) for coord in our_tokens) if our_tokens else "None")
    
    output.append("\nOpponent's Token Coordinates:")
    output.append(', '.join(str(coord) for coord in opponent_tokens) if opponent_tokens else "None")
    
    return '\n'.join(output), legal_moves
def gen_move(player_messages, player_model):
	content, used_token = get_chat(player_model, player_messages)
	try:
		parsed_json = None
		matches = json_pattern.findall(content)
		for match in matches:
			try:
				parsed_json = json.loads(match)
				print("Valid JSON Found:", parsed_json)
			except Exception as e:
				print("Invalid JSON Found:", match)
		action = parsed_json["action"]
		reason = parsed_json["reason"]
		move = action
		move = str(tuple(move))
		action = move
	except Exception as e:
		print(e)
		move = None
		action = None
		reason = None
	return move, content, used_token, action, reason

player1_model_list = [
	{
		"model": "gpt-4o-mini",
		"prompt_config": [
			{
				"name": "forced-reasoning",
				"params": {
					"interactive_times": 1,
					"prompt_messages": [
						"Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage.",
					]
				}
			}
		],
	},
]
player2_model_list = [
	{
		"model": "gpt-4o-mini",
		"prompt_config": [
			{
				"name": "forced-reasoning",
				"params": {
					"interactive_times": 1,
					"prompt_messages": [
						"Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage.",
					]
				}
			}
		],
	},
]



print(len(player1_model_list), len(player2_model_list))
for i in range(len(player1_model_list)):
	print(player1_model_list[i]["model"], "vs", player2_model_list[i]["model"])
	
assert len(player1_model_list) == len(player2_model_list)

for model_index in range(len(player1_model_list)):
	for game_index in range(2):
		player1_model = player1_model_list[model_index]
		player2_model = player2_model_list[model_index]
		player1_model_name = player1_model["model"]
		player2_model_name = player2_model["model"]
		if game_index < 1:
			pass
		else:
			temp = player1_model
			player1_model = player2_model
			player2_model = temp
			temp = player1_model_name
			player1_model_name = player2_model_name
			player2_model_name = temp

		first_player_initial_prompt = f"""
You are playing a game of Go against an opponent. Go is a board game with 2 players, black and white. The black player starts by placing a black stone at an empty board intersection. The white player follows by placing a stone of their own, aiming to either surround more territory than their opponent or capture the opponent’s stones. The game ends if both players sequentially decide to pass.
The board is a 19x19 grid, the komi is 7.5, and you are playing as 'black': 'X'. The opponent is playing as 'white': 'O'. The board is indexed as a two-dimensional array:
{board_index}
		"""
		second_player_initial_prompt = f"""
You are playing a game of Go against an opponent. Go is a board game with 2 players, black and white. The black player starts by placing a black stone at an empty board intersection. The white player follows by placing a stone of their own, aiming to either surround more territory than their opponent or capture the opponent’s stones. The game ends if both players sequentially decide to pass.
The board is a 19x19 grid, the komi is 7.5, and you are playing as 'white': 'O'. The opponent is playing as 'black': 'X'. The board is indexed as a two-dimensional array:
{board_index}
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

		first_player_reasoning_action_steps = []
		second_player_reasoning_action_steps = []

		first_player_store_message = first_player_messages.copy()
		second_player_store_message = second_player_messages.copy()


		env = go_v5.env(board_size = board_size, komi = komi, render_mode=None)
		env.reset(seed=42)
		cnt = 0
		win = None # 0 is player1, 1 is player2, 2 is Draw, 3 is player1 illegal move, 4 is player2 illegal move
		total_tokens = 0
		game_log = []
		for agent in env.agent_iter():
			hook_functions = {}
			cnt += 1
			observation, reward, termination, truncation, info = env.last()
			board_state, legal_moves = observation_to_text(observation, agent)
			rewards = env.rewards
			print(rewards)
			print(board_state)
			if win != None:
				break
			if win == None:
				if len(list(rewards.keys())) == 1 and rewards[list(rewards.keys())[0]] == 0:
					print("Draw!")
					win = 2
					break
				elif rewards["black_0"] == 1 and rewards["white_0"] == 1:
					print("Draw!")
					win = 2
					break
				elif rewards["black_0"] == 1 and rewards["white_0"] == -1:
					print("Player 1 wins!")
					win = 0
					break
				elif rewards["black_0"] == -1 and rewards["white_0"] == 1:
					print("Player 2 wins!")
					win = 1
					break
				elif rewards["black_0"] == -1 and rewards["white_0"] == 0:
					print("Player 1 illegal move!")
					win = 3
					break
				elif rewards["black_0"] == 0 and rewards["white_0"] == -1:
					print("Player 2 illegal move!")
					win = 4
					break
			illegal_tolerance = 10
			if termination or truncation:
				action = None
			else:
				if agent == 'black_0':
					# first_player
					first_player_messages = first_player_messages[:2]
					hook_functions = create_hook_functions(player1_model, first_player_reasoning_action_steps, "Your opponent has made the move, and now the board state is: \n" + board_state, generate_action_prompt(None))
					move, action, win, game_state, used_token = play(first_player_messages, first_player_store_message, player1_model_name, first_player_reasoning_action_steps, 
					None, None, legal_moves, gen_move, illegal_tolerance, True, hook_functions,1)
					total_tokens += used_token
				elif agent == 'white_0':
					# second_player
					second_player_messages = second_player_messages[:2]
					hook_functions = create_hook_functions(player2_model, second_player_reasoning_action_steps, "Your opponent has made the move, and now the board state is: \n" + board_state, generate_action_prompt(None))
					move, action, win, game_state, used_token = play(second_player_messages, second_player_store_message, player2_model_name, second_player_reasoning_action_steps,
					None, None, legal_moves, gen_move, illegal_tolerance, True, hook_functions,0)
					total_tokens += used_token
			game_log.append({
				"agent": agent,
				"action": action,
				"observation": observation["observation"].tolist(),
				"reward": env.rewards,
				"action_mask": observation["action_mask"].tolist(),
			})
			if win != None:
				break
			action = list(eval(move))
			print(f"Agent: {agent}, action: {action}")
			if action[0] != board_size or action[1] != board_size:
				action = action[0] * board_size + action[1]
			else:
				action = board_size * board_size
			try:
				env.step(action)
			except Exception as e:
				print(e)
				break
		env.close()

		player1_model_save_name = player1_model_name + "-" + "-".join([i["name"] for i in player1_model["prompt_config"]])
		player2_model_save_name = player2_model_name + "-" + "-".join([i["name"] for i in player2_model["prompt_config"]])
		player1_model_save_name = player1_model_save_name.replace("/", "_")
		player2_model_save_name = player2_model_save_name.replace("/", "_")
		print(player1_model_save_name, player2_model_save_name)

		# save the chat log for two players
		with open(f"go_{game_index}_{player1_model_save_name}_{player2_model_save_name}.json", "w") as f:
			json.dump({
				"status": {
					0: "Player 1 wins!",
					1: "Player 2 wins!",
					2: "Draw!",
					3: "Player 1 illegal move!",
					4: "Player 2 illegal move!",
				}[win],
				"winner": {
					0: "Player 1",
					1: "Player 2",
					2: "Draw",
					3: "Player 2",
					4: "Player 1",
				}[win],
				"player1_model": player1_model,
				"player2_model": player2_model,
				"total_tokens": total_tokens,
				"illegal_tolerance": illegal_tolerance,
				"number_of_requests": len(game_log)/2,
				"game_log": game_log,
				"first_player_messages": first_player_store_message,
				"second_player_messages": second_player_store_message,
			}, f, indent=4)