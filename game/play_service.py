import json
from chat_service import get_chat

def play(player_messages, player_store_message, player_model, player_reasoning_action_steps, state_description, legal_move_description, legal_moves, gen_move=None, illegal_tolerance=10,print_content=True, hook_functions=None):
    # in hook_functions, key is the function, and the value is the additional arguments
    win = None
    game_state = None
    added_tokens = 0
    for k in hook_functions:
        k(player_messages, player_store_message, player_model, **hook_functions[k])
    move, content, used_token, action, reason = gen_move(player_messages, player_model)
    added_tokens += used_token
    while illegal_tolerance > 0 and (move not in legal_moves or move == None):
        print(content)
        print("Illegal move for player", player_model, "try again")
        illegal_tolerance -= 1
        player_store_message.extend([
            {"role": "assistant", "content": content},
            {"role": "user", "content": "Illegal move, try again"}
        ])
        move, content, used_token, action, reason = gen_move(player_messages, player_model)
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

def forced_reasoning(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None):
    # user prompting the assistant to reason about the current state2
    assert len(prompt_messages) == interactive_times, "Prompt messages should be the same as the interactive times"
    for i in range(interactive_times):
        append_user_message(player_messages, player_store_message, prompt_messages[i])
        content, used_token = get_chat(player_model, player_messages)
        append_assistant_message(player_messages, player_store_message, content)

def implicit_knowledge_generation(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None):
    # user asking the assistant to generate implicit knowledge
    assert len(prompt_messages) == interactive_times, "Prompt messages should be the same as the interactive times"
    for i in range(interactive_times):
        append_user_message(player_messages, player_store_message, prompt_messages[i])
        content, used_token = get_chat(player_model, player_messages)
        append_assistant_message(player_messages, player_store_message, content)

def future_based_reasoning(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None):
    # user prompting the assistant to reason about the future
    assert len(prompt_messages) == interactive_times, "Prompt messages should be the same as the interactive times"
    for i in range(interactive_times):
        append_user_message(player_messages, player_store_message, prompt_messages[i])
        content, used_token = get_chat(player_model, player_messages)
        append_assistant_message(player_messages, player_store_message, content)

def in_context_learning_case(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None):
    # user providing some examples
    assert len(prompt_messages) == 1, "Only one prompt message is allowed"
    append_user_message(player_messages, player_store_message, prompt_messages[0])

def in_context_learning_experience(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None):
    # user providing some game tricks or strategies
    assert len(prompt_messages) == 1, "Only one prompt message is allowed"
    append_user_message(player_messages, player_store_message, prompt_messages[0])

def reasoning_history(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None, player_reasoning_action_steps=None,count=3):
    # generate reasoning prompt
    append_user_message(player_messages, player_store_message, generate_reasoning_prompt(player_reasoning_action_steps,count))

def add_state_description(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None, state_description=None):
    # state_description
    append_user_message(player_messages, player_store_message, state_description)

def action_prompt(player_messages=None, player_store_message=None, player_model=None, interactive_times=None, prompt_messages=None, action_prompt=None):
    assert action_prompt is not None
    append_user_message(player_messages, player_store_message, action_prompt)


def generate_reasoning_prompt(player_reasoning_action_steps,count):
	li = [f"Move: {step['action']}\nReason: {step['reason']}" for step in player_reasoning_action_steps[-count:]]
	steps = "\n---------------------------\n".join(li)
	return f"""
Your previous moves and thinking are below  (in the last {count} moves in the order of the oldest to the newest):
<previous_moves>
{steps}
</previous_moves>
"""

def append_user_message(player_messages, player_store_message, user_message):
    # check the role of the last message
    if player_messages[-1]["role"] == "assistant":
        player_messages.append({
            "role": "user",
            "content": user_message
        })
        player_store_message.append({
            "role": "user",
            "content": user_message
        })
    elif player_messages[-1]["role"] == "user":
        player_messages[-1]["content"] += "\n" + user_message
        player_store_message[-1]["content"] += "\n" + user_message

def append_assistant_message(player_messages, player_store_message, assistant_message):
    player_messages.append({
        "role": "assistant",
        "content": assistant_message
    })
    player_store_message.append({
        "role": "assistant",
        "content": assistant_message
    })