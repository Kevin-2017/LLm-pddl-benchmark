import os
import json
import csv
from collections import defaultdict

def format_model_name(model_info):
    """
    Format model name by appending prompt_config names and filtered params (excluding 'prompt_messages').
    If the model_info is a string, return it directly.
    """
    if isinstance(model_info, str):
        return model_info  # If it's a simple string, return directly
    base_model = model_info["model"]
    prompt_config = model_info.get("prompt_config", [])
    if not prompt_config:
        return base_model
    prompt_details = []
    for config in prompt_config:
        # Filter out 'prompt_messages' from params
        params = {
            key: value
            for key, value in config.get("params", {}).items()
            if key != "prompt_messages"
        }
        params_str = ", ".join(f"{key}: {value}" for key, value in params.items())
        prompt_details.append(f"{config['name']} ({params_str})" if params else config['name'])
    formatted_name = f"{base_model} ({' + '.join(prompt_details)})"
    return formatted_name

def process_json_files(input_directory, output_csv):
    # Dictionary to store win statistics
    win_stats = defaultdict(lambda: {"wins_model1": 0, "wins_model2": 0, "draws": 0})

    # Iterate over all files in the directory
    for filename in os.listdir(input_directory):
        if filename.endswith('.json'):
            print(f"Processing file: {filename}")
            file_path = os.path.join(input_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                winner = data.get("winner", "")
                player1_model = format_model_name(data["player1_model"])
                player2_model = format_model_name(data["player2_model"])

                # Ensure the order of the model pair is consistent
                model1, model2 = sorted([player1_model, player2_model])

                if winner == "Player 1":
                    if player1_model == model1:
                        win_stats[(model1, model2)]["wins_model1"] += 1
                    else:
                        win_stats[(model1, model2)]["wins_model2"] += 1
                elif winner == "Player 2":
                    if player2_model == model1:
                        win_stats[(model1, model2)]["wins_model1"] += 1
                    else:
                        win_stats[(model1, model2)]["wins_model2"] += 1
                elif winner == "Draw":
                    win_stats[(model1, model2)]["draws"] += 1
                else:
                    print(f"Unknown winner value '{winner}' in file {filename}")

    # Write the statistics to a CSV file
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write the header
        csv_writer.writerow(["Model 1", "Model 2", "Wins (Model 1)", "Wins (Model 2)", "Draws"])
        
        for (model1, model2), stats in win_stats.items():
            csv_writer.writerow([
                model1, 
                model2, 
                stats["wins_model1"], 
                stats["wins_model2"], 
                stats["draws"]
            ])

# Example usage
input_directory = "ttt_archive" 
output_csv = "ttt_model_win_stats.csv"
process_json_files(input_directory, output_csv)
