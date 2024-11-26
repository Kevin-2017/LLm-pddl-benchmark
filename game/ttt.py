from pettingzoo.classic import tictactoe_v3
from openai import OpenAI
import os
import re
import json
json_pattern = re.compile(r"(\{(.|\n)*\})")
client = OpenAI(
	api_key=os.environ["OPENAI_API_KEY"],
)

first_player_initial_prompt = """
You are playing a game of Tic-Tac-Toe against an opponent. Tic-tac-toe is a simple turn based strategy game where 2 players, X and O, take turns marking spaces on a 3 x 3 grid. The first player to place 3 of their marks in a horizontal, vertical, or diagonal line is the winner. Taking an illegal move ends the game and the player who made the illegal move loses.
The board is a 3x3 grid, and you are playing as 'X'. The opponent is playing as 'O'. The board is indexed as follows:
Action Space: 
Each action from 0 to 8 represents placing either an X or O in the corresponding cell. The cells are indexed as follows:

0 | 3 | 6
_________

1 | 4 | 7
_________

2 | 5 | 8
"""

second_player_initial_prompt = """
You are playing a game of Tic-Tac-Toe against an opponent. Tic-tac-toe is a simple turn based strategy game where 2 players, X and O, take turns marking spaces on a 3 x 3 grid. The first player to place 3 of their marks in a horizontal, vertical, or diagonal line is the winner.
The board is a 3x3 grid, and you are playing as 'O'. The opponent is playing as 'X'. The board is indexed as follows:
Action Space: 
Each action from 0 to 8 represents placing either an X or O in the corresponding cell. The cells are indexed as follows:

0 | 3 | 6
_________

1 | 4 | 7
_________

2 | 5 | 8
"""

action_prompt = """

0 | 3 | 6
_________

1 | 4 | 7
_________

2 | 5 | 8

Now it's your move. Please enter the index of the cell where you would like to place your mark (0-8), you should enter a number between 0 and 8 based on the cell index shown above. You should serialize the output to a json object with the key "action" and the value as the index of the cell where you would like to place your mark.
"""

def parse_observation(observation_dict, agent):
	# Extract the observation planes and the action mask from the observation dictionary
	observation = observation_dict['observation']  # 3x3x2 array
	action_mask = observation_dict['action_mask']  # Legal action mask

	# Initialize variables to store the board and the agent's mark
	board = [['' for _ in range(3)] for _ in range(3)]
	if agent == 'player_1':
		player_mark = 'X'
		opponent_mark = 'O'
	else:
		player_mark = 'O'
		opponent_mark = 'X'

	# Parse the board from the observation
	for row in range(3):
		for col in range(3):
			if observation[row][col][0] == 1:
				board[row][col] = player_mark
			elif observation[row][col][1] == 1:
				board[row][col] = opponent_mark
			else:
				board[row][col] = ' '

	# Convert the board into a text description
	board_description = "\n".join(
		[f"{board[0][0]} | {board[1][0]} | {board[2][0]}\n---------\n"
		 f"{board[0][1]} | {board[1][1]} | {board[2][1]}\n---------\n"
		 f"{board[0][2]} | {board[1][2]} | {board[2][2]}"]
	)

	# Convert the action mask into text description of legal actions
	legal_moves = [i for i, is_legal in enumerate(action_mask) if is_legal == 1]
	legal_moves_description = f"Legal moves: {', '.join(map(str, legal_moves))}" if legal_moves else "No legal moves available."

	# Create the final description
	description = f"Current player: {agent} ({player_mark})\n" \
				  f"Opponent: {'player_2' if agent == 'player_1' else 'player_1'} ({opponent_mark})\n" \
				  f"Board state:\n{board_description}\n" \
				  f"{legal_moves_description}"
	
	return f"Board state:\n{board_description}\n", f"{legal_moves_description}\n"

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

env = tictactoe_v3.env(render_mode=None)
env.reset(seed=42)
cnt = 0
win = None # 0 is player1, 1 is player2, 2 is Draw, 3 is player1 illegal move, 4 is player2 illegal move
total_tokens = 0
player1_model = "gpt-4o-mini"
player2_model = "gpt-4o"
game_log = []
for agent in env.agent_iter():
	cnt += 1
	observation, reward, termination, truncation, info = env.last()
	board_state, legal_moves = parse_observation(observation, agent)
	print(board_state)
	rewards = env.rewards
	print(rewards)
	if win == None:
		if len(list(rewards.keys())) == 1 and rewards[list(rewards.keys())[0]] == 0:
			print("Draw!")
			win = 2
		elif rewards["player_1"] == 1 and rewards["player_2"] == 1:
			print("Draw!")
			win = 2
		elif rewards["player_1"] == 1 and rewards["player_2"] == -1:
			print("Player 1 wins!")
			win = 0
		elif rewards["player_1"] == -1 and rewards["player_2"] == 1:
			print("Player 2 wins!")
			win = 1
		elif rewards["player_1"] == -1 and rewards["player_2"] == 0:
			print("Player 1 illegal move!")
			win = 3
		elif rewards["player_1"] == 0 and rewards["player_2"] == -1:
			print("Player 2 illegal move!")
			win = 4
	if termination or truncation:
		action = None
	else:
		if agent == 'player_1':
			# first_player
			first_player_messages.append({
				"role": "user", 
				"content": "Your opponent has made the move, and now the board state is: \n" + board_state + legal_moves + action_prompt
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
		elif agent == 'player_2':
			# second_player
			second_player_messages.append({
				"role": "user", 
				"content": "Your opponent has made the move, and now the board state is: \n" + board_state + legal_moves + action_prompt
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
	env.step(action)
env.close()

# save the chat log for two players
with open("ttt_chat_log.json", "w") as f:
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