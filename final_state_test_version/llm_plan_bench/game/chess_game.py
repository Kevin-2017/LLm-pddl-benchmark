import chess
from openai import OpenAI
import os
import random
import re
from stockfish import Stockfish
import json
import google.generativeai as genai
import anthropic
import time

anthropic_client = anthropic.Anthropic(
    api_key = os.environ["ANTHROPIC_API_KEY"]
)

genai.configure(api_key=os.environ["GENAI_API_KEY"])
# for m in genai.list_models():
# 	print(m.name)
Gemini_model = genai.GenerativeModel("models/gemini-1.5-flash")
json_pattern = re.compile(r"(\{(.|\n)*\})")
client = OpenAI(
	api_key=os.environ["OPENAI_API_KEY"],
)
stockfish = Stockfish("/opt/homebrew/bin/stockfish")


def transform_to_uci(board, s):
    # Parse the notation
    piece_symbol = s[0]  # e.g., 'Q' for queen
    target_square = chess.parse_square(s[1:])  # e.g., 'h8' becomes 63 (the index for h8)

    # Find the UCI move
    for move in board.legal_moves:
        if move.to_square == target_square and board.piece_at(move.from_square).symbol().upper() == piece_symbol:
            return move.uci()
    return None

def get_move(board, action):
	try:
		# uci format
		move = chess.Move.from_uci(action)
	except:
		# if the move is not in uci format
		try:
			move = chess.Move.from_uci(transform_to_uci(board, action))
		except:
			try:
				move = chess.Move.from_uci(action[:4])
			except:
				return None
	return move

def format_board(board_str):
	# r n b q k b n r
	# p p p p p p p p
	# . . . . . . . .
	# . . . . . . . .
	# . . . . . . . .
	# . . . . . . . .
	# P P P P P P P P
	# R N B Q K B N R
	# to
	#   +------------------------+
	# 8 | r  n  b  q  k  b  n  r |
	# 7 | p  p  p  p  p  p  p  p |
	# 6 | .  .  .  .  .  .  .  . |
	# 5 | .  .  .  .  .  .  .  . |
	# 4 | .  .  .  .  .  .  .  . |
	# 3 | .  .  .  .  .  .  .  . |
	# 2 | P  P  P  P  P  P  P  P |
	# 1 | R  N  B  Q  K  B  N  R |
	#   +------------------------+
	# 	  a  b  c  d  e  f  g  h
	result = "   +------------------------+\n"
	rows = board_str.split("\n")
	tokens = [row.split() for row in rows]
	for i in range(8):
		result += f" {8-i} | " + "  ".join(tokens[i]) + " |\n"
	result += "   +------------------------+\n"
	result += "     a  b  c  d  e  f  g  h\n"
	return result


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


player1_model_list = [
	# "gemini-1.5-flash",
	# "gemini-1.5-flash",
	# "gemini-1.5-flash",
	# "gemini-1.5-flash",
	# "gemini-1.5-flash",
	# "gemini-1.5-flash",
	# "claude-3-5-sonnet-20241022",
	# "claude-3-5-sonnet-20241022",
	# "claude-3-5-sonnet-20241022",
	# "claude-3-5-haiku-20241022",
	# "claude-3-5-haiku-20241022",
	# "claude-3-5-haiku-20241022",
	# "claude-3-5-haiku-20241022",
	# "gpt-4o",
	"gpt-4-turbo",
]
player2_model_list = [
	# "gpt-4o",
	# "gpt-4o-mini",
	# "gpt-4-turbo",
	# "gpt-3.5-turbo",
	# "claude-3-5-sonnet-20241022",
	# "claude-3-5-haiku-20241022",
	# "gpt-4o-mini",
	# "gpt-4-turbo",
	# "gpt-3.5-turbo",
	# "gpt-4o",
	# "gpt-4o-mini",
	# "gpt-4-turbo",
	# "gpt-3.5-turbo",
	# "gpt-4o-mini"
	"gpt-3.5-turbo",
]

assert len(player1_model_list) == len(player2_model_list)

