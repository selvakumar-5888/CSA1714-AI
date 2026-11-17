"""Task 3 - Behaviour of alpha-beta pruning under different move orderings."""
import json, random, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# A tree node is either an int (leaf) or a list of child nodes.

def build(b, d, rng, lo=1, hi=10 ** 6):
    if d == 0:
        return rng.randint(lo, hi)
    return [build(b, d - 1, rng, lo, hi) for _ in range(b)]


def engineered_no_cutoff(b, d, M=None):
    """Leaf value = sum_k s_k * M^(d-k) * idx_k  (s_k=+1 at levels where MAX moves, -1 where MIN moves).
    Children of a MAX node therefore have strictly increasing values and children of a MIN node strictly
    decreasing values, consistently with every ancestor window, so the best move is always searched LAST."""
    M = M or (b + 1)
    base = M ** (d + 1) * b
    def rec(level, acc):
        if level == d:
            return base + acc
        sign = 1 if level % 2 == 0 else -1
        return [rec(level + 1, acc + sign * (M ** (d - level)) * i) for i in range(b)]
    return rec(0, 0)


def value(node, maxim):
    if isinstance(node, int):
        return node
    vals = [value(c, not maxim) for c in node]
    return max(vals) if maxim else min(vals)


def reorder(node, maxim, best_first):
    """Sort children at every node by their minimax value.
    best_first=True  -> best move for the player to move first (ideal ordering)
    best_first=False -> worst move first (adversarial ordering)"""
    if isinstance(node, int):
        return node
    kids = [reorder(c, not maxim, best_first) for c in node]
    kids.sort(key=lambda c: value(c, not maxim), reverse=(maxim == best_first))
    return kids


def minimax(node, maxim, ctr):
    ctr["nodes"] += 1
    if isinstance(node, int):
        ctr["leaves"] += 1
        return node
    best = -float("inf") if maxim else float("inf")
    for c in node:
        v = minimax(c, not maxim, ctr)
        best = max(best, v) if maxim else min(best, v)
    return best


def alphabeta(node, maxim, alpha, beta, ctr):
    ctr["nodes"] += 1
    if isinstance(node, int):
        ctr["leaves"] += 1
        return node
    if maxim:
        best = -float("inf")
        for c in node:
            best = max(best, alphabeta(c, False, alpha, beta, ctr))
            alpha = max(alpha, best)
            if alpha >= beta:
                ctr["cutoffs"] += 1
                break
        return best
    best = float("inf")
    for c in node:
        best = min(best, alphabeta(c, True, alpha, beta, ctr))
        beta = min(beta, best)
        if alpha >= beta:
            ctr["cutoffs"] += 1
            break
    return best


def run(tree):
    m = dict(nodes=0, leaves=0)
    vm = minimax(tree, True, m)
    a = dict(nodes=0, leaves=0, cutoffs=0)
    va = alphabeta(tree, True, -float("inf"), float("inf"), a)
    assert vm == va
    return m, a


# ------------------------------------------------ predictions (written BEFORE running)
def total_nodes_full(b, d):
    return sum(b ** k for k in range(d + 1))


def critical_tree_counts(b, d):
    """Knuth-Moore minimal tree. Type1: all b children (first type1, rest type2).
    Type2 (cut node): exactly 1 child (type3).  Type3 (all node): all b children (type2)."""
    memo = {}

    def f(t, depth):
        if depth == 0:
            return (1, 1)  # nodes, leaves
        if (t, depth) in memo:
            return memo[(t, depth)]
        if t == 1:
            parts = [f(1, depth - 1)] + [f(2, depth - 1)] * (b - 1)
        elif t == 2:
            parts = [f(3, depth - 1)]
        else:
            parts = [f(2, depth - 1)] * b
        r = (1 + sum(p[0] for p in parts), sum(p[1] for p in parts))
        memo[(t, depth)] = r
        return r
    return f(1, d)


