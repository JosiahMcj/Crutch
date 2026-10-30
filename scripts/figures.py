#!/usr/bin/env python3
"""Figures from data/*.json. Needs matplotlib (the tables need only the stdlib).
Deterministic SVG output, committed alongside the data. Each figure also writes
paper/figures/<name>.values.json, recorded by the same calls that draw the marks.

    python3 scripts/figures.py [--preview DIR]     (DIR gets light, dark, phone-width PNGs)"""
import io, json, math, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as MPath
from matplotlib.text import Text
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
# DejaVu ships with matplotlib, so layout does not depend on this machine's fonts; it is also wider
# than the fallbacks a viewer substitutes, so text kept as text can only get narrower than checked here.
matplotlib.rcParams.update({"svg.hashsalt": "dsh", "svg.fonttype": "none", "font.family": "sans-serif",
                            "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"], "font.size": 10, "hatch.linewidth": 0.8})
ROOT = Path(__file__).resolve().parents[1]; D = ROOT/"data"; OUT = ROOT/"paper"/"figures"; OUT.mkdir(exist_ok=True)
L = lambda n: json.loads((D/f"{n}.json").read_text())
def wilson(k, n, z=1.959964):
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n); h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return (c-h)/d, (c+h)/d
def pct(k, n): return 100*k/n
def solved(rows): return sum(x["solved"] for x in rows)
d1, d2, d3, d4 = L("dsh1"), L("dsh2"), L("dsh3"), L("dsh4")
rungs = [("qwen3_8b","8B"),("qwen3_14b","14B"),("qwen3_32b","32B")]; SESSIONS = ("B1","B2","B3")

# ---------------- design system ----------------
# Width 6.4 in; paper/style.css caps figure height at 2.9 in, and anything taller would be scaled down, shrinking its text.
WIDTH, HEIGHT = 6.4, 2.9
SMALL = 10  # smallest text in any figure, pt; about 8.5 px when a phone shows the figure 390 px wide
BAR, BAR_R = 0.25, 3/72  # bar thickness and data-end radius, in
# Validated categorical slots 1 to 3 (all pairs, both modes). The ceiling takes no hue: it is ink, hollow and
# hatched or dashed, so it can never read as a fourth achievable arm. Aqua is under 3:1 on light, so its marks carry values.
LIGHT = dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", grid="#e1e0d9", axis="#c3c2b7", agent="#2a78d6", single="#eb6834", sampled="#1baf7a")
DARK = dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", grid="#2c2c2a", axis="#383835", agent="#3987e5", single="#d95926", sampled="#199e70")
ARM = {"single": dict(color="single", marker="s", label="Single shot (greedy)"),
       "sampled": dict(color="sampled", marker="D", label="One sampled shot"),
       "agent": dict(color="agent", marker="o", label="Agent"),
       "ceiling": dict(color="ink", marker="^", label="Best of eight samples (oracle ceiling)", ceiling=True),
       "whole_file": dict(color="ink2", marker="v", label="Whole-file agent (no editor)")}  # an agent variant, not one of the four arms

