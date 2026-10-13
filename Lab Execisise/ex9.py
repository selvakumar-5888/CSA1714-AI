
from itertools import permutations

def tsp(graph, start):
    n = len(graph)
    cities = [i for i in range(n) if i != start]

    min_cost = float('inf')
    best_path = []

    for path in permutations(cities):
        route = [start] + list(path) + [start]
        cost = 0

        for i in range(len(route) - 1):
            cost += graph[route[i]][route[i + 1]]

        if cost < min_cost:
            min_cost = cost
            best_path = route

    return best_path, min_cost


graph = [
    [0, 10, 15, 20],
    [10, 0, 35, 25],
    [15, 35, 0, 30],
    [20, 25, 30, 0]
]

path, cost = tsp(graph, 0)

print("Optimal Tour:", " -> ".join(str(c + 1) for c in path))
print("Minimum Cost:", cost)
