"""Task 7 - Diagnose/Redesign/Validate: minimax of Task 4 vs transposition-aware, ordered alpha-beta."""
import json, math, time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from task4_minimax import Game, minimax, WIN


# ---------- Diagnosis: how often is the same position searched again? (instrumented plain minimax)
def repeat_profile(game, depth):
    seen = {}
    total = [0]

    def rec(b, d, player, last):
        key = (tuple(b), player)
        total[0] += 1
        seen[key] = seen.get(key, 0) + 1
        if d == 0 or (last is not None and game.won(b, last, 3 - player)) or 0 not in b:
            return
        for m in range(len(b)):
            if b[m] == 0:
                b[m] = player
                rec(b, d - 1, 3 - player, m)
                b[m] = 0
    rec([0] * (game.n ** 2), depth, 1, None)
    return total[0], len(seen)


# ---------- Redesign: negamax alpha-beta + transposition table (exact/lower/upper) + ordering
class Searcher:
    def __init__(self, game, ordering=True, use_tt=True, use_ab=True):
        self.g, self.ordering, self.use_tt, self.use_ab = game, ordering, use_tt, use_ab
        self.tt = {}
        self.ctr = dict(expanded=0, evals=0, tt_hits=0, cutoffs=0)
        c = (game.n - 1) / 2
        self.centre = sorted(range(game.n ** 2), key=lambda i: abs(i // game.n - c) + abs(i % game.n - c))
        self.rank = {cell: r for r, cell in enumerate(self.centre)}

    def search(self, b, depth, player, alpha, beta, last):
        g, ctr = self.g, self.ctr
        if last is not None and g.won(b, last, 3 - player):
            ctr["evals"] += 1
            return -WIN                                   # side to move has lost
        if 0 not in b:
            ctr["evals"] += 1
            return 0
        sign = 1 if player == 1 else -1
        if depth == 0:
            ctr["evals"] += 1
            return sign * g.evaluate(b)
        key = (tuple(b), depth)
        a0 = alpha
        if self.use_tt:
            e = self.tt.get(key)
            if e:
                v, flag = e
                if flag == 0: ctr["tt_hits"] += 1; return v
                if flag == 1: alpha = max(alpha, v)       # lower bound
                else: beta = min(beta, v)                 # upper bound
                if alpha >= beta: ctr["tt_hits"] += 1; return v
        ctr["expanded"] += 1
        moves = [i for i, v in enumerate(b) if v == 0]
        if self.ordering:
            moves.sort(key=lambda m: self.rank[m])        # centre cells first (more windows through them)
        best = -math.inf
        for m in moves:
            b[m] = player
            v = -self.search(b, depth - 1, 3 - player, -beta, -alpha, m)
            b[m] = 0
            if v > best: best = v
            if self.use_ab:
                alpha = max(alpha, v)
                if alpha >= beta:
                    ctr["cutoffs"] += 1
                    break
        if self.use_tt:
            flag = 0 if a0 < best < beta else (1 if best >= beta else 2)
            self.tt[key] = (best, flag)
        return best


def run_plain(game, depth):
    b = [0] * (game.n ** 2)
    ctr = dict(expanded=0, evals=0)
    t0 = time.perf_counter()
    v = minimax(game, b, depth, 1, ctr)
    return v, ctr, time.perf_counter() - t0


def run_new(game, depth, **kw):
    b = [0] * (game.n ** 2)
    s = Searcher(game, **kw)
    t0 = time.perf_counter()
    v = s.search(b, depth, 1, -math.inf, math.inf, None)
    return v, s.ctr, time.perf_counter() - t0, len(s.tt)


def predicted_distinct(m, d):
    x, o = (d + 1) // 2, d // 2
    return math.comb(m, x) * math.comb(m - x, o)


if __name__ == "__main__":
    out = {"diagnosis": [], "predictions": [], "compare": [], "isotime": []}
    print("== Diagnosis: positions searched vs distinct positions (plain minimax, empty board) ==")
    for name, n, k, ds in (("3x3 k=3", 3, 3, (3, 5, 7)), ("4x4 k=4", 4, 4, (3, 4, 5))):
        g = Game(n, k)
        for d in ds:
            tot, dist = repeat_profile(g, d)
            row = dict(board=name, d=d, visits=tot, distinct=dist, repeat_factor=tot / dist)
            out["diagnosis"].append(row); print(row)

    print("== Predictions (written before the validation runs) ==")
    for name, n, k, ds in (("4x4 k=4", 4, 4, (3, 4, 5)), ("5x5 k=4", 5, 4, (3, 4))):
        for d in ds:
            m = n * n
            p = dict(board=name, d=d, plain_leaves=math.perm(m, d), predicted_distinct_leaves=predicted_distinct(m, d),
                     predicted_tt_factor=math.perm(m, d) / predicted_distinct(m, d))
            out["predictions"].append(p); print(p)

    print("== Validation: same root value, different work ==")
    cases = (("3x3 k=3", 3, 3, 9), ("4x4 k=4", 4, 4, 4), ("4x4 k=4", 4, 4, 5), ("5x5 k=4", 5, 4, 3), ("5x5 k=4", 5, 4, 4))
    for name, n, k, d in cases:
        g = Game(n, k)
        if name == "3x3 k=3" and d == 9:
            pass
        vp, cp, tp = run_plain(g, d)
        row = dict(board=name, d=d, plain_value=vp, plain_expanded=cp["expanded"], plain_evals=cp["evals"], plain_time=tp)
        variants = {"tt": dict(ordering=False, use_ab=False, use_tt=True),
                    "ab": dict(ordering=False, use_ab=True, use_tt=False),
                    "ab_order": dict(ordering=True, use_ab=True, use_tt=False),
                    "full": dict(ordering=True, use_ab=True, use_tt=True)}
        for vn, kw in variants.items():
            v, c, t, sz = run_new(g, d, **kw)
            v = v if True else v
            row[f"{vn}_value"] = v; row[f"{vn}_expanded"] = c["expanded"]; row[f"{vn}_evals"] = c["evals"]
            row[f"{vn}_time"] = t; row[f"{vn}_table"] = sz; row[f"{vn}_hits"] = c["tt_hits"]
        out["compare"].append(row); print(row)

    print("== Iso-time: deepest lookahead completed within 1.0 s (first move) ==")
    for name, n, k in (("4x4 k=4", 4, 4), ("5x5 k=4", 5, 4)):
        g = Game(n, k)
        r = dict(board=name)
        for lab, fn in (("plain", lambda d: run_plain(g, d)[2]), ("redesign", lambda d: run_new(g, d)[2])):
            best_d, t = 0, 0
            for d in range(1, 12):
                t = fn(d)
                if t > 1.0: break
                best_d = d
            r[lab + "_depth_1s"] = best_d
        out["isotime"].append(r); print(r)
    json.dump(out, open("../results/task7.json", "w"), indent=1)

    c = [x for x in out["compare"] if x["board"] == "4x4 k=4"]
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    ds = [x["d"] for x in c]
    for key, lab in (("plain_evals", "plain minimax"), ("tt_evals", "+ transposition table"),
                     ("ab_order_evals", "alpha-beta + ordering"), ("full_evals", "TT + alpha-beta + ordering")):
        ax.semilogy(ds, [x[key] for x in c], "o-", label=lab)
    ax.set_xlabel("depth d (4x4, k=4)"); ax.set_ylabel("evaluation calls"); ax.set_xticks(ds); ax.legend(fontsize=7)
    plt.tight_layout(); plt.savefig("../figs/fig9_task7.png", dpi=130)