class Figure:
    """One figure: fixed axes, the marks, and the sidecar rows those marks were drawn from."""
    def __init__(self, name, T, sources, xlim, panels=1, top=0.34, bottom=0.62, left=0.62, gap=0.2, xscale="linear", ymax=100):
        self.name, self.T, self.sources, self.rows = name, T, sources, []
        self.fig = plt.figure(figsize=(WIDTH, HEIGHT), facecolor=T["surface"]); self.axes = []
        w = (WIDTH-left-0.15-gap*(panels-1))/panels
        for i in range(panels):
            ax = self.fig.add_axes([(left+i*(w+gap))/WIDTH, bottom/HEIGHT, w/WIDTH, (HEIGHT-top-bottom)/HEIGHT], facecolor=T["surface"])
            ax.set_xscale(xscale); ax.set_xlim(*xlim)
            ax.set_ylim(0, ymax)  # never truncated: every y axis in this file starts at zero (check() enforces it)
            ax.set_axisbelow(True); ax.grid(axis="y", color=T["grid"], lw=0.75); ax.spines[["top","right"]].set_visible(False)
            ax.spines[["left","bottom"]].set_color(T["axis"]); ax.tick_params(colors=T["ink2"], color=T["axis"], labelsize=SMALL, length=3)
            self.axes.append(ax)
    def labels(self, ax, xlabel=None, ylabel=None):
        if xlabel: ax.set_xlabel(xlabel, color=self.T["ink2"], fontsize=10)
        if ylabel: ax.set_ylabel(ylabel, color=self.T["ink2"], fontsize=10)
    def categories(self, ax, ticks, names):
        ax.xaxis.set_major_locator(FixedLocator(ticks)); ax.xaxis.set_major_formatter(FixedFormatter(names)); ax.xaxis.set_minor_locator(NullLocator())
    def dx(self, ax, inches): return inches*(ax.get_xlim()[1]-ax.get_xlim()[0])/(ax.get_position().width*WIDTH)
    def dy(self, ax, inches): return inches*(ax.get_ylim()[1]-ax.get_ylim()[0])/(ax.get_position().height*HEIGHT)
    def record(self, ax, series, x, y, **extra):
        self.rows.append(dict(panel=self.axes.index(ax), series=series, x=x, y=y, **extra))
    def text(self, ax, x, y, s, ha="center", va="bottom", ink="ink", **kw):
        # The surface-coloured box keeps a gridline from striking through a label.
        ax.text(x, y, s, ha=ha, va=va, color=self.T[ink], fontsize=SMALL, clip_on=False, zorder=5, bbox=dict(fc=self.T["surface"], ec="none", pad=0.6), **kw)
    def bar(self, ax, arm, series, cat, x, y, label=None, label_y=None, **extra):
        """A bar from the zero baseline with a rounded data end. Draws nothing at zero."""
        T, A = self.T, ARM[arm]; w = self.dx(ax, BAR); rx = self.dx(ax, BAR_R); ry = min(self.dy(ax, BAR_R), y); l, r = x-w/2, x+w/2
        P = [(l,0),(l,y-ry),(l,y),(l+rx,y),(r-rx,y),(r,y),(r,y-ry),(r,0),(l,0)]
        C = [MPath.MOVETO,MPath.LINETO,MPath.CURVE3,MPath.CURVE3,MPath.LINETO,MPath.CURVE3,MPath.CURVE3,MPath.LINETO,MPath.CLOSEPOLY]
        if y > 0:
            style = dict(facecolor=T["surface"], edgecolor=T["ink"], hatch="////", lw=1) if A.get("ceiling") else dict(facecolor=T[A["color"]], edgecolor="none", lw=0)
            ax.add_patch(PathPatch(MPath(P, C), zorder=2, clip_on=False, **style))
        self.record(ax, series, cat, y, xpos=x, **extra)
        if label is not None: self.text(ax, x, (y if label_y is None else label_y)+self.dy(ax, 0.03), label)
    def point(self, ax, arm, series, cat, x, y, lo=None, hi=None, **extra):
        """A marker, with an interval when bounds are given (the bounds are percent, like y)."""
        T, A = self.T, ARM[arm]; c = T[A["color"]]; ceil = A.get("ceiling")
        yerr = None if lo is None else [[y-lo], [hi-y]]
        ax.errorbar([x], [y], yerr=yerr, color=c, marker=A["marker"], ms=7, mfc=T["surface"] if ceil else c, mec=c if ceil else T["surface"], mew=1.3 if ceil else 1,
                    ls="none", ecolor=c, elinewidth=1.5, capsize=3, capthick=1.5, clip_on=False, zorder=4)
        self.record(ax, series, cat, y, xpos=x, **({} if lo is None else dict(lo=lo, hi=hi)), **extra)
    def key(self, arm, form="bar", label=None):
        T, A = self.T, ARM[arm]; c = T[A["color"]]; ceil = A.get("ceiling"); label = label or A["label"]
        if form == "bar": return Patch(facecolor=T["surface"], edgecolor=T["ink"], hatch="////", lw=1, label=label) if ceil else Patch(facecolor=c, edgecolor="none", label=label)
        return Line2D([], [], color=c, ls="--" if ceil else "-" if form == "line" else "none", lw=2, marker=A["marker"], ms=7, mfc=T["surface"] if ceil else c, mec=c, mew=1.3 if ceil else 0, label=label)
    def legend(self, handles, ncol=None):
        # Always in the band above the axes, so it can never overlap a mark.
        self.fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=ncol or len(handles), frameon=False, fontsize=SMALL,
                        labelcolor=self.T["ink2"], handletextpad=0.5, columnspacing=1.3, borderaxespad=0.15, handlelength=1.6)
    def check(self):
        """Fail the build on the things a redraw can silently break."""
        self.fig.canvas.draw(); rr = self.fig.canvas.get_renderer(); box = self.fig.bbox
        assert self.fig.get_size_inches().tolist() == [WIDTH, HEIGHT], self.name
        for ax in self.axes: assert ax.get_yscale() == "linear" and ax.get_ylim()[0] == 0, (self.name, ax.get_ylim())
        tx = [(t.get_text(), t.get_window_extent(rr)) for t in self.fig.findobj(Text) if t.get_visible() and t.get_text().strip()]
        for t in self.fig.findobj(Text):
            if t.get_text().strip(): assert t.get_fontsize() >= 8, (self.name, t.get_text())
        for s, b in tx: assert b.x0 >= box.x0 and b.x1 <= box.x1 and b.y0 >= box.y0 and b.y1 <= box.y1, (self.name, "clipped", s)
        for i, (s, a) in enumerate(tx):
            for u, b in tx[i+1:]: assert not a.overlaps(b), (self.name, "overlap", s, u)
    def sidecar(self):
        ax_ = [dict(panel=i, xlabel=a.get_xlabel(), ylabel=a.get_ylabel(), xscale=a.get_xscale(), xlim=list(a.get_xlim()), ylim=list(a.get_ylim())) for i, a in enumerate(self.axes)]
        doc = dict(figure=self.name+".svg", sources=self.sources, axes=ax_, plotted=self.rows)
        (OUT/f"{self.name}.values.json").write_text(json.dumps(doc, indent=1, sort_keys=True)+"\n")
    def svg(self):
        # The surface is painted, so the figure is legible on any page; dark mode swaps every colour for its selected dark step.
        rules = "".join(f'[style*="fill: {a}"],[fill="{a}"]{{fill:{b}!important}}[style*="stroke: {a}"]{{stroke:{b}!important}}' for a, b in sorted((LIGHT[k], DARK[k]) for k in LIGHT))
        buf = io.StringIO(); self.fig.savefig(buf, format="svg", metadata={"Date": None})
        (OUT/f"{self.name}.svg").write_text(buf.getvalue().replace("</style>", f"@media screen and (prefers-color-scheme: dark){{{rules}}}</style>", 1))
    def finish(self, preview, write):
        self.check()
        if write: self.svg(); self.sidecar()
        if preview:
            stem = str(Path(preview)/self.name)
            if write: self.fig.savefig(stem+".png", dpi=170); self.fig.savefig(stem+".phone.png", dpi=390/WIDTH)
            else: self.fig.savefig(stem+".dark.png", dpi=170)
        plt.close(self.fig)

