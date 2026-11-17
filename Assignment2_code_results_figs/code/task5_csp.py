"""Task 5 - Constraint propagation (derived from the 'unsupported value' principle) for exam timetabling."""
import json, random, statistics as st
from collections import deque
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


class CSP:
    """Variables = exams, domains = slots, binary constraints: conflicting exams must differ."""
    def __init__(self, n, edges, domains):
        self.n = n
        self.nb = {i: set() for i in range(n)}
        for a, b in edges:
            self.nb[a].add(b); self.nb[b].add(a)
        self.dom0 = [set(d) for d in domains]


def revise(csp, dom, i, j, st_):
    """Remove from D(i) every value that has no support in D(j)."""
    removed = False
    for a in list(dom[i]):
        supported = False
        for b in dom[j]:
            st_["checks"] += 1
            if a != b:                     # compatibility test c_ij(a,b)
                supported = True
                break
        if not supported:
            dom[i].discard(a); removed = True
    return removed


def ac3(csp, dom, st_, queue=None, trace=None):
    q = deque(queue if queue is not None else [(i, j) for i in range(csp.n) for j in csp.nb[i]])
    inq = set(q)
    while q:
        i, j = q.popleft(); inq.discard((i, j))
        if revise(csp, dom, i, j, st_):
            if trace is not None:
                trace.append([len(d) for d in dom])
            if not dom[i]:
                st_["wipeouts"] += 1
                return False               # domain wipe-out => no solution
            for k in csp.nb[i]:            # neighbours whose support may have relied on removed values
                if k != j and (k, i) not in inq:
                    q.append((k, i)); inq.add((k, i))
    return True


def backtrack(csp, dom, assign, st_, use_ac, order, limit):
    if st_["nodes"] > limit:
        raise TimeoutError
    if len(assign) == csp.n:
        return dict(assign)
    var = order[len(assign)]
    for val in sorted(dom[var]):
        st_["nodes"] += 1
        if use_ac:
            new = [set(d) for d in dom]
            new[var] = {val}
            if ac3(csp, new, st_, [(k, var) for k in csp.nb[var]]):
                assign[var] = val
                r = backtrack(csp, new, assign, st_, True, order, limit)
                if r: return r
                del assign[var]
        else:
            ok = True
            for k in csp.nb[var]:
                if k in assign:
                    st_["checks"] += 1
                    if assign[k] == val:
                        ok = False; break
            if ok:
                assign[var] = val
                r = backtrack(csp, dom, assign, st_, False, order, limit)
                if r: return r
                del assign[var]
    st_["backtracks"] += 1
    return None


def solve(csp, use_ac, limit=300000):
    st_ = dict(nodes=0, backtracks=0, checks=0, wipeouts=0)
    dom = [set(d) for d in csp.dom0]
    order = sorted(range(csp.n), key=lambda v: -len(csp.nb[v]))
    status = "solved"
    try:
        if use_ac and not ac3(csp, dom, st_):
            sol = None
        else:
            sol = backtrack(csp, dom, {}, st_, use_ac, order, limit)
        if sol is None: status = "no solution"
    except TimeoutError:
        sol, status = None, "node limit"
    return sol, status, st_


def random_instance(n, avg_deg, k, seed):
    rng = random.Random(seed)
    p = avg_deg / (n - 1)
    edges = [(a, b) for a in range(n) for b in range(a + 1, n) if rng.random() < p]
    return CSP(n, edges, [set(range(k)) for _ in range(n)])


def shade(dom_sizes_list, titles, fname, k):
    fig, axes = plt.subplots(1, len(titles), figsize=(2.6 * len(titles), 3.2))
    for ax, doms, t in zip(axes, dom_sizes_list, titles):
        M = np.array([[1 if s in d else 0 for s in range(k)] for d in doms])
        ax.imshow(M, cmap="Blues", vmin=0, vmax=1.3, aspect="auto")
        ax.set_title(t, fontsize=8); ax.set_xlabel("slot"); ax.set_xticks(range(k)); ax.set_xticklabels(range(1, k + 1))
        ax.set_yticks(range(len(doms))); ax.set_yticklabels([f"E{i + 1}" for i in range(len(doms))], fontsize=6)
    plt.tight_layout(); plt.savefig(fname, dpi=130)


