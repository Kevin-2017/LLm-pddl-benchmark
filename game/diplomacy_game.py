# seven LLMs playing Diplomacy
# This file is mainly for generating prompts for language models and bridge the gap between the game engine and the language model.
import random
from diplomacy import Game, Message
from diplomacy.utils.export import to_saved_game_format
from openai import OpenAI
import os
import re
from diplomacy.utils import common
from diplomacy.utils.sorted_dict import SortedDict
import json
json_pattern = re.compile(r"(\{(.|\n)*\})")
client = OpenAI(
	api_key=os.environ["OPENAI_API_KEY"],
)
total_negotiation_rounds = 3

# Function to parse the state dictionary
def parse_diplomacy_state(state):
    # Store descriptions in a list
    descriptions = []

    # Parse note
    note = state['note'] or "No notes are provided for this state."
    descriptions.append(f"Note: {note}")

    # Parse name (stage/phase)
    descriptions.append(f"Phase Name: The current game phase is '{state['name']}'.")

    # Parse units
    descriptions.append("Units: Stores the location of the units currently controlled by each player on the map:")
    for power, units in state['units'].items():
        unit_list = ', '.join(units)
        descriptions.append(f"  {power}: {unit_list}")

    # Parse retreats
    descriptions.append("Retreats: If a unit is defeated but not destroyed and it needs to retreat to a neighboring empty province. The units that need to retreat are as follows:")
    for power, retreats in state['retreats'].items():
        retreat_list = ', '.join([f"{unit} at {location}" for unit, location in retreats.items()]) if retreats else "No retreats needed."
        descriptions.append(f"  {power}: {retreat_list}")

    # Parse centers
    descriptions.append("Supply Centers: The supply centers controlled by each player are:")
    for power, centers in state['centers'].items():
        center_list = ', '.join(centers)
        descriptions.append(f"  {power}: {center_list}")

    # Parse homes
    descriptions.append("Home Centers: Each player's initial or home supply centers are:")
    for power, homes in state['homes'].items():
        home_list = ', '.join(homes)
        descriptions.append(f"  {power}: {home_list}")

    # Parse influence
    descriptions.append("Influence: The regions influenced or controlled by each player are:")
    for power, influence in state['influence'].items():
        influence_list = ', '.join(influence)
        descriptions.append(f"  {power}: {influence_list}")

    # Parse civil_disorder
    descriptions.append("Civil Disorder: Status of players under civil disorder (1 for yes, 0 for no):")
    for power, disorder in state['civil_disorder'].items():
        descriptions.append(f"  {power}: {'Civil disorder' if disorder == 1 else 'No civil disorder'}")

    # Parse builds
    descriptions.append("Builds: Each player’s allowable builds or disbands are:")
    for power, build_info in state['builds'].items():
        build_count = build_info['count']
        build_homes = ', '.join(build_info['homes']) if build_info['homes'] else "No specific build locations"
        descriptions.append(f"  {power}: {build_count} builds allowed. Homes available for builds: {build_homes}")

    # Join all descriptions into a final report
    final_report = "\n".join(descriptions)
    return final_report

index_model = {
    0: "gpt-4o-mini",
    1: "gpt-4o-mini",
    2: "gpt-4o-mini",
    3: "gpt-4o-mini",
    4: "gpt-4o-mini",
    5: "gpt-4o-mini",
    6: "gpt-4o-mini",
}

index_power_name = {
    0: "AUSTRIA",
    1: "ENGLAND",
    2: "FRANCE",
    3: "GERMANY",
    4: "ITALY",
    5: "RUSSIA",
    6: "TURKEY",
}

power_name_index = {
    "AUSTRIA": 0,
    "ENGLAND": 1,
    "FRANCE": 2,
    "GERMANY": 3,
    "ITALY": 4,
    "RUSSIA": 5,
    "TURKEY": 6,
}

player_initial_prompts = []

