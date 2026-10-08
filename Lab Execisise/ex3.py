from collections import deque

def water_jug_problem(capacity1, capacity2, target):
    visited = set()
    queue = deque()

    queue.append((0, 0, []))

    while queue:
        jug1, jug2, path = queue.popleft()

        if (jug1, jug2) in visited:
            continue

        visited.add((jug1, jug2))


        path = path + [(jug1, jug2)]

        if jug1 == target or jug2 == target:
            print("Solution:")
            for state in path:
                print(state)
            return

        states = [
            (capacity1, jug2),  
            (jug1, capacity2),  
            (0, jug2),          
            (jug1, 0),          

            (max(0, jug1 - (capacity2 - jug2)),
             min(capacity2, jug1 + jug2)),

            (min(capacity1, jug1 + jug2),
             max(0, jug2 - (capacity1 - jug1)))
        ]

        for state in states:
            if state not in visited:
                queue.append((state[0], state[1], path))



water_jug_problem(4, 3, 2)
