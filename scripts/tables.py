#!/usr/bin/env python3
"""Build every results table from data/*.json (stdlib only). Writes
paper/tables.json: {name: markdown}. Nothing in the paper is typed by hand."""
import json, math
from pathlib import Path
D = Path(__file__).resolve().parents[1] / "data"
L = lambda n: json.loads((D/f"{n}.json").read_text())

def wilson(k, n, z=1.959964):
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (c-h)/d, (c+h)/d
def sign_p(w, n):
    if n == 0: return 1.0
    return min(1.0, 2*sum(math.comb(n,k) for k in range(min(w,n-w)+1))/2**n)
def fp(p): return "<0.0001" if p < 1e-4 else f"{p:.4f}" if p < 0.1 else f"{p:.2f}"
def ci(k, n): lo, hi = wilson(k, n); return f"{k}/{n} ({100*k/n:.1f}%, [{100*lo:.1f}, {100*hi:.1f}])"
def disc(x, y):  # x,y: dict task->bool. returns (x_only, y_only)
    t = x.keys() & y.keys()
    return sum(1 for k in t if x[k] and not y[k]), sum(1 for k in t if y[k] and not x[k])
def md(head, rows):
    return "\n".join(["| "+" | ".join(head)+" |", "|"+"|".join("---" for _ in head)+"|"]+["| "+" | ".join(map(str,r))+" |" for r in rows])
T = {}

# ---- DSH-1
d1 = L("dsh1"); n = len(d1)
A = {r["task_id"]: r["a"]["solved"] for r in d1}; B = {r["task_id"]: r["b"]["solved"] for r in d1}
ao, bo = disc(A, B)
T["dsh1_main"] = md(["Arm","Solved (rate, Wilson 95% CI)","Mean wall time (s)"],
  [["A: single shot", ci(sum(A.values()), n), f"{sum(r['a']['wall_s'] for r in d1)/n:.0f}"],
   ["B: agent", ci(sum(B.values()), n), f"{sum(r['b']['wall_s'] for r in d1)/n:.0f}"]]) + \
  f"\n\nDiscordant pairs: {ao} A-only, {bo} B-only (both solved {sum(1 for k in A if A[k] and B[k])}, neither {sum(1 for k in A if not A[k] and not B[k])}). Exact two-sided sign test p = {fp(sign_p(bo, ao+bo))}."
rows = []
for bank in sorted({r["bank"] for r in d1}):
    s = [r for r in d1 if r["bank"] == bank]
    x = {r["task_id"]: r["a"]["solved"] for r in s}; y = {r["task_id"]: r["b"]["solved"] for r in s}
    a_, b_ = disc(x, y); rows.append([{'blind_holdout': 'Algorithmic', 'mbpp_blind': 'MBPP', 'physics_scale_blind': 'Physics'}.get(bank, bank), len(s), sum(x.values()), sum(y.values()), a_, b_])
T["dsh1_banks"] = md(["Bank","n","A solved","B solved","A-only","B-only"], rows)
cap = [r for r in d1 if r["b"]["cap_hit"]]; capl = [r for r in cap if not r["b"]["solved"]]
capl_a = [r for r in capl if A[r["task_id"]]]
k = len(capl_a)
sens = [["As measured", f"{ao} : {bo}", fp(sign_p(bo, ao+bo))],
        [f"Grant all {k} capped losses on tasks A solved", f"{ao-k} : {bo}", fp(sign_p(bo, ao-k+bo))],
        [f"...and all {len(capl)-k} capped losses A also failed", f"{ao-k} : {bo+len(capl)-k}", fp(sign_p(bo+len(capl)-k, ao-k+bo+len(capl)-k))]]
T["dsh1_sens"] = md(["Assumption","Discordance (A-only : B-only)","Exact p"], sens) + f"\n\n{len(cap)} of {n} agent episodes reached the 600 s wall cap, and {len(cap)-len(capl)} of them still solved the task."