# initialize the player initial prompts
for i in range(7):
    player_initial_prompts.append(f"""
You are playing a game of Diplomacy against 6 opponents. Diplomacy is a 7-player turn based game, where players must use negotiation and strategy to control the most supply centers on the map. The players can move their units to different locations on the map, and can support other players' units to help them succeed. The game is played on a map of Europe, divided into territories and sea zones. The players can issue orders to their units to move, support, hold, or convoy. The game ends when one player controls 18 supply centers, or when all players agree to a draw. Taking an illegal move ends the game and the player who made the illegal move loses.
                                  
Diplomacy proceeds by seasons, beginning in the year 1901, with each year divided into two main seasons: the "Spring" and "Fall" (Autumn) moves. Each season is further divided into negotiation and movement phases, followed by "retreat" or "disband" adjustments and an end-of-the-year Winter phase of new builds or removals following the Fall adjustments.
                                  
Negotiation phase
In the negotiation phase, players discuss tactics and strategy, form alliances, and share intelligence or spread disinformation. Negotiations may be made public or kept private. Players are not bound to anything they say or promise, and no agreements are enforceable.
Communication and trust are highly important; players must forge alliances with others and observe their actions to evaluate their trustworthiness. At the same time, they must convince others of their own trustworthiness while making plans to turn against their allies when least expected. A well-timed betrayal can be just as profitable as an enduring, reliable alliance.

Movement phase
After the negotiation period, players write secret orders for each unit; these orders are revealed and executed simultaneously. A unit can move from its location to an adjacent space, support an adjacent unit to hold an area in the event of an attack, support another unit to attack a space into which it could move itself, or hold defensively. In addition, fleets may transport armies from one coast space to another when in a chain called a "convoy". Armies may only occupy land regions, and fleets occupy sea regions and the land regions that border named seas. Only one unit may occupy each region. If multiple units are ordered to move to the same region, only the unit with the most support moves there. If two or more units have the same highest support, a standoff occurs and no units ordered to that region move. A unit ordered to give support that is attacked has those orders canceled and is forced to hold, except in the case that support is being given to a unit invading the region from which the attack originated (in which case the unit that had been ordered to give support must retreat from, rather than hold, its position).
Certain spaces on the board have two coasts and here a player must specify which one they want their fleet to occupy. A fleet can only move to coasts and oceans that border the coast that it is on. For example, a fleet occupying the southern coast of Bulgaria cannot move into Romania or the Black Sea, but a fleet on the east coast could.

In the game of Diplomacy, an action space is the collection of all the legal actions that each country or unit can take in each round. The following are common types of actions in games and their common formats:

1. Move
Units can be moved from one province to a neighboring province. The format is:

A [province] - [target province] (Army moves from current position to target province)
F [province] - [target province] (Fleet moves from current position to target province)
For example:

A BER-MUN indicates that the army from Berlin moved to Munich.
F NTH-ENG indicates the movement of the fleet from the North Sea (NTH) to the English Channel (ENG).

2. Support
Units can choose to support the movement or garrison of another unit. The supported unit must be in the vicinity of the supported unit. The format is:

A [province] S A [target province] - [destination] (support army movement)
A [province] S A [target province] (supporting the garrisoning of the army)
F [province] S F [target province] - [destination] (Support fleet movement)
F [province] S F [target province] (garrisoning of supporting fleet)
For example:

A BER S A MUN indicated that the Army in Berlin supported the Army garrison in Munich.
A BER S A MUN-KIE stated that the Army of Berlin supported the Army of Munich in moving to Kiel.

3. Support to Attack
Sometimes it is necessary to support another unit in an attack on a province. The format is:

A [province] S A [target province] - [attacked province]
For example:

A BER S A WAR-SIL means that the Army of Berlin supported the Army of Warsaw in attacking Silesia.

4. Hold
Units can choose to stay in their current province and not move or support. The format is:

A [province] H (Army garrison)
F [province] H (Fleet garrison)
For example:

A BER H means the Army garrison in Berlin.

5. Convoy (Occupation)
The fleet may choose to transport an army from one coastal province to another. The operation requires the collaboration of multiple fleets, especially over long distances. The format is:

F [province] C A [origin province] - [destination province]
For example:

F ENG C A LON-BRE refers to the fleet in the English Channel transporting the Army of London to Brest (BRE).

6. Build
During the specified construction phase of the game, the country in control can choose to build new units (army or fleet) in the supply center, provided that there are supply centers available and it does not exceed its maximum number of supply centers.

For example:

Build A BER means to build a new army in Berlin.

7. Disband
Units may choose to disband, usually when defeated or strategically necessary.

The range of action space per turn
At each turn, players can choose a combination of actions to perform on the units they control, which can be moves, supports, garrisons, capture, etc.
                                  
End-of-year and supply centers
After each Fall move, newly acquired supply centers become owned by the occupying player, and each power's supply center total is recalculated; players with fewer supply centers than units on the board must disband units, while players with more supply centers than units on the board are entitled to build units in their open (unoccupied) Home centers (supply centers controlled at the start of the game). Players who have lost all of their Home centers may not build new units, while players controlling no supply centers are eliminated from the game. If a player controls 18 or more (being more than half) of the 34 supply centers at the end of a year, they are the winner. Players who remain may also agree to a draw – around half of all games will end in a draw.

You are playing as {index_power_name[i]}. The other players are playing as the following powers: {', '.join([index_power_name[j] for j in range(7) if j != i])}.
The action space is the set of possible orders that you can issue to your units. You can issue orders to move your units to different locations, support other players' units, hold your units in place, or convoy your units across sea zones.
""")

