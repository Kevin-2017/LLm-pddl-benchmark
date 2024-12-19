import json

def play(player_messages, player_store_message, player_model, player_reasoning_action_steps, state_description, legal_move_description, legal_moves, gen_move=None, illegal_tolerance=10,print_content=True):
    # No pre-move discussion
    win = None
    game_state = None
    added_tokens = 0
    move, content, used_token, action, reason = gen_move(player_messages, player_store_message, player_model, player_reasoning_action_steps, state_description, legal_move_description, legal_moves, True)
    added_tokens += used_token
    while illegal_tolerance > 0 and (move not in legal_moves or move == None):
        print(content)
        print("Illegal move for player", player_model, "try again")
        illegal_tolerance -= 1
        player_store_message.extend([
            {"role": "assistant", "content": content},
            {"role": "user", "content": "Illegal move, try again"}
        ])
        move, content, used_token, action, reason = gen_move(player_messages, player_store_message, player_model, player_reasoning_action_steps, state_description, legal_move_description, legal_moves, True)
        added_tokens += used_token
    if print_content:
        print(content)
    player_store_message.append({
        "role": "assistant",
        "content": content
    })
    if move not in legal_moves or move == None:
        print("Player", player_model, "exceeded illegal move tolerance")
        win = 3
        game_state = "Player " + player_model + " illegal move!"
    else:
        player_reasoning_action_steps.append({
            "action": action,
            "reason": reason
        })
    return move, action, win, game_state, added_tokens