# ---- DSH-2
d2 = L("dsh2"); n2 = len(d2)
x = {r["task_id"]: r["b1"]["solved"] for r in d2}; y = {r["task_id"]: r["b2"]["solved"] for r in d2}
x_, y_ = disc(x, y)
def cnt(k, f): return sum(1 for r in d2 if f(r[k]))
T["dsh2_main"] = md(["Arm","Solved (rate, Wilson 95% CI)","Syntax-invalid files","Wall-cap hits","Tool errors per episode"],
  [["B1: editor tool available", ci(sum(x.values()), n2), cnt("b1", lambda b: b["syntax_ok"] is False), cnt("b1", lambda b: b["cap_hit"]), f"{sum(r['b1']['tool_errors'] or 0 for r in d2)/n2:.1f}"],
   ["B2: bash only, whole-file writes", ci(sum(y.values()), n2), cnt("b2", lambda b: b["syntax_ok"] is False), cnt("b2", lambda b: b["cap_hit"]), f"{sum(r['b2']['tool_errors'] or 0 for r in d2)/n2:.1f}"]]) + \
  f"\n\nDiscordant pairs: {y_} B2-only, {x_} B1-only. Exact two-sided sign test p = {fp(sign_p(y_, x_+y_))}. The test has {x_+y_} informative pairs."
d1b = {r["task_id"]: r["b"]["solved"] for r in d1}; ar = {r["task_id"]: r["solved"] for r in L("dsh2_armA_replication")}
d1a = {r["task_id"]: r["a"]["solved"] for r in d1}
tk = [t for t in x if t in d1b and t in ar]
f2p = sum(1 for t in tk if x[t] and not d1b[t]); p2f = sum(1 for t in tk if d1b[t] and not x[t])
af = sum(1 for t in tk if ar[t] != d1a[t])
T["dsh2_repl"] = md(["Arm","Session 1 (DSH-1)","Session 2 (DSH-2)","Tasks that changed outcome"],
  [["Agent (identical configuration)", f"{sum(d1b[t] for t in tk)}/{len(tk)}", f"{sum(x[t] for t in tk)}/{len(tk)}", f"{f2p} fail to pass, {p2f} pass to fail"],
   ["Single shot, greedy", f"{sum(d1a[t] for t in tk)}/{len(tk)}", f"{sum(ar[t] for t in tk)}/{len(tk)}", f"{af} of {len(tk)}"]]) + \
  f"\n\nSign test on the agent's flips: p = {fp(sign_p(p2f, f2p+p2f))}."

# ---- DSH-3
d3 = L("dsh3"); lad = []; cmp_rows = []; cost = []
for rung, lbl in (("qwen3_8b","8B"),("qwen3_14b","14B"),("qwen3_32b","32B")):
    R = d3[rung]; a = {r["task_id"]: r["solved"] for r in R["A"]}; N = len(a)
    for s in (1,2,3):
        b = {r["task_id"]: r["solved"] for r in R[f"B{s}"]}; ao, bo = disc(a, b)
        cmp_rows.append([lbl, f"S{s}", ci(sum(b.values()), N), sum(a.values())-sum(b.values()), f"{ao} : {bo}", fp(sign_p(bo, ao+bo))])
    bs = [sum(r["solved"] for r in R[f"B{s}"]) for s in (1,2,3)]
    capc = [sum(1 for r in R[f"B{s}"] if r["cap_hit"]) for s in (1,2,3)]
    syn = [sum(1 for r in R[f"B{s}"] if r["syntax_ok"] is False) for s in (1,2,3)]
    st = sum(r["steps"] or 0 for s in (1,2,3) for r in R[f"B{s}"])/(3*N); tk_ = sum(r["out_tokens"] or 0 for s in (1,2,3) for r in R[f"B{s}"])/(3*N)
    wl = sum(r["wall_s"] or 0 for s in (1,2,3) for r in R[f"B{s}"])/(3*N); wa = sum(r["wall_s"] or 0 for r in R["A"])/N
    lad.append([lbl, ci(sum(a.values()), N), ", ".join(map(str, bs)), f"{sum(sum(a.values())-v for v in bs)/3:+.1f}"])
    cost.append([lbl, ", ".join(map(str, syn)), ", ".join(map(str, capc)), f"{st:.1f}", f"{tk_:.0f}", f"{wa:.1f}", f"{wl:.1f}"])