if __name__ == "__main__":
    out = {}
    # ---- Instance A: path of exams, solved purely by propagation
    k = 3
    edgesA = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
    domsA = [{0}, {0, 1}, {0, 1}, {0, 1}, {0, 1}, {0, 1}, {0, 1}, {0, 1}]
    A = CSP(8, edgesA, domsA)
    dom = [set(d) for d in A.dom0]; s = dict(nodes=0, backtracks=0, checks=0, wipeouts=0); snaps = [[set(d) for d in dom]]
    trace = []
    ac3(A, dom, s, trace=trace)
    print("Instance A (solvable by propagation) domains after AC-3:", [sorted(d) for d in dom], s)
    out["A"] = dict(final=[sorted(d) for d in dom], stats=s, trace=trace)
    # ---- Instance A2: same path, other end fixed to a conflicting slot -> failure detected without search
    domsA2 = [{0}, {0, 1}, {0, 1}, {0, 1}, {0, 1}, {0, 1}, {0, 1}, {0}]
    A2 = CSP(8, edgesA, domsA2)
    dom2 = [set(d) for d in A2.dom0]; s2 = dict(nodes=0, backtracks=0, checks=0, wipeouts=0)
    ok = ac3(A2, dom2, s2)
    print("Instance A2 (failure detected): consistent =", ok, s2)
    out["A2"] = dict(consistent=ok, stats=s2)
    shade([[set(d) for d in A.dom0], dom, [set(d) for d in A2.dom0], dom2],
          ["A: initial", "A: after AC-3 (solved)", "A2: initial", "A2: after AC-3 (wipe-out)"],
          "../figs/fig6_task5_domains.png", 2)

    # ---- Instance B (challenge): K_n with n-1 slots. AC-3 prunes nothing but the problem is unsolvable.
    rowsB = []
    for n in (5, 6, 7, 8, 9):
        edges = [(a, b) for a in range(n) for b in range(a + 1, n)]
        C = CSP(n, edges, [set(range(n - 1)) for _ in range(n)])
        r = {}
        for name, ac in (("BT", False), ("MAC", True)):
            sol, status, stt = solve(C, ac)
            r[name] = dict(status=status, **stt)
        rowsB.append(dict(n=n, **{f"{a}_{b}": v for a, d in r.items() for b, v in d.items()}))
        print("K_n challenge", rowsB[-1])
    out["B"] = rowsB

    # ---- Scaling on random timetables (avg conflicts per exam 4.0, 3 slots... chosen near the hard region)
    rowsS = []
    for n in (10, 15, 20, 25, 30, 35):
        agg = {"BT": [], "MAC": []}
        for seed in range(10):
            C = random_instance(n, 4.0, 3, 500 + seed)
            for name, ac in (("BT", False), ("MAC", True)):
                sol, status, stt = solve(C, ac)
                agg[name].append(dict(status=status, **stt))
        row = dict(n=n)
        for name in agg:
            for key in ("nodes", "backtracks", "checks", "wipeouts"):
                row[f"{name}_{key}"] = st.mean(x[key] for x in agg[name])
            row[f"{name}_limit_hits"] = sum(x["status"] == "node limit" for x in agg[name])
            row[f"{name}_unsat"] = sum(x["status"] == "no solution" for x in agg[name])
        rowsS.append(row)
        print("scaling", row)
    out["S"] = rowsS
    json.dump(out, open("../results/task5.json", "w"), indent=1)

    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    ns = [r["n"] for r in rowsS]
    ax[0].semilogy(ns, [r["BT_nodes"] for r in rowsS], "o-", label="BT")
    ax[0].semilogy(ns, [r["MAC_nodes"] for r in rowsS], "s-", label="BT + AC-3 (MAC)")
    ax[0].set_xlabel("number of exams"); ax[0].set_ylabel("nodes (mean of 10)"); ax[0].legend(fontsize=7)
    ax[1].semilogy(ns, [r["BT_checks"] for r in rowsS], "o-", label="BT")
    ax[1].semilogy(ns, [r["MAC_checks"] for r in rowsS], "s-", label="MAC")
    ax[1].set_xlabel("number of exams"); ax[1].set_ylabel("constraint checks"); ax[1].legend(fontsize=7)
    plt.tight_layout(); plt.savefig("../figs/fig7_task5_scaling.png", dpi=130)
