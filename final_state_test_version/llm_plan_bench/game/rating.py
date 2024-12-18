# Import necessary libraries
import numpy as np
import networkx as nx
import trueskill
import json

# Install the necessary packages before running this script:
# pip install numpy networkx trueskill glicko2 choix

try:
    from glicko2 import Player
except ImportError:
    print("Please install glicko2: pip install glicko2")
    exit(1)

try:
    import choix
except ImportError:
    print("Please install choix: pip install choix")
    exit(1)

# Competition data as a multiline string
data = """
(model1, model2)
(win, lose)
(lose, win)
draw
(gpt-4o, gpt-3.5-turbo)
4
0
0
(gpt-4o, gpt-4o-mini)
2
0
2
(gpt-4o, gpt-4-turbo)
0
0
4
(gpt-4o-mini, gpt-4-turbo)
0
0
4
(claude-haiku, gpt-3.5-turbo)
2
0
2
(claude-haiku, gpt-4-turbo)
0
0
4
(claude-haiku, gpt-4o-mini)
0
1
3
(claude-haiku, gpt-4o)
0
0
4
(claude-sonnet, gpt-3.5-turbo)
0
0
4
(claude-sonnet, gpt-4-turbo)
1
0
3
(claude-sonnet, gpt-4o-mini)
1
0
3
(claude-sonnet, gpt-4o)
1
1
2
"""

# Parse the data
lines = data.strip().split('\n')

# Skip the first 4 lines (headers)
lines = lines[4:]

matches = []

for i in range(0, len(lines), 4):
    match_line = lines[i]
    win1 = int(lines[i+1])
    win2 = int(lines[i+2])
    draw = int(lines[i+3])

    # Extract model1 and model2 from match_line
    match_line = match_line.strip('()')
    model1, model2 = match_line.split(',')
    model1 = model1.strip()
    model2 = model2.strip()

    # Generate match results
    # For each win1, model1 wins over model2
    for _ in range(win1):
        matches.append((model1, model2, 1))  # model1 wins
    # For each win2, model2 wins over model1
    for _ in range(win2):
        matches.append((model1, model2, 0))  # model1 loses
    # For each draw
    for _ in range(draw):
        matches.append((model1, model2, 0.5))  # draw

# List of all models
models = list(set([model for match in matches for model in match[:2]]))

# Initialize result dictionary
results = {}

######################################
# 1. Elo Rating
######################################
def compute_elo_ratings(matches):
    K = 32  # K-factor
    elo_ratings = {model: 1500 for model in models}

    for match in matches:
        model1, model2, result = match
        r1 = elo_ratings[model1]
        r2 = elo_ratings[model2]

        # Expected scores
        E1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
        E2 = 1 / (1 + 10 ** ((r1 - r2) / 400))

        # Update ratings
        elo_ratings[model1] = r1 + K * (result - E1)
        elo_ratings[model2] = r2 + K * ((1 - result) - E2)

    return elo_ratings

elo_ratings = compute_elo_ratings(matches)
results['Elo'] = elo_ratings

######################################
# 2. TrueSkill Rating
######################################
def compute_trueskill_ratings(matches):
    env = trueskill.TrueSkill(draw_probability=0)
    ts_ratings = {model: env.create_rating() for model in models}

    for match in matches:
        model1, model2, result = match
        rating1 = ts_ratings[model1]
        rating2 = ts_ratings[model2]

        if result == 1:  # model1 wins
            rating1, rating2 = trueskill.rate_1vs1(rating1, rating2)
        elif result == 0:  # model1 loses
            rating2, rating1 = trueskill.rate_1vs1(rating2, rating1)
        else:  # draw
            rating1, rating2 = trueskill.rate_1vs1(rating1, rating2, drawn=True)

        ts_ratings[model1] = rating1
        ts_ratings[model2] = rating2

    # Convert ratings to dict
    ts_ratings_dict = {model: {'mu': rating.mu, 'sigma': rating.sigma} for model, rating in ts_ratings.items()}
    return ts_ratings_dict

ts_ratings = compute_trueskill_ratings(matches)
results['TrueSkill'] = ts_ratings

######################################
# 3. Glicko2 Rating
######################################
def compute_glicko2_ratings(matches):
    players = {model: Player() for model in models}

    for match in matches:
        model1, model2, result = match
        p1 = players[model1]
        p2 = players[model2]

        if result == 1:  # model1 wins
            score1 = 1
            score2 = 0
        elif result == 0:  # model1 loses
            score1 = 0
            score2 = 1
        else:  # draw
            score1 = 0.5
            score2 = 0.5

        # Update players
        p1.update_player([p2.rating], [p2.rd], [score1])
        p2.update_player([p1.rating], [p1.rd], [score2])

    # Collect ratings
    glicko2_ratings = {}
    for model, player in players.items():
        glicko2_ratings[model] = {
            'rating': player.rating,
            'rd': player.rd,
            'vol': player.vol
        }
    return glicko2_ratings

