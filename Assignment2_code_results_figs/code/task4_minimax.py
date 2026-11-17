"""Task 4 - Depth-limited minimax with own evaluation function on an n x n k-in-a-row game."""
import json, math, random, time, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WIN = 10 ** 6


class Game:
    def __init__(self, n, k):
        self.n, self.k = n, k
        self.windows = []
        for r in range(n):
            for c in range(n):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    er, ec = r + (k - 1) * dr, c + (k - 1) * dc
                    if 0 <= er < n and 0 <= ec < n:
                        self.windows.append(tuple((r + i * dr) * n + (c + i * dc) for i in range(k)))
        self.by_cell = [[w for w in self.windows if cell in w] for cell in range(n * n)]

    def won(self, b, cell, p):
        return any(all(b[i] == p for i in w) for w in self.by_cell[cell])

    def evaluate(self, b):
        """Own evaluation (from X's view): every k-window that holds only one colour scores 10^(count-1);
        windows containing both colours are dead (0). Positive favours X (player 1)."""
        s = 0
        for w in self.windows:
            x = o = 0
            for i in w:
                v = b[i]
                if v == 1: x += 1
                elif v == 2: o += 1
            if x and not o: s += 10 ** (x - 1)
            elif o and not x: s -= 10 ** (o - 1)
        return s


def minimax(game, b, depth, player, ctr, last=None):
    """player 1 = MAX (X), 2 = MIN (O). Counts expanded nodes and evaluation-function calls."""
    if last is not None and game.won(b, last, 3 - player):
        ctr["evals"] += 1
        return WIN if 3 - player == 1 else -WIN
    moves = [i for i, v in enumerate(b) if v == 0]
    if not moves:
        ctr["evals"] += 1
        return 0
    if depth == 0:
        ctr["evals"] += 1
        return game.evaluate(b)
    ctr["expanded"] += 1
    best = -math.inf if player == 1 else math.inf
    for m in moves:
        b[m] = player
        v = minimax(game, b, depth - 1, 3 - player, ctr, m)
        b[m] = 0
        best = max(best, v) if player == 1 else min(best, v)
    return best


def best_move(game, b, depth, player, ctr):
    moves = [i for i, v in enumerate(b) if v == 0]
    scored = []
    for m in moves:
        b[m] = player
        scored.append((minimax(game, b, depth - 1, 3 - player, ctr, m), m))
        b[m] = 0
    return (max(scored) if player == 1 else min(scored))[1] if scored else None


def play(game, depth, rng, agent_first):
    b = [0] * (game.n ** 2)
    player, agent = 1, (1 if agent_first else 2)
    while True:
        moves = [i for i, v in enumerate(b) if v == 0]
        if not moves:
            return 0
        if player == agent:
            ctr = dict(expanded=0, evals=0)
            vals = []
            for m in moves:
                b[m] = player
                vals.append((minimax(game, b, depth - 1, 3 - player, ctr, m), rng.random(), m))
                b[m] = 0
            m = (max(vals) if player == 1 else min(vals))[2]
        else:
            m = rng.choice(moves)
        b[m] = player
        if game.won(b, m, player):
            return 1 if player == agent else -1
        player = 3 - player


def perm(m, i):
    return math.perm(m, i)


def theory_const(b, d):
    return (b ** d - 1) // (b - 1), b ** d


def theory_fall(m, d):
    return sum(perm(m, i) for i in range(d)), perm(m, d)


if __name__ == "__main__":
    out = {"growth": [], "winrate": []}
    configs = [("3x3 k=3", 3, 3), ("4x4 k=4", 4, 4), ("5x5 k=4", 5, 4)]
    print("== Growth of work, first move on an empty board (m = n*n legal moves) ==")
    for name, n, k in configs:
        g = Game(n, k)
        for d in range(1, 6):
            if n == 5 and d > 4: continue
            if n == 3 and d > 5: continue
            b = [0] * (n * n)
            ctr = dict(expanded=0, evals=0)
            t0 = time.perf_counter()
            best_move(g, b, d, 1, ctr)
            ctr["expanded"] += 1  # root
            dt = time.perf_counter() - t0
            te, tl = theory_fall(n * n, d)
            tc_e, tc_l = theory_const(n * n, d)
            row = dict(board=name, d=d, m=n * n, expanded=ctr["expanded"], evals=ctr["evals"], time_s=dt,
                       theory_expanded=te, theory_leaves=tl, const_b_leaves=tc_l)
            out["growth"].append(row)
            print(row)
    print("== Quality of play: minimax(depth d) vs random, 20 games (10 first / 10 second) ==")
    play_cfg = {"3x3 k=3": (1, 2, 4), "4x4 k=4": (1, 2, 3), "5x5 k=4": (1, 2, 3)}
    for name, n, k in configs:
        g = Game(n, k)
        for d in play_cfg[name]:
            rng = random.Random(1000 + d)
            res = [play(g, d, rng, i % 2 == 0) for i in range(20)]
            t0 = time.perf_counter()
            row = dict(board=name, d=d, wins=res.count(1), draws=res.count(0), losses=res.count(-1),
                       win_rate=res.count(1) / 20)
            out["winrate"].append(row)
            print(row)
    json.dump(out, open("../results/task4.json", "w"), indent=1)

    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    for name, n, k in configs:
        rows = [r for r in out["growth"] if r["board"] == name]
        ax.semilogy([r["d"] for r in rows], [r["evals"] for r in rows], "o-", label=f"{name} measured")
        ax.semilogy([r["d"] for r in rows], [r["theory_leaves"] for r in rows], "x--", alpha=.6, label=f"{name} theory P(m,d)")
    ax.set_xlabel("lookahead depth d"); ax.set_ylabel("evaluation calls (leaves)"); ax.legend(fontsize=6)
    plt.tight_layout(); plt.savefig("../figs/fig5_task4.png", dpi=130)
