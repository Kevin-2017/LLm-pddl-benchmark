import os
import re
import regex
# Regex pattern for recursive matching
json_pattern = regex.compile(r'\{(?:[^{}]|(?R))*\}', regex.DOTALL)

import json
from pettingzoo.classic import connect_four_v3
import random
import time
from chat_service import get_chat
from play_service import (
	play,
	create_hook_functions,
)

cf_strategy = """
How to play Connect 4
Connect 4 is all about lining stuff up in a row. If you already know how to win tic-tac-toe, then consider yourself ahead of the curve. But whereas tic-tac-toe is played on a tiny grid consisting of three rows and three columns, Connect 4 is played on a grid made up of six rows and seven columns—with a total of 42 possible spots. The upshot is that there are more than 4.5 trillion ways for the grid to be completed (4,531,985,219,092, to be exact). Fortunately, there are around 2 trillion ways to win as well, which makes the game not only super fun and compelling, but also mildly addictive for competitive folks.

To play, two people take turns dropping checkers into the Connect 4 slots, attempting to make a horizontal, vertical or diagonal line of four checkers of your own color. You can also use your checkers to block your opponent's attempt at four connections. But what does it take to actually hit a winning combination (while playing a focused opponent with a few tricks up their own sleeve)? Intense strategy, not unlike learning how to win Monopoly.

What are the best strategies to win Connect 4 every time?
Mastering how to win Connect 4 boils down to two options. One is playing again and again—as both the first and the second player—to learn the best strategies. The other option, a slight shortcut, is going into the game armed with the strategies discussed below. While none can guarantee a win every time, as Allis notes, “there are definitely some rules of thumb that can help.”

1. Be “player one”
The simplest Connect 4 strategy is simply going first. “Going first means you can dictate the play,” says Keith Galli, a Connect 4 expert who earned his masters in computer science at Massachusetts Institute of Technology and has devoted considerable time to teaching a large audience on YouTube his favorite winning Connect 4 strategies.

Because players take alternate turns, and forfeiting a turn is not an option, order matters. In fact, as Allis proved in his thesis, player one is guaranteed a win—provided they play a perfect game. Playing a “perfect” game refers to always dropping your playing piece into a spot that not only creates an advantage for you but also eliminates (or zeros out) whatever advantage the other player may have gained via their last move. It's a tall order, our experts agree. And in the average game involving two average players, it's just as likely the second player wins. But using strategy increases the chances of playing a perfect game.

2. Start in the middle of the bottom row
If you're player one, the perfect first play is to place your first piece in the middle spot of the bottom row (in Connect 4 parlance, that's known as “D1”). Indeed, it is the only surefire, guaranteed way to win—provided that you continue to play a perfect game. The number of spots on a Connect 4 grid is finite (i.e., 42), and the number of ways to win is finite as well (albeit large). A checker in D1 allows you to make a Connect 4 in all possible directions, which makes it the best possible first move.

In fact, for player one, starting at D1 is critical. If the second player can manage to play a perfect game, then the first player cannot win unless they began the game by taking D1, Allis says.

3. Focus on the middle column
Generally speaking, either player can improve their odds of winning by loading up the middle column with their own pieces, says Galli. With seven columns and six rows within which to create a line of four, all horizontal lines of four will end up having a playing piece located in the middle column. Since horizontal is one of the three directions in which a line of four may be created, the laws of probability make it difficult to envision winning without controlling the middle. Exceptions do apply, however.

4. Make a strategic second move
If you're player one and have played the perfect first move at D1, then your opponent's first move will likely be to place a piece directly above—in a reasonable attempt to block you vertically up the middle, says Allis. If that is the case, your instinct as player one might be to place your second piece right above that one. Instead, Galli suggests a more strategic alternative, which is placing your next piece in the farthest left-hand or farthest right-hand column. “As the grid builds up,” Galli explains, “you'll be giving yourself an opportunity to create a diagonal four-in-a-row.”

5. React appropriately as player two
As noted above, if player one places their first piece at D1, player two will often place theirs directly above D1. If you're player two, however, you're better off resisting the impulse to do so and instead, making your first move at one of the two spots directly next to D1. According to Allis, this strategy stands a good chance of enticing player one to place their own piece directly above D1 (a reasonable attempt to gain control of the middle column). In that case, your response should be to place your second piece directly above that. Doing so may not result in a win, notes Allis, but it levels the playing field enough that a tie will be possible.

6. Play the odd rows
Also known as the parity strategy, “playing the odd rows” is when the first player aims to secure three pieces in a line so that an empty fourth spot is in one of the odd-numbered rows (the first, third or fifth from the bottom). That line can be horizontal, vertical or diagonal. Galli says that this is not only his favorite how-to-win Connect 4 strategy but also the one that is talked about least on social media—thus making it all the more powerful for those in the know.

Given the finite number of positions on the grid, and assuming perfect play, this strategy should have the effect of leaving one of the columns “either free or nearly free” by the 37th move of the game, Galli notes. This will have the effect of forcing the second player to place their piece in the last spot before the first player's winning spot.

7. If you're player two, play the even rows
The parity strategy discussed above works for the second player as well, except that the second player must set up their three-in-line in an even row, Galli points out. Of course, while setting things up as such, “you still have to make sure you're not ignoring some other risk.” In other words, even as you play offensively, it's still important to play defensively, eliminating any advantage gained by the first player in an earlier move. This, of course, applies to the odd-parity play as well.

8. Fork your threats
In Connect 4 parlance, whenever three playing pieces are lined up adjacently, it's called a “major threat,” even if it might take several moves to complete the line-of-four (due to the vertical nature of the columns). An “adjacent threat pair” refers to two major threats that are connected by at least one playing piece. And forming an adjacent threat pair—also known as “forking your threats”—is one key to a quicker win than you may achieve using the parity strategy, says Galli.

Galli's preferred fork is known by many as the “figure 7 trap” because the player making use of it creates a seven-shaped formation of their playing pieces. This involves three pieces in a diagonal line, where the top piece is also part of a three-piece horizontal line. If executed in the center of the board, in any orientation, this offers multiple opportunities for a win, and that can be difficult, if not impossible, for the other player to block. As you play more, you're likely to pick up on other forks as they arise organically, Allis notes.

9. Observe carefully and think ahead
As you've probably gleaned by now, watching the grid carefully as it builds up is critical to winning Connect 4 because four-in-a-row can occur in any direction, and the threats build up quickly. As discussed above, playing a “perfect” game requires defending against all threats made by your opponent. These include major threats, as well as minor threats. Minor threats are two pieces in a row when there is a third piece that would be in line if it weren't for an empty spot in between. Thinking ahead, you would want to close up that empty spot immediately.

Likewise, if your opponent has set up two pieces in a row with a space on either side, thinking ahead would tell you to block them on one side—otherwise, your opponent will be assured a win by placing a piece on either side, creating a line of three. In that case, on your next turn, you'll be able to defend only against one side, leading to your loss.

10. Assume your opponent knows as much as you do
Mastering a Connect 4 win requires the assumption that your opponent knows all the strategies you know (if not more). Before placing your next piece, always consider what your opponent would do in response, and you'll want to assume that they're playing optimally. Doing so can help avoid making mistakes that might have you face-palming.

What is the fastest way to win Connect 4?
According to Galli, there's no faster way to win Connect 4 than to place three tiles next to one another in the bottom row. As noted above, this leaves your opponent with the ability to block only one of the two possible four-in-a-rows that you've set up, leading to their loss within two moves. Losing in the bottom row is a potential rookie mistake, but it can happen to anyone, no matter their expertise. As Galli points out, anyone can be caught off-guard if they're not giving their full attention to the game.

Is it possible for no one to win Connect 4?
Just as it is possible for no player to win tic-tac-toe, it is also possible that no one wins a game of Connect 4. This situation is known as a “draw.” Not only did Allis prove the possibility of a draw in his thesis, but if you play Connect 4 enough, you'll likely prove it for yourself in relatively short order.

Before you declare a draw though, you'll want to be sure to study the grid carefully to make sure a line of four in a row hasn't been created unintentionally by either player. When Connect 4 players are playing strategically, each may be so focused on creating the line they've strategized, it's possible to miss a line that has been created inadvertently.

Common mistakes to avoid when playing Connect 4
As noted above, the fastest route to losing Connect 4 is allowing your opponent to place three pieces in a horizontal row. However, another common mistake is to forget to play defensively. This often happens when you focus too much on placing your pieces into whatever configuration you may have pre-envisioned. “Every time you drop a piece, make sure you're not offering your opponent an opportunity to win before your next turn,” Galli suggests.

He also suggests avoiding placing pieces into the perimeter columns too early in the game. Finally, an easy mistake to make is aiming for a particular space without consciously registering that there's an empty space beneath it. In many cases, that's the penultimate move before the other player can declare victory.

Is there an algorithm for Connect 4 if you're playing online?
It took Allis nine months to do so in 1988, but these days, it would probably take a skilled programmer less than a day to create an algorithm capable of playing a perfect game of Connect 4, he says. If you could leverage such a program, then theoretically, you could stop any opponent in their tracks by playing every move perfectly—as long as you're player one. In every single game that's played perfectly from start to finish, the first player will always win, Allis says. It's simply mathematical fact.

By the same token, if you play Connect 4 online against a computer, then you will likely be doing so against a sophisticated algorithm. Even if it's not sophisticated enough to anticipate every perfect move, it's very likely that the computer will emerge the victor. Of course, you still have a chance if you happen to be the first player. Read on to find out how to play Connections, the latest New York Times brain game.
"""