for model_index in range(len(player1_model_list)):
	for game_index in range(4):
		player1_model = player1_model_list[model_index]
		player2_model = player2_model_list[model_index]
		if game_index < 2:
			pass
		else:
			temp = player1_model
			player1_model = player2_model
			player2_model = temp

		first_player_initial_prompt = f"""
	You are playing a text game of Chess against an opponent. Chess is a two-player strategy board game played on an 8x8 board. The goal of the game is to checkmate the opponent's king. On the board, your pieces are represented by uppercase letters and the opponent's pieces are represented by lowercase letters. You are a chest master playing a text based game of chess.
		"""

		second_player_initial_prompt = f"""
	You are playing a text game of Chess against an opponent. Chess is a two-player strategy board game played on an 8x8 board. The goal of the game is to checkmate the opponent's king. On the board, your pieces are represented by lowercase letters and the opponent's pieces are represented by uppercase letters. You are a chest master playing a text based game of chess.
		"""

		def generate_action_prompt(legal_moves):
			return f"""
	Please enter your move in Universal Chess Interface (UCI) format. For example, to move a pawn from e2 to e4, you would enter \"e2e4\". You should state your reason first, and serialize the output to a json object with the key "reason" and the value as a string of your reasoning and planning process, the key "action" and the value as a UCI string representing your move. The legal moves are: \n<legal_moves>\n{" ".join(legal_moves)}\n</legal_moves>\n You must select one legal move from this list and respond with the UCI format of the move you choose. Do not generate any move outside of this list. You have to win. In your reason and action, you can only use UCI format to describe.
	"""

		def generate_reasoning_prompt(player_reasoning_action_steps):
			li = [f"Move: {step['action']}\nReason: {step['reason']}" for step in player_reasoning_action_steps[-3:]]
			steps = "\n---------------------------\n".join(li)
			return f"""
	Your previous moves and thinking are below:
	<previous_moves>
	{steps}
	</previous_moves>
	Please explain your thinking before making move. 
	Comment on your current tactics so you know your plan for the next move.
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

		first_player_reasoning_action_steps = [
			# {
			# 	"action": "e2e4",
			# 	"reason": "I am playing e4 to control the center of the board and open up lines for my queen and bishop. This move is a standard opening move in chess, known as the King's Pawn Opening.",
			# }
		]
		second_player_reasoning_action_steps = []


		first_player_store_message = first_player_messages.copy()
		second_player_store_message = second_player_messages.copy()

		board = chess.Board()
		cnt = 0
		win = None # 0 is player1, 1 is player2, 2 is Draw, 3 is player1 illegal move, 4 is player2 illegal move
		total_tokens = 0
		game_log = []
		game_state = None
		while True:
			if "ge" in player1_model or "ge" in player2_model:
				time.sleep(2)
			cnt += 1
			board_state = format_board(str(board))
			fen_board = board.fen()
			outcome = board.outcome()
			stockfish.set_fen_position(fen_board)
			stockfish.set_skill_level() # default is 20 (full strength)
			print(board)
			print("outcome: ", outcome)
			if outcome != None:
				termination = outcome.termination
				game_state = termination.name
				winner = outcome.winner
				result = outcome.result()
				if winner == True:
					print("Player 1 (white) wins!")
					win = 0
				elif winner == False:
					print("Player 2 (black) wins!")
					win = 1
				elif winner == None:
					print("Draw!")
					win = 2
				break
			turn = board.turn
			legal_moves = [move.uci() for move in board.legal_moves]
			illegal_tolerance = 10 # if the model makes an illegal move, it will try again 3 times
			if turn == True: # white
				first_player_messages = first_player_messages[:2]
				first_player_messages.append({
					"role": "user", 
					"content": generate_reasoning_prompt(first_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
				})
				first_player_store_message.append({
					"role": "user", 
					"content":generate_reasoning_prompt(first_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
				})
				content, used_token = get_chat(player1_model, first_player_messages)
				total_tokens += used_token
				try:
					action = json.loads(re.search(json_pattern, content).group())["action"]
					reason = json.loads(re.search(json_pattern, content).group())["reason"]
					print(content)
					move = get_move(board, action)
				except:
					move = None
				while illegal_tolerance > 0 and (move not in board.legal_moves or move == None):
					print("Illegal move for player 1, try again")
					illegal_tolerance -= 1
					first_player_store_message.append({
						"role": "assistant",
						"content": content
					})
					first_player_store_message.append({
						"role": "user",
						"content": "Illegal move, try again."
					})
					first_player_messages = first_player_messages[:2]
					first_player_messages.append({
						"role": "user", 
						"content": generate_reasoning_prompt(first_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
					})
					first_player_store_message.append({
						"role": "user", 
						"content":generate_reasoning_prompt(first_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
					})
					content, used_token = get_chat(player1_model, first_player_messages)
					total_tokens += used_token
					try:
						action = json.loads(re.search(json_pattern, content).group())["action"]
						reason = json.loads(re.search(json_pattern, content).group())["reason"]
						print(content)
						move = get_move(board, action)
					except:
						move = None
				first_player_store_message.append({
					"role": "assistant",
					"content": content
				})
				if move == None or move not in board.legal_moves:
					print("Invalid move for player 1")
					game_state = "player1 (white) invalid move"
					win = 3
					break
				# action = random.choice(legal_moves)
				# move = chess.Move.from_uci(action)
				# reason = "Random move"
				first_player_reasoning_action_steps.append({
					"action": action,
					"reason": reason,
				})
				best_move_by_stockfish = stockfish.get_best_move()
				top_moves = stockfish.get_top_moves()
				before_evaluation = stockfish.get_evaluation()
				if before_evaluation["type"] == "mate":
					print("Mate by stockfish")
				elif before_evaluation["type"] == "cp":
					print("Evaluation by stockfish cp is ", before_evaluation["value"])
				print("Action is ", action)
				print("Best move by stockfish is ", best_move_by_stockfish)
			elif turn == False: # black
				second_player_messages = second_player_messages[:2]
				second_player_messages.append({
					"role": "user", 
					"content": generate_reasoning_prompt(second_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
				})
				second_player_store_message.append({
					"role": "user", 
					"content": generate_reasoning_prompt(second_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
				})
				content, used_token = get_chat(player2_model, second_player_messages)
				total_tokens += used_token
				try:
					action = json.loads(re.search(json_pattern, content).group())["action"]
					reason = json.loads(re.search(json_pattern, content).group())["reason"]
					print(content)
					move = get_move(board, action)
				except:
					move = None
				while illegal_tolerance > 0 and (move not in board.legal_moves or move == None):
					print("Illegal move for player 2, try again")
					illegal_tolerance -= 1
					second_player_store_message.append({
						"role": "assistant",
						"content": content
					})
					second_player_store_message.append({
						"role": "user",
						"content": "Illegal move, try again",
					})
					second_player_messages = second_player_messages[:2]
					second_player_messages.append({
						"role": "user", 
						"content": generate_reasoning_prompt(second_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
					})
					second_player_store_message.append({
						"role": "user", 
						"content": generate_reasoning_prompt(second_player_reasoning_action_steps) + "\nPlease look at the current board state represented by asci and FEN and make your next move:\n <FEN>\nFEN: " + fen_board +  "\n</FEN>\n\n<board_state>\n\n2D board: \n" + board_state + "\n</board_state>\n\n" + generate_action_prompt(legal_moves)
					})
					content, used_token = get_chat(player2_model, second_player_messages)
					total_tokens += used_token
					try:
						action = json.loads(re.search(json_pattern, content).group())["action"]
						reason = json.loads(re.search(json_pattern, content).group())["reason"]
						print(content)
						move = get_move(board, action)
					except:
						move = None
				second_player_store_message.append({
					"role": "assistant",
					"content": content
				})
				if move == None or move not in board.legal_moves:
					print("Invalid move for player 2")
					game_state = "player2 (black) invalid move"
					win = 4
					break
				# action = random.choice(legal_moves)
				# move = chess.Move.from_uci(action)
				# reason = "Random move"
				second_player_reasoning_action_steps.append({
					"action": action,
					"reason": reason,
				})
				best_move_by_stockfish = stockfish.get_best_move()
				top_moves = stockfish.get_top_moves()
				before_evaluation = stockfish.get_evaluation()
				print("before action")
				if before_evaluation["type"] == "mate":
					print("Mate by stockfish", before_evaluation["value"])
				elif before_evaluation["type"] == "cp":
					print("Evaluation by stockfish cp is ", before_evaluation["value"])
				print("Action is ", action)
				print("Best move by stockfish is ", best_move_by_stockfish)
			game_log.append({
				"board": board.fen(),
				"agent": "white" if turn == True else "black",
				"action": action,
			})
			board.push(move)
			print("after action")
			stockfish.set_fen_position(board.fen())
			# after_evaluation = stockfish.get_evaluation()
			# if after_evaluation["type"] == "mate":
			# 	print("Mate by stockfish", after_evaluation["value"])
			# elif after_evaluation["type"] == "cp":
			# 	print("Evaluation by stockfish cp is ", after_evaluation["value"])
			# if after_evaluation["type"] == "cp" and before_evaluation["type"] == "cp":
			# 	if turn == True:
			# 		print("the value of the evaluation is ", after_evaluation["value"] - before_evaluation["value"])
			# 	else:
			# 		print("the value of the evaluation is ", before_evaluation["value"] - after_evaluation["value"])
			# elif after_evaluation["type"] == "mate" and before_evaluation["type"] == "mate":
			# 	if turn:
			# 		if after_evaluation["value"] > 0:
			# 			print(f"White is closer to a checkmate in {after_evaluation['value']} moves")
			# 		elif after_evaluation["value"] < 0:
			# 			print(f"White is further from checkmate, Black is closer to checkmate in {-after_evaluation['value']} moves")
			# 	else:
			# 		if after_evaluation["value"] > 0:
			# 			print(f"Black is further from checkmate, White is closer to checkmate in {after_evaluation['value']} moves")
			# 		elif after_evaluation["value"] < 0:
			# 			print(f"Black is closer to a checkmate in {-after_evaluation['value']} moves")

		# save the chat log for two players

		with open(f"chess_log_{game_index}_{player1_model}_{player2_model}.json", "w") as f:
			json.dump({
				"status": game_state,
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