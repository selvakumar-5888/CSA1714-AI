from collections import deque


def is_safe(m, c):
    
    if m < 0 or c < 0 or m > 3 or c > 3:
        return False

    
    if m > 0 and m < c:
        return False

   
    mr = 3 - m
    cr = 3 - c

    if mr > 0 and mr < cr:
        return False

    return True


def solve():
    start = (3, 3, 0)
    goal = (0, 0, 1)

    # Possible boat movements
    moves = [
        (1, 0),  # 1 Missionary
        (2, 0),  # 2 Missionaries
        (0, 1),  # 1 Cannibal
        (0, 2),  # 2 Cannibals
        (1, 1)   # 1 Missionary and 1 Cannibal
    ]

    queue = deque([start])
    visited = {start}
    parent = {start: None}

    while queue:
        state = queue.popleft()
        m, c, boat = state

        if state == goal:
            break

        for dm, dc in moves:

            if boat == 0:  # Boat moves from left to right
                new_m = m - dm
                new_c = c - dc
                new_boat = 1
            else:          # Boat moves from right to left
                new_m = m + dm
                new_c = c + dc
                new_boat = 0

            new_state = (new_m, new_c, new_boat)

            if is_safe(new_m, new_c) and new_state not in visited:
                visited.add(new_state)
                parent[new_state] = state
                queue.append(new_state)

    
    if goal not in parent:
        print("No solution found.")
        return

    path = []
    state = goal

    while state is not None:
        path.append(state)
        state = parent[state]

    path.reverse()

    print("Solution:")
    for i, state in enumerate(path):
        m, c, boat = state

        side = "Left" if boat == 0 else "Right"

        print(
            f"Step {i}: "
            f"Left(M={m}, C={c}) | "
            f"Right(M={3-m}, C={3-c}) | "
            f"Boat = {side}"
        )


solve()