if __name__ == "__main__":
    out = {"predictions": {}, "results": [], "growth": []}
    b, d = 4, 6
    pn_best, pl_best = critical_tree_counts(b, d)
    pn_worst = total_nodes_full(b, d)
    pl_rand = round(b ** (0.75 * d))
    print(f"PREDICTIONS (b={b}, d={d}) - computed before any experiment")
    print(f"  best-ordered   : nodes = {pn_best}, leaves = {pl_best}  (Knuth-Moore b^ceil(d/2)+b^floor(d/2)-1 = {b**3 + b**3 - 1})")
    print(f"  worst-ordered  : nodes = {pn_worst}, leaves = {b**d}, cutoffs = 0")
    print(f"  random order   : leaves ~ b^(3d/4) = {pl_rand} (range between best {pl_best} and worst {b**d})")
    out["predictions"] = dict(b=b, d=d, best_nodes=pn_best, best_leaves=pl_best, worst_nodes=pn_worst,
                              worst_leaves=b ** d, random_leaves=pl_rand)

    rng = random.Random(7)
    base = build(b, d, rng)
    trees = {
        "T1 best-ordered (many cutoffs)": reorder(base, True, True),
        "T2 engineered worst case (no cutoffs)": engineered_no_cutoff(b, d),
        "T2b locally worst-ordered (random leaves)": reorder(base, True, False),
        "T3 random order (30 trees, mean)": None,
        "T4 all leaves equal": build(b, d, rng, 5, 5),
    }
    for name, t in trees.items():
        if t is None:
            ms, as_ = [], []
            for s in range(30):
                m, a = run(build(b, d, random.Random(100 + s)))
                ms.append(m); as_.append(a)
            m = dict(nodes=st.mean(x["nodes"] for x in ms), leaves=st.mean(x["leaves"] for x in ms))
            a = {k: st.mean(x[k] for x in as_) for k in as_[0]}
            a["leaves_min"] = min(x["leaves"] for x in as_); a["leaves_max"] = max(x["leaves"] for x in as_)
        else:
            m, a = run(t)
        out["results"].append(dict(tree=name, minimax_nodes=m["nodes"], ab_nodes=a["nodes"], ab_leaves=a["leaves"],
                                   cutoffs=a["cutoffs"], saving=1 - a["nodes"] / m["nodes"]))
        print(f"{name:36s} minimax nodes={m['nodes']:.0f}  AB nodes={a['nodes']:.1f} leaves={a['leaves']:.1f} "
              f"cutoffs={a['cutoffs']:.1f}  saved={(1 - a['nodes'] / m['nodes']) * 100:.1f}%")

    # growth with depth (b=4)
    for dd in (4, 6, 8):
        r = random.Random(dd)
        base = build(4, dd, r)
        bt, wt = reorder(base, True, True), engineered_no_cutoff(4, dd)
        row = dict(d=dd, full=total_nodes_full(4, dd), pred_best_nodes=critical_tree_counts(4, dd)[0])
        for nm, t in (("best", bt), ("worst", wt), ("random", base)):
            _, a = run(t)
            row[nm + "_nodes"] = a["nodes"]; row[nm + "_cutoffs"] = a["cutoffs"]
        out["growth"].append(row)
        print("growth", row)
    # growth with branching (d=6)
    for bb in (2, 3, 5):
        r = random.Random(bb)
        base = build(bb, 6, r)
        bt, wt = reorder(base, True, True), engineered_no_cutoff(bb, 6)
        row = dict(b=bb, full=total_nodes_full(bb, 6), pred_best_nodes=critical_tree_counts(bb, 6)[0])
        for nm, t in (("best", bt), ("worst", wt), ("random", base)):
            _, a = run(t)
            row[nm + "_nodes"] = a["nodes"]
        out["growth"].append(row)
        print("growth-b", row)
    json.dump(out, open("../results/task3.json", "w"), indent=1)

    gd = [g for g in out["growth"] if "d" in g]
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    ax.semilogy([g["d"] for g in gd], [g["full"] for g in gd], "k--o", label="minimax / worst-order")
    ax.semilogy([g["d"] for g in gd], [g["random_nodes"] for g in gd], "b-s", label="alpha-beta random order")
    ax.semilogy([g["d"] for g in gd], [g["best_nodes"] for g in gd], "g-^", label="alpha-beta best order")
    ax.set_xlabel("depth d (b = 4)"); ax.set_ylabel("nodes visited"); ax.legend(fontsize=7)
    plt.tight_layout(); plt.savefig("../figs/fig4_task3.png", dpi=130)
