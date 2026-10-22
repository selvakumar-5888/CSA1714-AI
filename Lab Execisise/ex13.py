
# Minimax Algorithm for Gaming

def minimax(depth, node_index, maximizing_player, scores, height):
    # Base case: leaf node
    if depth == height:
        return scores[node_index]

    if maximizing_player:
        best = float('-inf')

        for i in range(2):
            value = minimax(
                depth + 1,
                node_index * 2 + i,
                False,
                scores,
                height
            )
            best = max(best, value)

        return best

    else:
        best = float('inf')

        for i in range(2):
            value = minimax(
                depth + 1,
                node_index * 2 + i,
                True,
                scores,
                height
            )
            best = min(best, value)

        return best


# Leaf node scores of the game tree
scores = [3, 5, 2, 9, 12, 5, 23, 23]

# Calculate tree height
height = 3

# Find the optimal score
optimal_score = minimax(0, 0, True, scores, height)

print("Leaf node scores:", scores)
print("Optimal score using Minimax:", optimal_score)
