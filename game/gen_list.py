import itertools
import json

models = [
    {
        "model": "gpt-4o",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "gpt-4o-mini",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "gpt-4-turbo",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "gpt-3.5-turbo",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "claude-3-5-sonnet-20241022",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "claude-3-5-haiku-20241022",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "ollama-qwen2.5:72b",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "ollama-llama3.1:70b",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "ollama-llama3:70b-instruct",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "ollama-llama3.2:3b",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    },
    {
        "model": "ollama-mistral:latest",
        "prompt_config": [
            {
                "name": "forced-reasoning",
                "params": {
                    "interactive_times": 1,
                    "prompt_messages": [
                        "Please reason about the current state. You should analyze all the opponent's moves and your moves, try to reason opponent's thought in detail. Only need to plan and reason now, no need to make move at this stage."
                    ]
                }
            }
        ]
    }
]


seen_pairs = set()

player1 = []
player2 = []

import itertools

for pair in itertools.permutations(models, 2):
    
    model1 = pair[0]["model"]
    model2 = pair[1]["model"]
    if (model1, model2) in seen_pairs or (model2, model1) in seen_pairs:
        continue
    seen_pairs.add((model1, model2))
    seen_pairs.add((model2, model1))
    player1.append(pair[0])
    player2.append(pair[1])
    print(f"{model1} vs {model2}")
print(len(models))
print(len(player1), len(player2))
with open('player-list1.json', 'w', encoding='utf-8') as f1:
    json.dump({
        "player1_model_list": player1,
        "player2_model_list": player2
    }, f1, ensure_ascii=False, indent=4)