# Figure 1: single shot vs the three agent sessions at each scale
def fig1(T, preview, write):
    F = Figure("fig1_scale_ladder", T, ["data/dsh3.json"], (-0.6, 2.5), left=0.86); ax = F.axes[0]
    for i, (r, lbl) in enumerate(rungs):
        R = d3[r]; n = len(R["A"]); a = solved(R["A"]); lo, hi = wilson(a, n)
        F.point(ax, "single", "Single shot (greedy)", lbl, i-0.33, pct(a, n), 100*lo, 100*hi, solved=a, n=n)
        F.text(ax, i-0.33, 100*lo-F.dy(ax, 0.05), f"{a} of {n}", va="top")
        ks = [solved(R[s]) for s in SESSIONS]; lows = []
        for j, k in enumerate(ks):
            lo, hi = wilson(k, n); lows.append(100*lo)
            F.point(ax, "agent", f"Agent session {j+1}", lbl, i+0.03+0.13*j, pct(k, n), 100*lo, 100*hi, solved=k, n=n)
        F.text(ax, i+0.16, min(lows)-F.dy(ax, 0.05), ", ".join(map(str, ks)), va="top")
    F.categories(ax, range(len(rungs)), [l for _, l in rungs]); F.labels(ax, "Model size (billions of parameters)", "Tasks solved (%)\nwith Wilson 95% interval")
    F.legend([F.key("single", "point"), F.key("agent", "point", "Agent, one point per session")]); F.finish(preview, write)
