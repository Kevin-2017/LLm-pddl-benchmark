import csv

player_ratings_elo = {}
player_ratings_trueskill = {}
player_ratings_glicko2 = {}

matches = []
with open('model_win_stats.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        model1 = row['Model 1']
        model2 = row['Model 2']
        wins1 = int(row['Wins (Model 1)'])
        wins2 = int(row['Wins (Model 2)'])
        matches.append((model1, model2, wins1, wins2))

        if model1 not in player_ratings_elo:
            player_ratings_elo[model1] = 1500
        if model2 not in player_ratings_elo:
            player_ratings_elo[model2] = 1500


def elo_expected(rating1, rating2):
    return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

def elo_update(rating, expected, actual, k=32):
    return rating + k * (actual - expected)

for model1, model2, wins1, wins2 in matches:
    rating1 = player_ratings_elo[model1]
    rating2 = player_ratings_elo[model2]
    total_games = wins1 + wins2

    expected_score1 = total_games * elo_expected(rating1, rating2)
    actual_score1 = wins1

    player_ratings_elo[model1] = elo_update(rating1, expected_score1, actual_score1)
    player_ratings_elo[model2] = elo_update(rating2, total_games - expected_score1, wins2)

import trueskill

env = trueskill.TrueSkill(draw_probability=0.0)

for model in player_ratings_elo.keys():
    player_ratings_trueskill[model] = env.create_rating()

for model1, model2, wins1, wins2 in matches:
    total_games = wins1 + wins2
    for _ in range(wins1):
        rating1 = player_ratings_trueskill[model1]
        rating2 = player_ratings_trueskill[model2]
        rating1, rating2 = env.rate_1vs1(rating1, rating2)
        player_ratings_trueskill[model1] = rating1
        player_ratings_trueskill[model2] = rating2
    for _ in range(wins2):
        rating1 = player_ratings_trueskill[model1]
        rating2 = player_ratings_trueskill[model2]
        rating2, rating1 = env.rate_1vs1(rating2, rating1)
        player_ratings_trueskill[model1] = rating1
        player_ratings_trueskill[model2] = rating2

from glicko2 import Player

for model in player_ratings_elo.keys():
    player_ratings_glicko2[model] = Player()

for model1, model2, wins1, wins2 in matches:
    for _ in range(wins1):
        player1 = player_ratings_glicko2[model1]
        player2 = player_ratings_glicko2[model2]
        player1.update_player([player2.rating], [player2.rd], [1])
        player2.update_player([player1.rating], [player1.rd], [0])
    for _ in range(wins2):
        player1 = player_ratings_glicko2[model1]
        player2 = player_ratings_glicko2[model2]
        player1.update_player([player2.rating], [player2.rd], [0])
        player2.update_player([player1.rating], [player1.rd], [1])
        
print("Elo Ratings:")
for model, rating in sorted(player_ratings_elo.items(), key=lambda x: x[1], reverse=True):
    print(f"{model}: {rating:.2f}")

print("\nTrueSkill Ratings:")
for model, rating in sorted(player_ratings_trueskill.items(), key=lambda x: x[1].mu, reverse=True):
    print(f"{model}: μ={rating.mu:.2f}, σ={rating.sigma:.2f}")

print("\nGlicko2 Ratings:")
for model, player in sorted(player_ratings_glicko2.items(), key=lambda x: x[1].rating, reverse=True):
    print(f"{model}: {player.rating:.2f}, RD={player.rd:.2f}")
