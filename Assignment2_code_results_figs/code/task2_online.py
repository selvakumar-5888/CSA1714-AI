"""Task 2 - Online search agent (online DFS and LRTA*) for a rover in an unmapped facility."""
import json, random, statistics as st
from collections import deque
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DIRS = [(-1, 0), (0, 1), (1, 0), (0, -1)]


def make_maze(n, seed, braid):
    """Perfect maze (n odd) with a fraction `braid` of dead ends removed (braid=0 -> many dead ends)."""
    rng = random.Random(seed)
    g = [[1] * n for _ in range(n)]
    g[1][1] = 0
    stack = [(1, 1)]
    while stack:
        r, c = stack[-1]
        opts = [(r + 2 * dr, c + 2 * dc, dr, dc) for dr, dc in DIRS
                if 0 < r + 2 * dr < n - 1 and 0 < c + 2 * dc < n - 1 and g[r + 2 * dr][c + 2 * dc]]
        if not opts:
            stack.pop(); continue
        nr, nc, dr, dc = rng.choice(opts)
        g[r + dr][c + dc] = 0; g[nr][nc] = 0
        stack.append((nr, nc))
    for r in range(1, n - 1):
        for c in range(1, n - 1):
            if not g[r][c] and dead_end(g, r, c) and rng.random() < braid:
                cand = [(r + dr, c + dc) for dr, dc in DIRS
                        if 0 < r + dr < n - 1 and 0 < c + dc < n - 1 and g[r + dr][c + dc]
                        and 0 <= r + 2 * dr < n and 0 <= c + 2 * dc < n and not g[r + 2 * dr][c + 2 * dc]]
                if cand:
                    wr, wc = rng.choice(cand); g[wr][wc] = 0
    return g


def free_nb(g, p):
    n = len(g)
    return [(p[0] + dr, p[1] + dc) for dr, dc in DIRS
            if 0 <= p[0] + dr < n and 0 <= p[1] + dc < n and not g[p[0] + dr][p[1] + dc]]


def dead_end(g, r, c):
    return len(free_nb(g, (r, c))) == 1


def count_dead_ends(g):
    return sum(1 for r in range(len(g)) for c in range(len(g)) if not g[r][c] and dead_end(g, r, c))


def bfs_dist(g, s):
    d = {s: 0}; q = deque([s])
    while q:
        c = q.popleft()
        for nb in free_nb(g, c):
            if nb not in d:
                d[nb] = d[c] + 1; q.append(nb)
    return d


def online_dfs(g, start, goal, cap=10 ** 6):
    """ONLINE-DFS-AGENT: senses only the 4 neighbours; remembers visited cells; backtracks physically."""
    pos, visited, stack = start, {start}, []
    moves = revisits = 0
    while pos != goal:
        nxt = [nb for nb in free_nb(g, pos) if nb not in visited]
        if nxt:
            stack.append(pos); pos = nxt[0]; visited.add(pos)
        elif stack:
            pos = stack.pop(); revisits += 1                 # physical backtrack onto a known cell
        else:
            return dict(found=False, moves=moves, revisits=revisits, explored=len(visited))
        moves += 1
        if moves > cap:
            break
    return dict(found=True, moves=moves, revisits=revisits, explored=len(visited))


def lrta(g, start, goal, H, cap, rng):
    """One LRTA* trial. H (dict) persists across trials -> learning."""
    h0 = lambda p: abs(p[0] - goal[0]) + abs(p[1] - goal[1])
    pos, moves, visited, revisits = start, 0, {start}, 0
    while pos != goal and moves < cap:
        nbs = free_nb(g, pos)
        scores = [(1 + H.get(nb, h0(nb)), rng.random(), nb) for nb in nbs]
        best = min(scores)
        H[pos] = max(H.get(pos, h0(pos)), best[0]) if False else best[0]
        pos = best[2]; moves += 1
        if pos in visited: revisits += 1
        visited.add(pos)
    return dict(found=pos == goal, moves=moves, revisits=revisits, explored=len(visited))


def pick_target(g, start, frac):
    d = bfs_dist(g, start)
    mx = max(d.values())
    tgt = min(d, key=lambda p: abs(d[p] - frac * mx))
    return tgt, d[tgt]


def seal_target(g, start):
    """unreachable target: a free cell enclosed by walls (an isolated pocket)."""
    g2 = [row[:] for row in g]
    n = len(g)
    pocket = (n - 2, n - 2)
    for dr, dc in DIRS:
        r, c = pocket[0] + dr, pocket[1] + dc
        if 0 <= r < n and 0 <= c < n: g2[r][c] = 1
    g2[pocket[0]][pocket[1]] = 0
    return g2, pocket