# Figure 2: unbiased pass@k of eight samples against the mean of three agent sessions (ceiling is dashed)
def upk(n, c, k): return 1.0 if n-c < k else 1-math.comb(n-c, k)/math.comb(n, k)
def agent_mean(R): return pct(sum(solved(R[s]) for s in SESSIONS)/len(SESSIONS), len(R["A"]))
def fig2(T, preview, write):
    m = len(d4[rungs[1][0]][0]["per_sample"]); ks = list(range(1, m+1))
    F = Figure("fig2_sampling_ceiling", T, ["data/dsh3.json", "data/dsh4.json"], (0.5, m+0.5), panels=2, top=0.44)
    for ax, (r, lbl) in zip(F.axes, rungs[1:]):
        C = d4[r]; n = len(C); ys = [100*sum(upk(m, sum(1 for x in t["per_sample"] if x), k) for t in C)/n for k in ks]
        ag = agent_mean(d3[r])
        ax.plot(ks, [ag]*m, color=T["agent"], lw=2, zorder=2, clip_on=False); F.record(ax, "Agent, mean of three sessions", [ks[0], ks[-1]], ag, model=lbl)
        ax.plot(ks, ys, color=T["ink"], lw=1.5, ls="--", zorder=3, clip_on=False)
        for k, y in zip(ks, ys): F.point(ax, "ceiling", "Unbiased pass@k (oracle ceiling)", k, k, y, model=lbl)
        ax.plot([ks[-1]], [ag], marker=ARM["agent"]["marker"], ms=7, color=T["agent"], mec=T["surface"], mew=1, zorder=4, clip_on=False)
        F.text(ax, ks[0], ys[0]+F.dy(ax, 0.08), f"{ys[0]:.1f}"); F.text(ax, ks[-1], ys[-1]+F.dy(ax, 0.08), f"{ys[-1]:.1f}")
        F.text(ax, (ks[0]+ks[-1])/2, ys[m//2]+F.dy(ax, 0.1), "oracle ceiling")
        F.text(ax, (ks[0]+ks[-1])/2, ag-F.dy(ax, 0.07), f"Agent mean {ag:.1f}", va="top")
        F.text(ax, (ks[0]+ks[-1])/2, F.dy(ax, 0.12), f"{lbl} model", fontweight="bold"); ax.xaxis.set_major_locator(FixedLocator(ks)); ax.xaxis.set_minor_locator(NullLocator())
        F.labels(ax, "Samples per task, k")
    F.labels(F.axes[0], ylabel="Tasks solved (%)"); F.axes[1].tick_params(labelleft=False)
    F.legend([F.key("ceiling", "line", "Unbiased pass@k (oracle ceiling)"), F.key("agent", "line", "Agent, mean of three sessions")]); F.finish(preview, write)

# Figure 3: every arm at each model size (greedy, one sampled shot, agent sessions, oracle ceiling)
def fig3(T, preview, write):
    F = Figure("fig3_arms_by_scale", T, ["data/dsh3.json", "data/dsh4.json"], (-0.5, 2.5), top=0.66); ax = F.axes[0]
    p = F.dx(ax, BAR+0.17); tick = F.dx(ax, BAR/3)
    for i, (r, lbl) in enumerate(rungs):
        R = d3[r]; n = len(R["A"]); a = solved(R["A"]); ss = [solved(R[s]) for s in SESSIONS]; ag = agent_mean(R); top = max([ag]+[pct(k, n) for k in ss])
        F.bar(ax, "single", "Single shot (greedy)", lbl, i-1.5*p, pct(a, n), f"{pct(a, n):.1f}", solved=a, n=n)
        F.bar(ax, "agent", "Agent, mean of three sessions", lbl, i+0.5*p, ag, f"{ag:.1f}", label_y=top, n=n)
        for j, k in enumerate(ss):
            x = i+0.5*p+tick*(j-1)
            ax.plot([x-tick*0.42, x+tick*0.42], [pct(k, n)]*2, color=T["ink"], lw=1.6, solid_capstyle="butt", zorder=4, clip_on=False)
            F.record(ax, f"Agent session {j+1}", lbl, pct(k, n), xpos=x, solved=k, n=n)
        if r in d4:
            C = d4[r]; c = len(C); s0 = sum(1 for t in C if t["per_sample"][0]); p8 = sum(1 for t in C if any(t["per_sample"]))
            F.bar(ax, "sampled", "One sampled shot (sample 0)", lbl, i-0.5*p, pct(s0, c), f"{pct(s0, c):.1f}", solved=s0, n=c)
            F.bar(ax, "ceiling", "Best of eight samples (oracle ceiling)", lbl, i+1.5*p, pct(p8, c), f"ceiling\n{pct(p8, c):.1f}", solved=p8, n=c)
        else:
            for x, series in ((i-0.5*p, "One sampled shot (sample 0)"), (i+1.5*p, "Best of eight samples (oracle ceiling)")):
                F.text(ax, x, F.dy(ax, 0.05), "not run", ink="ink2", rotation=90); F.record(ax, series, lbl, None, xpos=x, note="not run at this size")
    F.categories(ax, range(len(rungs)), [l for _, l in rungs]); F.labels(ax, "Model size (billions of parameters)", "Tasks solved (%)")
    sess = Line2D([], [], color=T["ink"], lw=1.6, label="Three agent sessions")
    F.legend([F.key("single"), F.key("sampled"), F.key("agent", label="Agent, mean"), sess, F.key("ceiling", label="Oracle ceiling (best of eight)")], ncol=3); F.finish(preview, write)

# Figure 4: editing ablation (DSH-2). All three measures count the same episodes, so they share one axis, 0 to the episode count.
def fig4(T, preview, write):
    n = len(d2); F = Figure("fig4_editing_ablation", T, ["data/dsh2.json"], (-0.5, 2.5), ymax=n, top=0.42); ax = F.axes[0]; p = F.dx(ax, BAR+0.2)
    def cnt(k, f): return sum(1 for r in d2 if f(r[k]))
    # Same predicates as scripts/tables.py: syntax_ok is True, False or None, and only False counts as invalid.
    panels = [("Tasks solved", lambda b: b["solved"]), ("Syntax-invalid files", lambda b: b["syntax_ok"] is False), ("Wall-cap hits", lambda b: b["cap_hit"])]
    for i, (title, f) in enumerate(panels):
        F.bar(ax, "agent", "Editor", title, i-p/2, cnt("b1", f), str(cnt("b1", f)), n=n)
        F.bar(ax, "whole_file", "Whole-file agent", title, i+p/2, cnt("b2", f), str(cnt("b2", f)), n=n)
    ax.yaxis.set_major_locator(FixedLocator([n*q/4 for q in range(5)])); ax.yaxis.set_minor_locator(NullLocator())
    F.categories(ax, range(len(panels)), [t for t, _ in panels]); F.labels(ax, "Measure", f"Count, of {n} episodes per arm")
    F.legend([F.key("agent", label="Editor (agent as configured)"), F.key("whole_file")]); F.finish(preview, write)

# Figure 5: cost against solve rate
def fig5(T, preview, write):
    F = Figure("fig5_cost_vs_solved", T, ["data/dsh3.json", "data/dsh4.json"], (1, 300), xscale="log"); ax = F.axes[0]  # the one exception to zero-based axes: log time cannot include zero; the y axis still runs 0 to 100
    off = {("single","8B"): (0,-15), ("single","14B"): (0,8), ("single","32B"): (0,-15), ("agent","8B"): (11,-4), ("agent","14B"): (-5,-15), ("agent","32B"): (18,-7), ("ceiling","14B"): (0,8), ("ceiling","32B"): (0,8)}
    pts = {"single": [], "agent": [], "ceiling": []}
    for r, lbl in rungs:
        R = d3[r]; n = len(R["A"])
        pts["single"].append((lbl, sum(x["wall_s"] or 0 for x in R["A"])/n, pct(solved(R["A"]), n)))
        pts["agent"].append((lbl, sum(x["wall_s"] or 0 for s in SESSIONS for x in R[s])/(len(SESSIONS)*n), agent_mean(R)))
        if r in d4:
            C = d4[r]; pts["ceiling"].append((lbl, sum(t["wall_s"] for t in C)/len(C), pct(sum(1 for t in C if any(t["per_sample"])), len(C))))
    for arm, ps in pts.items():
        ax.plot([q[1] for q in ps], [q[2] for q in ps], color=T[ARM[arm]["color"]], lw=1, ls="--" if ARM[arm].get("ceiling") else "-", zorder=2)
        for lbl, x, y in ps:
            F.point(ax, arm, ARM[arm]["label"], lbl, x, y, wall_s=x)
            ax.annotate(lbl, (x, y), xytext=off[arm, lbl], textcoords="offset points", ha="center", color=T["ink"], fontsize=SMALL, zorder=5)
    F.text(ax, pts["ceiling"][-1][1]*1.2, pts["ceiling"][-1][2], "oracle ceiling", ha="left", va="center")
    ax.xaxis.set_major_locator(FixedLocator([1,3,10,30,100,300])); ax.xaxis.set_major_formatter(FixedFormatter(["1","3","10","30","100","300"])); ax.xaxis.set_minor_locator(NullLocator())
    F.labels(ax, "Mean wall time per task (s, log scale)", "Tasks solved (%)")
    F.legend([F.key("single", "line", "Single shot"), F.key("agent", "line", "Agent (mean)"), F.key("ceiling", "line", "Eight samples (oracle ceiling)")]); F.finish(preview, write)

# Figure 6: DSH-1 by task bank
def fig6(T, preview, write):
    banks = sorted({r["bank"] for r in d1}); names = {"blind_holdout": "Algorithmic", "mbpp_blind": "MBPP", "physics_scale_blind": "Physics"}
    F = Figure("fig6_dsh1_banks", T, ["data/dsh1.json"], (-0.5, len(banks)-0.5)); ax = F.axes[0]; p = F.dx(ax, BAR+0.2); ticks = []
    for i, b in enumerate(banks):
        s = [r for r in d1 if r["bank"] == b]; n = len(s); a = sum(r["a"]["solved"] for r in s); g = sum(r["b"]["solved"] for r in s); ticks.append(f"{names[b]} (n={n})")
        F.bar(ax, "single", "Single shot", names[b], i-p/2, pct(a, n), f"{a}/{n}", solved=a, n=n)
        F.bar(ax, "agent", "Agent", names[b], i+p/2, pct(g, n), f"{g}/{n}", solved=g, n=n)
    F.categories(ax, range(len(banks)), ticks); F.labels(ax, "Task bank (n = tasks)", "Tasks solved (%)")
    F.legend([F.key("single", label="Single shot"), F.key("agent")]); F.finish(preview, write)

if __name__ == "__main__":
    preview = sys.argv[sys.argv.index("--preview")+1] if "--preview" in sys.argv else None
    if preview: Path(preview).mkdir(parents=True, exist_ok=True)
    for build in (fig1, fig2, fig3, fig4, fig5, fig6):
        build(LIGHT, preview, True)
        if preview: build(DARK, preview, False)
    print("figures ->", OUT)