# json_pattern = re.compile(r'\{(?:[^{}]|(?R))*\}', re.DOTALL)

def generate_action_prompt(legal_moves):
	action_prompt = f"""
Now it's your move. Please enter the index of the column where you would like to place your token (0-6 from left to right), except the illegal position. You should serialize the output to a json object with the key "reason" and the value str as the detailed reasoning or planning for your action, and the key "action" and the value as the index of the column where you would like to place your token. The legal moves are: \n<legal_moves>\n{" ".join([str(move) for move in legal_moves])}\n</legal_moves>\n You must select one legal move from this list. You have to win.  Your output should be {{'reason': string, 'action': index}}, and you can only use json valid characters.
"""
	return action_prompt

def generate_reasoning_prompt(player_reasoning_action_steps):
	li = [f"Move: {step['action']}\nReason: {step['reason']}" for step in player_reasoning_action_steps[-3:]]
	steps = "\n---------------------------\n".join(li)
	return f"""
Your previous moves and thinking are below  (in the last 3 moves in the order of the oldest to the newest):
<previous_moves>
{steps}
</previous_moves>
"""

def parse_observation(observation_dict, agent):
	"""
	This function takes the observation dictionary from the PettingZoo environment
	and returns a text description of the current game state and legal moves.
	"""
	# Extract observation and action mask
	observation = observation_dict['observation']
	action_mask = observation_dict['action_mask']
	
	player_0_grid = observation[:, :, 0]
	player_1_grid = observation[:, :, 1]

	if agent == "player_0":
		player_mark = "X "
		opponent_mark = "O "
	elif agent == "player_1":
		player_mark = "O "
		opponent_mark = "X "

	X_places = []
	O_places = []

	# Create text description for the current game state
	grid_description = "Current game state:\n"
	for row in range(6):
		row_description = "r" + str(row) + " "
		for col in range(7):
			if player_0_grid[row, col] == 1:
				row_description += player_mark  # Represent player 0's token with 'X'
				if agent == "player_0":
					X_places.append((row, col))
				else:
					O_places.append((row, col))
			elif player_1_grid[row, col] == 1:
				row_description += opponent_mark  # Represent player 1's token with 'O'
				if agent == "player_0":
					O_places.append((row, col))
				else:
					X_places.append((row, col))
			else:
				row_description += "- "  # Empty cell with '-'
		grid_description += row_description.strip() + "\n"
	grid_description += "   "+" ".join(["c0", "c1", "c2", "c3", "c4", "c5", "c6"]) + "\n"

	grid_description += f"""
r0 means row 0, r1 means row 1, and so on.
c0 means column 0, c1 means column 1, and so on.

Token places(row index, column index): 
X tokens are at places: {X_places}
O tokens are at places: {O_places}
"""

	# Create text description for legal moves
	legal_moves_description = "Legal actions (columns where you can drop a token):\n"
	legal_moves = [i for i, is_legal in enumerate(action_mask) if is_legal == 1]
	legal_moves_description += ", ".join([str(col) for col in legal_moves])

	# Combine the two descriptions
	full_description = f"{grid_description}\n{legal_moves_description}"
	
	return grid_description + "\n", legal_moves_description + "\n", legal_moves

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
	except Exception as e:
		print(e)
		move = None
		action = None
		reason = None
	return move, content, used_token, action, reason