T["dsh3_ladder"] = md(["Model","Single shot (greedy)","Agent, solved per session","Mean gap (A minus agent)"], lad)
T["dsh3_sessions"] = md(["Model","Session","Agent solved (rate, 95% CI)","Gap","Discordant (A-only : agent-only)","Exact p"], cmp_rows)
T["dsh3_mech"] = md(["Model","Syntax-invalid files (per session)","Wall-cap hits (per session)","Mean steps","Mean output tokens","Single-shot wall (s)","Agent wall (s)"], cost)
aud = []
for rung, lbl in (("qwen3_8b","8B"),("qwen3_14b","14B"),("qwen3_32b","32B")):
    R = d3[rung]; ids = [r["task_id"] for r in R["A"]]
    m = {k: {r["task_id"]: r["solved"] for r in R[k]} for k in ("A","B1","B2","B3")}
    sat = sum(1 for t in ids if all(m[k][t] for k in m)); dead = sum(1 for t in ids if not any(m[k][t] for k in m))
    aud.append([lbl, sat, dead, len(ids)-sat-dead])
T["dsh3_audit"] = md(["Model","All four arms solve","No arm solves","Informative"], aud)

# ---- DSH-4
d4 = L("dsh4"); rows4 = []; ceil = []; reach = []; cst = []
for rung, lbl in (("qwen3_14b","14B"),("qwen3_32b","32B")):
    C = {r["task_id"]: r for r in d4[rung]}; N = len(C); R = d3[rung]
    a = {r["task_id"]: r["solved"] for r in R["A"]}; s0 = {t: bool(C[t]["per_sample"][0]) for t in C}
    pk = {t: any(C[t]["per_sample"]) for t in C}
    for s in (1,2,3):
        b = {r["task_id"]: r["solved"] for r in R[f"B{s}"]}; so, bo = disc(s0, b)
        rows4.append([lbl, f"S{s}", ci(sum(s0.values()), N), ci(sum(b.values()), N), f"{so} : {bo}", fp(sign_p(bo, so+bo))])
    def upk(n_, c_, k_): return 1.0 if n_-c_ < k_ else 1-math.comb(n_-c_, k_)/math.comb(n_, k_)
    ceil.append([lbl]+[f"{sum(upk(8, sum(1 for x in C[t]['per_sample'] if x), k) for t in C):.1f}" for k in range(1,9)])
    b1 = {r["task_id"]: r["solved"] for r in R["B1"]}; bany = {t: any(r["solved"] for r in [ {x["task_id"]: x for x in R[f"B{s}"]}[t] for s in (1,2,3)]) for t in C}
    aonly_vs_pk = [sum(1 for t in C if {r["task_id"]: r["solved"] for r in R[f"B{s}"]}[t] and not pk[t]) for s in (1,2,3)]
    reach.append([lbl, ", ".join(map(str, aonly_vs_pk)), sum(1 for t in C if a[t] or pk[t]), sum(pk.values())])
    wc = sum(C[t]["wall_s"] for t in C)/N; wa = sum(r["wall_s"] or 0 for r in R["A"])/N
    wl = sum(r["wall_s"] or 0 for s in (1,2,3) for r in R[f"B{s}"])/(3*N)
    cst.append([lbl, f"{wa:.1f}", f"{wc:.1f}", f"{wl:.1f}", f"{wl/max(wa,1e-9):.1f}"])
T["dsh4_primary"] = md(["Model","Session","One sampled shot","Agent","Discordant (shot-only : agent-only)","Exact p"], rows4)
T["dsh4_ceiling"] = md(["Model"]+[f"k={k}" for k in range(1,9)], ceil)
T["dsh4_reach"] = md(["Model","Agent-only tasks vs 8 samples (per session)","Single shot or 8 samples","8 samples (ceiling)"], reach)
T["dsh4_cost"] = md(["Model","Single shot wall (s)","Eight samples wall (s)","Agent wall (s)","Agent / single shot"], cst)

out = Path(__file__).resolve().parents[1]/"paper"/"tables.json"
out.write_text(json.dumps(T, indent=1)); print("tables:", len(T), "->", out)