index_messages = {
    0: [],
    1: [],
    2: [],
    3: [],
    4: [],
    5: [],
    6: [],
}

for i in range(7):
    index_messages[i].append({
        "role": "user",
        "content": player_initial_prompts[i],
    })
    index_messages[i].append({
        "role": "assistant",
        "content": "Sure, let's start. "
    })


def gen_round_prompt(power_name, state, possible_orders, phase, result):
    # after the game processes the orders, it will generate a round prompt for the next player
    if phase[0] == 'W':
        return f"""
Now it's phase {phase}, and you are {power_name}. It is now your turn to play. 
The result of the action for each unit is as follows:
{result}
The current state of the game is as follows:
{parse_diplomacy_state(state)}

"""
    else:
        return f"""
Now it's phase {phase}, and you are {power_name}. It is now your turn to play. The current state of the game is as follows:
{parse_diplomacy_state(state)}
And the possible orders that you can issue are as follows:
{possible_orders}
Now it's the negotiation phase. There are {total_negotiation_rounds} rounds of negotiation. 
You can send messages to other players to discuss tactics and strategy, form alliances, share intelligence or spread disinformation. You can send a message to a specific player or to all players.
"""

def gen_message_prompt(negotiation_round, this_power_index, last_round_messages=None):
    # Negotiation phase
    # In the negotiation phase, players discuss tactics and strategy, form alliances, and share intelligence or spread disinformation. Negotiations may be made public or kept private. Players are not bound to anything they say or promise, and no agreements are enforceable.
    # format: Message(sender='FRANCE', recipient='ENGLAND', message='Hello!',phase=game.get_current_phase())
    # recipient can be 'GLOBAL' to send a message to all players
    return f"""
It is now the {negotiation_round+1} round of negotiation phase. The number of total negotiation round is {total_negotiation_rounds}, after that, you have to decide your actions.
The last negotiation round messages are as follows:
{last_round_messages if last_round_messages else "No messages from the last round."}
Please enter the message that you would like to send. You should serialize the output to a json object with the key "message" and the value as a dictionary with the following keys
- "recipients": (list(str)) the names of the recipient of the message. Recipient list: {', '.join([index_power_name[j] for j in range(7) if j != this_power_index])}, 'GLOBAL'
- "messages": (list(str)) the content of the messages that you would like to send.
The same index in the recipient list corresponds to the same index in the message list. The length of the recipients should be the same as messages. For example, if you want to send a message to ENGLAND and FRANCE, you should serialize the output as "recipients": ["ENGLAND", "FRANCE"], "messages": ["Hello, ENGLAND!", "Hello, FRANCE!"] Generate the text with standard straight double quotes (\")
"""

def gen_action_prompt(possible_orders):
    return f"""
Now you have to decide your orders. Please enter the orders that you would like to issue to your units. You should serialize the output to a json object with the key "orders" and the value as a list of orders. 
For each location, you can only issue one order. So the length of the list should be the same as the number of locations that you can issue orders.
Please tell me the reason why you choose these orders, explain your strategy or your plan in another key "reason", and the string value as your explanation, so that I can understand your decision better. The string should be able to be parsed to json str. So don't use special characters like \\n, \\t, etc.
All the possible orders that you can issue are as follows(key is the location, value is the list of possible orders at that location):
{possible_orders}
"""