player1_model_list = [
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
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
	}
]
player2_model_list = [
	{
		"model": "gpt-4o",
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
	{
		"model": "gpt-4-turbo",
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
	{
		"model": "gpt-3.5-turbo",
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
	{
		"model": "claude-3-5-sonnet-20241022",
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
	{
		"model": "claude-3-5-haiku-20241022",
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
	{
		"model": "ollama-qwen2.5:72b",
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
	{
		"model": "ollama-llama3.1:70b",
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
	{
		"model": "ollama-llama3:70b-instruct",
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
	{
		"model": "ollama-llama3.2:3b",
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
	{
		"model": "ollama-mistral:latest",
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
	{
		"model": "o1-preview-2024-09-12",
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
	{
		"model": "o1-mini-2024-09-12",
		"prompt_config": [
		],
	},
]

print(len(player1_model_list))
print(len(player2_model_list))
for i in range(len(player1_model_list)):
	print(player1_model_list[i]["model"], "vs", player2_model_list[i]["model"])
	
assert len(player1_model_list) == len(player2_model_list)

for model_index in range(len(player1_model_list)):
	for game_index in range(10):
		player1_model = player1_model_list[model_index]
		player2_model = player2_model_list[model_index]
		player1_model_name = player1_model["model"]
		player2_model_name = player2_model["model"]
		if game_index < 5:
			pass
		else:
			temp = player1_model
			player1_model = player2_model
			player2_model = temp
			temp = player1_model_name
			player1_model_name = player2_model_name
			player2_model_name = temp

		first_player_initial_prompt = """
		You are playing a game of Connect Four against an opponent. Connect Four is a 2-player turn based game, where players must connect four of their tokens vertically, horizontally or diagonally. The players drop their respective token in a column of a standing grid, where each token will fall until it reaches the bottom of the column or reaches an existing token. Players cannot place a token in a full column, and the game ends when either a player has made a sequence of 4 tokens, or when all 7 columns have been filled. Taking an illegal move ends the game and the player who made the illegal move loses.
		The board is a 6x7 grid, and you are playing as 'X'. The opponent is playing as 'O'. 
		The action space is the set of integers from 0 to 6 (inclusive), from left to right, where the action represents which column a token should be dropped in.
		"""

		second_player_initial_prompt = """
		You are playing a game of Connect Four against an opponent. Connect Four is a 2-player turn based game, where players must connect four of their tokens vertically, horizontally or diagonally. The players drop their respective token in a column of a standing grid, where each token will fall until it reaches the bottom of the column or reaches an existing token. Players cannot place a token in a full column, and the game ends when either a player has made a sequence of 4 tokens, or when all 7 columns have been filled. Taking an illegal move ends the game and the player who made the illegal move loses.
		The board is a 6x7 grid, and you are playing as 'O'. The opponent is playing as 'X'. 
		The action space is the set of integers from 0 to 6 (inclusive), from left to right, where the action represents which column a token should be dropped in.
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

		env = connect_four_v3.env(render_mode="rgb_array")
		env.reset(seed=42)
		win = None # 0 is player1, 1 is player2, 2 is Draw, 3 is player1 illegal move, 4 is player2 illegal move
		total_tokens = 0
		
		game_log = []

		# kg_messages = first_player_store_message.copy()
		# append_user_message(kg_messages, [], "Tell me about the general skills, the general experience of playing Connect Four, and then you need to use those skills and experience against your opponent")
		# content, used_token = get_chat(player1_model, first_player_messages)
		# append_assistant_message(kg_messages, [], content)
		# kg_messages = kg_messages[-2:]

		for agent in env.agent_iter():
			hook_functions = {}
			observation, reward, termination, truncation, info = env.last()
			grid_description, legal_moves_description, legal_moves = parse_observation(observation, agent)
			print(grid_description)
			rewards = env.rewards
			print(rewards)
			if win != None:
				break
			if win == None:
				if len(list(rewards.keys())) == 1 and rewards[list(rewards.keys())[0]] == 0:
					print("Draw!")
					win = 2
					break
				elif rewards["player_0"] == 1 and rewards["player_1"] == 1:
					print("Draw!")
					win = 2
					break
				elif rewards["player_0"] == 1 and rewards["player_1"] == -1:
					print("Player 1 wins!")
					win = 0
					break
				elif rewards["player_0"] == -1 and rewards["player_1"] == 1:
					print("Player 2 wins!")
					win = 1
					break
				elif rewards["player_0"] == -1 and rewards["player_1"] == 0:
					print("Player 1 illegal move!")
					win = 3
					break
				elif rewards["player_0"] == 0 and rewards["player_1"] == -1:
					print("Player 2 illegal move!")
					win = 4
					break
			illegal_tolerance = 10
			if termination or truncation:
				action = None
			else:
				if agent == 'player_0':
					first_player_messages = first_player_messages[:2]
					hook_functions = create_hook_functions(player1_model, first_player_reasoning_action_steps, "Your opponent has made the move, and now the state is: \n" + grid_description + "\n", generate_action_prompt(legal_moves))
					move, action, win, game_state, added_tokens = play(first_player_messages, first_player_store_message, player1_model_name, first_player_reasoning_action_steps, grid_description, legal_moves_description, legal_moves, gen_move, illegal_tolerance,True, hook_functions,0)
					total_tokens += added_tokens
				elif agent == 'player_1':
					second_player_messages = second_player_messages[:2]
					hook_functions = create_hook_functions(player2_model, second_player_reasoning_action_steps, "Your opponent has made the move, and now the state is: \n" + grid_description + "\n", generate_action_prompt(legal_moves))
					move, action, win, game_state, added_tokens = play(second_player_messages, second_player_store_message, player2_model_name, second_player_reasoning_action_steps, grid_description, legal_moves_description, legal_moves, gen_move, illegal_tolerance,True, hook_functions,1)
					total_tokens += added_tokens
			game_log.append({
				"agent": agent,
				"action": action,
				"observation": observation["observation"].tolist(),
				"reward": env.rewards,
				"action_mask": observation["action_mask"].tolist(),
			})
			try:
				env.step(move)
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
		with open(f"cf_{game_index}_{player1_model_save_name}_{player2_model_save_name}.json", "w") as f:
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