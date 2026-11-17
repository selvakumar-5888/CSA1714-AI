"""Task 1 - Uniform-Cost, Greedy Best-First and A* on grid maps (campus shuttle)."""
import heapq, json, random, time
from collections import deque
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DIRS = [(-1, 0), (0, 1), (1, 0), (0, -1)]


def h_manhattan(p, goal):
    """Own heuristic: Manhattan distance (exact cost of the relaxed problem
    'obstacles removed' on a 4-connected unit-cost grid)."""
    return abs(p[0] - goal[0]) + abs(p[1] - goal[1])


def search(grid, start, goal, mode):
    n, m = len(grid), len(grid[0])
    t0 = time.perf_counter()
    prio = {"ucs": lambda g, h: g, "gbfs": lambda g, h: h, "astar": lambda g, h: g + h}[mode]
    cnt = 0
    heap = [(prio(0, h_manhattan(start, goal)), h_manhattan(start, goal), cnt, start)]
    g = {start: 0}
    parent = {start: None}
    open_live = {start}
    closed = set()
    expanded, generated, maxf = 0, 1, 1
    while heap:
        _, _, _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        open_live.discard(cur)
        if cur == goal:
            cost = g[cur]
            return dict(expanded=expanded, generated=generated, max_frontier=maxf, cost=cost,
                        time_ms=(time.perf_counter() - t0) * 1000, closed=closed | {cur})
        closed.add(cur)
        expanded += 1
        for dr, dc in DIRS:
            nb = (cur[0] + dr, cur[1] + dc)
            if not (0 <= nb[0] < n and 0 <= nb[1] < m) or grid[nb[0]][nb[1]] or nb in closed:
                continue
            ng = g[cur] + 1
            if mode == "gbfs":
                if nb in g:
                    continue          # greedy: first discovery only
            elif nb in g and g[nb] <= ng:
                continue
            g[nb] = ng
            parent[nb] = cur
            cnt += 1
            h = h_manhattan(nb, goal)
            heapq.heappush(heap, (prio(ng, h), h, cnt, nb))
            open_live.add(nb)
            generated += 1
        maxf = max(maxf, len(open_live))
    return dict(expanded=expanded, generated=generated, max_frontier=maxf, cost=None,
                time_ms=(time.perf_counter() - t0) * 1000, closed=closed)


def bfs_opt(grid, start, goal):
    n, m = len(grid), len(grid[0])
    d = {start: 0}
    q = deque([start])
    while q:
        c = q.popleft()
        if c == goal:
            return d[c]
        for dr, dc in DIRS:
            nb = (c[0] + dr, c[1] + dc)
            if 0 <= nb[0] < n and 0 <= nb[1] < m and not grid[nb[0]][nb[1]] and nb not in d:
                d[nb] = d[c] + 1
                q.append(nb)
    return None


# ---------------------------------------------------------------- map builders
def open_map(n, seed, density=0.05):
    rng = random.Random(seed)
    while True:
        grid = [[1 if rng.random() < density else 0 for _ in range(n)] for _ in range(n)]
        s, g = (0, 0), (n - 1, n - 1)
        grid[0][0] = grid[n - 1][n - 1] = 0
        if bfs_opt(grid, s, g) is not None:
            return grid, s, g


def maze_map(n, seed, loops=0.08):
    """Recursive-backtracker maze (n odd) + a fraction of interior walls knocked out so that
    several routes of different length exist."""
    rng = random.Random(seed)
    grid = [[1] * n for _ in range(n)]
    stack = [(1, 1)]
    grid[1][1] = 0
    while stack:
        r, c = stack[-1]
        opts = [(r + 2 * dr, c + 2 * dc, dr, dc) for dr, dc in DIRS
                if 0 < r + 2 * dr < n - 1 and 0 < c + 2 * dc < n - 1 and grid[r + 2 * dr][c + 2 * dc]]
        if not opts:
            stack.pop()
            continue
        nr, nc, dr, dc = rng.choice(opts)
        grid[r + dr][c + dc] = 0
        grid[nr][nc] = 0
        stack.append((nr, nc))
    walls = [(r, c) for r in range(1, n - 1) for c in range(1, n - 1)
             if grid[r][c] and ((r % 2 == 1) != (c % 2 == 1))]
    for r, c in rng.sample(walls, int(loops * len(walls))):
        grid[r][c] = 0
    return grid, (1, 1), (n - 2, n - 2)