def get_message_text(messages, recipient, time_start, time_end):
    message_text = ""
    for k in messages.keys():
        if time_start <= k <= time_end:
            if messages[k].recipient == recipient:
                message_text += f"{messages[k].sender}: {messages[k].message}\n"
            elif messages[k].recipient == 'GLOBAL':
                message_text += f"{messages[k].sender} to all players: {messages[k].message}\n"
    return message_text

# Creating a game
game = Game()

possible_orders = game.get_all_possible_orders()
total_tokens = 0
cnt = 0

while not game.is_game_done:
    cnt += 1

    winter = False
    
    # negotiation phase
    # no negotiation in phase winter
    if game.get_current_phase()[0] != 'W':
        last_negotiation_round_time = None
        for negotiation_round in range(total_negotiation_rounds):
            negotiation_round_start_time = common.timestamp_microseconds()

            for power_name, power in game.powers.items():
                orderable_locations = game.get_orderable_locations(power_name)
                location_orders = {loc: possible_orders[loc] for loc in orderable_locations if possible_orders[loc]}
                if negotiation_round == 0:
                    # generate a round prompt for the player
                    this_prompt = gen_round_prompt(power_name, game.get_state(), str(location_orders), game.get_current_phase(), game.result)
                    this_prompt += gen_message_prompt(negotiation_round, power_name_index[power_name] , None)
                else:
                    # get the last round messages
                    this_prompt = ""
                    messages = game.messages
                    last_round_messages = get_message_text(messages, power_name, last_negotiation_round_time, negotiation_round_start_time)
                    this_prompt += gen_message_prompt(negotiation_round, power_name_index[power_name] ,last_round_messages)
                index_messages[power_name_index[power_name]].append({
                    "role": "user",
                    "content": this_prompt,
                })
                chat_completion = client.chat.completions.create(
                    messages=index_messages[power_name_index[power_name]],
                    model=index_model[power_name_index[power_name]],
                )
                index_messages[power_name_index[power_name]].append({
                    "role": "assistant",
                    "content": chat_completion.choices[0].message.content,
                })
                print(chat_completion.choices[0].message.content)
                total_tokens += chat_completion.usage.to_dict()["total_tokens"]
                respond = json.loads(re.search(json_pattern, chat_completion.choices[0].message.content).group())["message"]
                recipients = respond["recipients"]
                messages = respond["messages"]
                for recipient, message in zip(recipients, messages):
                    game.add_message(Message(sender=power_name, recipient=recipient, message=message, phase=game.get_current_phase()))

            last_negotiation_round_time = negotiation_round_start_time
    else:
        winter = True # should gen_round_prompt to provide the information for winter phase


    # action phase
    for power_name, power in game.powers.items():
        orderable_locations = game.get_orderable_locations(power_name)
        location_orders = {loc: possible_orders[loc] for loc in orderable_locations if possible_orders[loc]}
        if winter:
            action_prompt = gen_round_prompt(power_name, game.get_state(), None, game.get_current_phase(), game.result) + gen_action_prompt(str(location_orders))
        else:
            action_prompt = gen_action_prompt(str(location_orders))
        index_messages[power_name_index[power_name]].append({
            "role": "user",
            "content": action_prompt,
        })
        chat_completion = client.chat.completions.create(
            messages=index_messages[power_name_index[power_name]],
            model=index_model[power_name_index[power_name]],
        )
        index_messages[power_name_index[power_name]].append({
            "role": "assistant",
            "content": chat_completion.choices[0].message.content,
        })
        print(chat_completion.choices[0].message.content)
        total_tokens += chat_completion.usage.to_dict()["total_tokens"]
        respond = json.loads(re.search(json_pattern, chat_completion.choices[0].message.content).group())
        power_orders = respond["orders"]
        game.set_orders(power_name, power_orders)
    game.process()
    if cnt == 4:
        break

# outcome
outcome = str(game.outcome)

# token used
print("Total tokens used: ", total_tokens)

# history
to_saved_game_format(game, output_path='game.json')

with open("diplomacy_chat_log.json", "w") as f:
    json.dump({
        "total_tokens": total_tokens,
        "outcome": outcome,
        "index_model": index_model,
        "index_power_name": index_power_name,
        "index_messages": index_messages,
    }, f, indent=4)