glicko2_ratings = compute_glicko2_ratings(matches)
results['Glicko2'] = glicko2_ratings

######################################
# 4. Bradley-Terry Model using choix
######################################
def compute_bradley_terry_ratings(matches):
    import choix

    model_indices = {model: idx for idx, model in enumerate(models)}
    comparisons = []

    for match in matches:
        model1, model2, result = match
        idx1 = model_indices[model1]
        idx2 = model_indices[model2]

        if result == 1:
            comparisons.append((idx1, idx2))
        elif result == 0:
            comparisons.append((idx2, idx1))
        else:
            # For draws, add half wins to both
            comparisons.append((idx1, idx2))
            comparisons.append((idx2, idx1))

    # Estimate skills using MLE for pairwise comparisons (Bradley-Terry model)
    skills = choix.mle_pairwise(n_items=len(models), data=comparisons, alpha=0.01)

    # Map skills back to model names
    bt_ratings = {model: skill for model, skill in zip(models, skills)}
    return bt_ratings

# bt_ratings = compute_bradley_terry_ratings(matches)
# results['BradleyTerry'] = bt_ratings

######################################
# 5. Plackett-Luce Model using choix
######################################
def compute_plackett_luce_ratings(matches):
    import choix

    model_indices = {model: idx for idx, model in enumerate(models)}
    comparisons = []

    for match in matches:
        model1, model2, result = match
        idx1 = model_indices[model1]
        idx2 = model_indices[model2]

        if result == 1:
            comparisons.append([idx1, idx2])
        elif result == 0:
            comparisons.append([idx2, idx1])
        else:
            # For draws, represent as ties
            comparisons.append([idx1, idx2])
            comparisons.append([idx2, idx1])

    # Estimate skills using ILSR (Plackett-Luce model)
    skills = choix.ilsr_pairwise(len(models), comparisons)

    # Map skills back to model names
    pl_ratings = {model: skill for model, skill in zip(models, skills)}
    return pl_ratings

pl_ratings = compute_plackett_luce_ratings(matches)
results['PlackettLuce'] = pl_ratings

######################################
# 6. PageRank
######################################
def compute_pagerank_ratings(matches):
    G = nx.DiGraph()

    for match in matches:
        model1, model2, result = match
        if result == 1:
            G.add_edge(model1, model2)
        elif result == 0:
            G.add_edge(model2, model1)
        else:
            # For draws, add edges both ways with equal weights
            G.add_edge(model1, model2, weight=0.5)
            G.add_edge(model2, model1, weight=0.5)

    pr = nx.pagerank(G, alpha=0.85)
    return pr

pr_ratings = compute_pagerank_ratings(matches)
results['PageRank'] = pr_ratings

######################################
# 7. Rank Centrality
######################################
def compute_rank_centrality_ratings(matches):
    model_indices = {model: idx for idx, model in enumerate(models)}
    n = len(models)
    W = np.zeros((n, n))

    for match in matches:
        model1, model2, result = match
        i = model_indices[model1]
        j = model_indices[model2]

        if result == 1:
            W[i, j] += 1
        elif result == 0:
            W[j, i] += 1
        else:
            W[i, j] += 0.5
            W[j, i] += 0.5

    # Normalize rows
    row_sums = W.sum(axis=1)
    W_normalized = np.divide(W, row_sums[:, np.newaxis], out=np.zeros_like(W), where=row_sums[:, np.newaxis]!=0)

    # Compute stationary distribution
    eigvals, eigvecs = np.linalg.eig(W_normalized.T)
    stationary = np.real(eigvecs[:, np.isclose(eigvals, 1)])
    stationary = stationary / stationary.sum()

    # Map scores back to model names
    rc_ratings = {model: score for model, score in zip(models, stationary.flatten())}
    return rc_ratings

rc_ratings = compute_rank_centrality_ratings(matches)
results['RankCentrality'] = rc_ratings

######################################
# Output Results to JSON
######################################
import json

# Convert numpy types to native Python types for JSON serialization
def convert_np(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Serialize results
with open('ranking_results.json', 'w') as f:
    json.dump(results, f, default=convert_np, indent=4)

print("Ranking results have been saved to 'ranking_results.json'")