def trap_map(n):
    """Edge-case map: 'decoy corridor'. A full-height wall band (open only along the top row) splits start
    from goal. A gap on the straight line to the goal leads into a long serpentine corridor (dead-end-like
    detour). Greedy follows the falling h-values into the corridor; the true shortest route is around the top."""
    grid = [[0] * n for _ in range(n)]
    cw, W, r0 = n // 2, max(2, n // 10), n // 4
    for r in range(1, n):
        for c in range(cw - W, cw + W + 1):
            grid[r][c] = 1
    L = (n - 2 - r0) // 2 + 1
    rows = [r0 + 2 * i for i in range(L)]
    for i, r in enumerate(rows):
        for c in range(cw - W + 1, cw + W):
            grid[r][c] = 0                   # lane (sealed at both band edges)
        if i < L - 1:                        # connector between lane i and i+1
            grid[r + 1][(cw + W - 1) if i % 2 == 0 else (cw - W + 1)] = 0
    grid[rows[0]][cw - W] = 0                # entrance gap (on the straight line to the goal)
    grid[rows[-1]][cw + W] = 0               # exit at the far end of the serpentine
    return grid, (r0, 1), (r0, n - 2)


def draw(ax, grid, closed, start, goal, title):
    img = np.array(grid, dtype=float) * 0.0
    arr = np.ones((len(grid), len(grid[0]), 3))
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c]:
                arr[r, c] = (0.1, 0.1, 0.1)
            elif (r, c) in closed:
                arr[r, c] = (0.55, 0.78, 0.95)
    arr[start] = (0.1, 0.7, 0.1)
    arr[goal] = (0.9, 0.1, 0.1)
    ax.imshow(arr, interpolation="nearest")
    ax.set_title(title, fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])


if __name__ == "__main__":
    families = {
        "A: Open (5% obstacles)": [("n=20", *open_map(20, 1)), ("n=40", *open_map(40, 2)), ("n=60", *open_map(60, 3))],
        "B: Maze-like (loops)": [("n=21", *maze_map(21, 1)), ("n=41", *maze_map(41, 2)), ("n=61", *maze_map(61, 3))],
        "C: Decoy corridor (edge case)": [("n=21", *trap_map(21)), ("n=41", *trap_map(41)), ("n=61", *trap_map(61))],
    }
    rows = []
    figs = {}
    for fam, variants in families.items():
        for label, grid, s, g in variants:
            opt = bfs_opt(grid, s, g)
            for mode in ("ucs", "gbfs", "astar"):
                r = search(grid, s, g, mode)
                closed = r.pop("closed")
                r.update(map=fam, size=label, algo=mode, optimal_cost=opt,
                         is_optimal=(r["cost"] == opt), suboptimality=round(r["cost"] / opt, 3))
                rows.append(r)
                figs[(fam, label, mode)] = (grid, closed, s, g, r)
                print(f"{fam:26s} {label:6s} {mode:6s} exp={r['expanded']:5d} gen={r['generated']:5d} "
                      f"maxF={r['max_frontier']:4d} cost={r['cost']:4d} opt={opt:4d} optimal={r['is_optimal']} "
                      f"t={r['time_ms']:.1f}ms")
    json.dump(rows, open("../results/task1.json", "w"), indent=1)

    # Figure 1: expanded cells (middle size of each family)
    fig, axes = plt.subplots(3, 3, figsize=(8.5, 8.5))
    names = {"ucs": "Uniform-cost", "gbfs": "Greedy", "astar": "A*"}
    for i, (fam, variants) in enumerate(families.items()):
        label = variants[1][0]
        for j, mode in enumerate(("ucs", "gbfs", "astar")):
            grid, closed, s, g, r = figs[(fam, label, mode)]
            draw(axes[i][j], grid, closed, s, g,
                 f"{fam.split(':')[0]} - {names[mode]}\nexp={r['expanded']}, cost={r['cost']}")
    plt.tight_layout()
    plt.savefig("../figs/fig1_task1_expansion.png", dpi=130)

    # Figure 2: bar chart of expanded nodes
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), sharey=False)
    for ax, fam in zip(axes, families):
        sizes = [v[0] for v in families[fam]]
        for k, mode in enumerate(("ucs", "gbfs", "astar")):
            vals = [next(r["expanded"] for r in rows if r["map"] == fam and r["size"] == s_ and r["algo"] == mode)
                    for s_ in sizes]
            ax.bar(np.arange(3) + 0.27 * (k - 1), vals, 0.27, label=names[mode])
        ax.set_xticks(range(3)); ax.set_xticklabels(sizes)
        ax.set_title(fam.split(" (")[0], fontsize=9); ax.set_ylabel("nodes expanded")
    axes[0].legend(fontsize=7)
    plt.tight_layout()
    plt.savefig("../figs/fig2_task1_bars.png", dpi=130)
