from openai import OpenAI
import os
import re
import json
from pettingzoo.classic import go_v5
import sys
json_pattern = re.compile(r"(\{(.|\n)*\})")
client = OpenAI(
	api_key=os.environ["OPENAI_API_KEY"],
)

board_size = 6
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

action_prompt = f"""

board index map:

{board_index}

Now it's your move. Please enter the index of the cell where you would like to place your stone (x, y) 0 <= x,y <= {board_size-1}, you should enter two numbers between 0 and {board_size-1} based on the cell index shown above. You can't put a stone where there is a stone already at that place. If there is no place you can put the stone or you want to skip your round, please enter ({board_size}, {board_size}) to pass. You should serialize the output to a json object with the key "action" and the value as a tuple (length of two) where you would like to place your mark.
"""

def observation_to_text(observation, agent):
	import numpy as np

	obs = observation['observation']
	obs = obs.astype(int)
	action_mask = observation['action_mask']

	N = obs.shape[0]

	plane_current = obs[:, :, 0]
	plane_opponent = obs[:, :, 1]

	# Determine current player
	current_player = 'Black' if agent == "black_0" else 'White'
	if current_player == 'Black':
		our_cell = 'O'
		opponent_cell = 'X'
	elif current_player == 'White':
		our_cell = 'X'
		opponent_cell = 'O'
	# Build board representation
	board = []
	for i in range(N):
		row = []
		for j in range(N):
			if plane_current[i, j] == 1:
				cell = our_cell  # Current player's stone
			elif plane_opponent[i, j] == 1:
				cell = opponent_cell  # Opponent's stone
			else:
				cell = '.'  # Empty intersection
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
	# output.append(f"Current player: {current_player}\n")
	output.append("Board state:")
	# Add column numbers
	col_numbers = '   ' + ' '.join(str(j) for j in range(N))
	output.append(col_numbers)
	for i in range(N):
		row_str = ' '.join(board[i])
		output.append(f"{i}  {row_str}  {i}")
	output.append(col_numbers)
	# output.append("\nLegal moves:")
	# output.append(', '.join(legal_moves))

	return '\n'.join(output)

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


env = go_v5.env(board_size = board_size, komi = komi, render_mode=None)
env.reset(seed=42)
cnt = 0
win = None # 0 is player1, 1 is player2, 2 is Draw, 3 is player1 illegal move, 4 is player2 illegal move
total_tokens = 0
player1_model = "gpt-4o"
player2_model = "gpt-4o"
game_log = []
for agent in env.agent_iter():
	cnt += 1
	observation, reward, termination, truncation, info = env.last()
	board_state = observation_to_text(observation, agent)
	rewards = env.rewards
	print(rewards)
	print(board_state)
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
	
	if termination or truncation:
		action = None
	else:
		if agent == 'black_0':
			# first_player
			first_player_messages.append({
				"role": "user", 
				"content": "Your opponent has made the move, and now the board state is: \n" + board_state + action_prompt
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
			print("Action is ", action)
		elif agent == 'white_0':
			# second_player
			second_player_messages.append({
				"role": "user", 
				"content": "Your opponent has made the move, and now the board state is: \n" + board_state + action_prompt
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
			print("Action is ", action)
	game_log.append({
		"agent": agent,
		"action": action,
		"observation": observation["observation"].tolist(),
		"reward": env.rewards,
		"action_mask": observation["action_mask"].tolist(),
	})
	print(f"Agent: {agent}, action: {action}")
	if action[0] != board_size or action[1] != board_size:
		action = action[0] * board_size + action[1]
	else:
		action = board_size * board_size
	env.step(action)
	if cnt == 40:
		win=0
		print("early 40 termination")
		break
env.close()


# save the chat log for two players
with open("go_chat_log.json", "w") as f:
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
		"game_log": game_log,
		"first_player_messages": first_player_messages,
		"second_player_messages": second_player_messages,
	}, f, indent=4)