if __name__ == "__main__":
    out = {}
    # E1: target distance (n=31, braid 0.3), 10 seeds
    rows = []
    for frac in (0.1, 0.25, 0.5, 0.75, 1.0):
        res = []
        for seed in range(10):
            g = make_maze(31, seed, 0.3); tgt, opt = pick_target(g, (1, 1), frac)
            r = online_dfs(g, (1, 1), tgt)
            l = lrta(g, (1, 1), tgt, {}, 200000, random.Random(seed))
            res.append((opt, r["moves"], r["revisits"], l["moves"]))
        rows.append(dict(frac=frac, opt=st.mean(x[0] for x in res), dfs_moves=st.mean(x[1] for x in res),
                         dfs_rev=st.mean(x[2] for x in res), dfs_cr=st.mean(x[1] / x[0] for x in res),
                         lrta_moves=st.mean(x[3] for x in res), lrta_cr=st.mean(x[3] / x[0] for x in res)))
        print("E1", rows[-1])
    out["E1"] = rows

    # E2: size x dead-end density
    rows = []
    for n in (21, 31, 41, 51):
        for braid in (0.0, 0.5, 1.0):
            res = []
            for seed in range(10):
                g = make_maze(n, seed, braid); tgt, opt = pick_target(g, (1, 1), 0.75)
                r = online_dfs(g, (1, 1), tgt)
                res.append((opt, r["moves"], r["revisits"], count_dead_ends(g)))
            rows.append(dict(n=n, braid=braid, dead_ends=st.mean(x[3] for x in res), opt=st.mean(x[0] for x in res),
                             moves=st.mean(x[1] for x in res), revisits=st.mean(x[2] for x in res),
                             cr=st.mean(x[1] / x[0] for x in res), cr_max=max(x[1] / x[0] for x in res)))
            print("E2", rows[-1])
    out["E2"] = rows

    # E3: unreachable targets
    rows = []
    for n in (21, 31, 41):
        res = []
        for seed in range(10):
            g, pocket = seal_target(make_maze(n, seed, 0.3), (1, 1))
            reach = len(bfs_dist(g, (1, 1)))
            r = online_dfs(g, (1, 1), pocket)
            l = lrta(g, (1, 1), pocket, {}, 20 * n * n, random.Random(seed))
            res.append((reach, r["found"], r["moves"], r["explored"], l["found"], l["moves"]))
        rows.append(dict(n=n, reachable=st.mean(x[0] for x in res), dfs_terminates=all(not x[1] for x in res),
                         dfs_moves=st.mean(x[2] for x in res), dfs_explored=st.mean(x[3] for x in res),
                         dfs_ratio_moves_over_cells=st.mean(x[2] / x[0] for x in res),
                         lrta_found=any(x[4] for x in res), lrta_moves_at_cap=st.mean(x[5] for x in res)))
        print("E3", rows[-1])
    out["E3"] = rows

    # E4: LRTA* learning over repeated trials (same facility)
    trials = 30
    curves = []
    for seed in range(10):
        g = make_maze(31, seed, 0.5); tgt, opt = pick_target(g, (1, 1), 0.75)
        H, rng, mv = {}, random.Random(seed), []
        for t in range(trials):
            mv.append(lrta(g, (1, 1), tgt, H, 200000, rng)["moves"] / opt)
        curves.append(mv)
    mean_curve = [st.mean(c[t] for c in curves) for t in range(trials)]
    out["E4"] = dict(mean_cr_per_trial=mean_curve)
    print("E4", [round(x, 2) for x in mean_curve])
    # DFS first-mission ratio on the same mazes
    dfs_cr = st.mean(online_dfs(g2, (1, 1), pick_target(g2, (1, 1), .75)[0])["moves"] / pick_target(g2, (1, 1), .75)[1]
                     for g2 in (make_maze(31, s, 0.5) for s in range(10)))
    out["E4"]["dfs_cr"] = dfs_cr

    # E5: amortised cost over M missions (n=31, braid .5)
    g_list = [make_maze(31, s, 0.5) for s in range(10)]
    c_dfs = st.mean(online_dfs(g, (1, 1), pick_target(g, (1, 1), .75)[0])["moves"] for g in g_list)
    c_opt = st.mean(pick_target(g, (1, 1), .75)[1] for g in g_list)
    c_explore = st.mean(len([1 for r in g for v in r if not v]) for g in g_list) * 2  # full-DFS mapping ~2 moves/cell
    am = []
    for M in (1, 2, 5, 10, 50, 200):
        am.append(dict(M=M, repeat_online_dfs=M * c_dfs, map_once_then_plan=c_explore + (M) * c_opt,
                       lrta_total=sum(mean_curve[t] if t < trials else mean_curve[-1] for t in range(M)) * c_opt))
        print("E5", am[-1])
    out["E5"] = dict(rows=am, c_dfs=c_dfs, c_opt=c_opt, c_explore=c_explore)
    json.dump(out, open("../results/task2.json", "w"), indent=1)

    # figures
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    ax[0].plot(range(1, trials + 1), mean_curve, "o-"); ax[0].axhline(1, ls="--", c="gray")
    ax[0].set_xlabel("trial number (same facility)"); ax[0].set_ylabel("competitive ratio"); ax[0].set_title("LRTA* learning across trials", fontsize=9)
    xs = [e["frac"] for e in out["E1"]]
    ax[1].plot(xs, [e["dfs_cr"] for e in out["E1"]], "s-", label="online DFS")
    ax[1].plot(xs, [e["lrta_cr"] for e in out["E1"]], "^-", label="LRTA* (1st trial)")
    ax[1].set_xlabel("target distance (fraction of max BFS distance)"); ax[1].set_ylabel("competitive ratio")
    ax[1].legend(fontsize=7); ax[1].set_title("Effect of target distance", fontsize=9)
    plt.tight_layout(); plt.savefig("../figs/fig3_task2.png", dpi=130)
