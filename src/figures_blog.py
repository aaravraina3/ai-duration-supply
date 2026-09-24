"""Three figures for the writeup that the main pipeline does not produce:
the recovery experiment, endpoint sensitivity, and leave-one-out."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import PROC, FIG
import curve as C, concession as K, abnormal as A, recovery as RC

plt.rcParams.update({"figure.dpi": 140, "font.size": 9, "axes.grid": True,
                     "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED, GREY, GREEN = "#1f4e79", "#c0392b", "#7f8c8d", "#27ae60"


def fig8_recovery():
    """Superseded by figures_fix.fig8, which fixes the legend overlap (review m6)."""
    import figures_fix; return figures_fix.fig8()


def _fig8_recovery_original():
    ev = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    z = C.load_gsw(start="2024-01-01"); V, _ = K.loadings(z)
    lab, truth, raw, sm = [], [], [], []
    for _, e in ev.iterrows():
        tw = K.tenor_weights(tr, e.issuer, e.announce)
        t, r, s = RC.experiment(sorted(tw), tw, V)
        lab.append(f"{e.issuer}\n{e.announce.date()}"); truth.append(t); raw.append(r); sm.append(s)
    x = np.arange(len(lab)); w = 0.27
    fig, ax = plt.subplots(figsize=(8.2, 3.4))
    ax.bar(x - w, truth, w, label="injected bump (truth)", color=GREY)
    ax.bar(x, raw, w, label="recovered, 3-PC residualisation only", color=BLUE)
    ax.bar(x + w, sm, w, label="recovered, after GSW's Svensson re-fit", color=RED)
    ax.axhline(0, color="k", lw=.8)
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=6.5)
    ax.set_ylabel("bp"); ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.set_title("A known 5bp localised bump, put in and taken back out")
    fig.tight_layout(); fig.savefig(FIG / "fig8_recovery.png"); plt.close(fig)
    print("fig8", np.mean(np.array(raw) / np.array(truth)), np.mean(np.array(sm) / np.array(truth)))


def fig9_endpoints():
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    s10, tp = fred.DGS10.dropna(), acm.ACMTP10.dropna()
    at = lambda s, d: s[s.index <= pd.Timestamp(d)].iloc[-1]
    starts = ["2025-12-31", "2026-01-02", "2026-01-15", "2026-02-02", "2026-02-27"]
    ends = ["2026-06-30", "2026-07-31", "2026-08-31", "2026-09-11", "2026-09-15"]
    M = np.full((len(starts), len(ends)), np.nan)
    for i, st in enumerate(starts):
        for j, en in enumerate(ends):
            M[i, j] = (at(tp, en) - at(tp, st)) * 100
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    v = np.nanmax(np.abs(M))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-v, vmax=v, aspect="auto")
    ax.set_xticks(range(len(ends))); ax.set_xticklabels(ends, rotation=30, ha="right", fontsize=7)
    ax.set_yticks(range(len(starts))); ax.set_yticklabels(starts, fontsize=7)
    for i in range(len(starts)):
        for j in range(len(ends)):
            ax.text(j, i, f"{M[i,j]:+.0f}", ha="center", va="center", fontsize=7.5,
                    color="k" if abs(M[i, j]) < v * .55 else "w")
    ax.set_title("2026 change in the ACM 10Y term premium (bp), by endpoint")
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=.85, label="bp")
    fig.tight_layout(); fig.savefig(FIG / "fig9_endpoints.png"); plt.close(fig)
    print("fig9 range", np.nanmin(M), np.nanmax(M), "pos", int((M > 0).sum()), "of", M.size)


def fig10_loo():
    ev = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    df, tn = A.panel(); W = A.build_windows(df, tn)
    res, _, _, _ = A.abnormal(ev, tr, W, verbose=False)
    base = A.agg(res)["mean"]
    labs, vals = [], []
    for i in range(len(ev)):
        sub = ev.drop(ev.index[i]).reset_index(drop=True)
        r2, _, _, _ = A.abnormal(sub, tr, W, verbose=False)
        labs.append(f"{ev.issuer[i]} {ev.announce[i].date()}")
        vals.append(A.agg(r2)["mean"])
    o = np.argsort(vals)
    labs = [labs[i] for i in o]; vals = [vals[i] for i in o]
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    cols = [RED if v < 0 else BLUE for v in vals]
    ax.barh(range(len(vals)), vals, color=cols)
    ax.axvline(base, color="k", ls="--", lw=1, label=f"all 7 events: {base:+.2f} bp")
    ax.axvline(0, color="k", lw=.8)
    ax.set_yticks(range(len(labs))); ax.set_yticklabels(labs, fontsize=7)
    ax.set_xlabel("X with that event dropped (bp)")
    ax.set_title("Leave-one-out: X is one observation")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / "fig10_loo.png"); plt.close(fig)
    print("fig10 range", min(vals), max(vals))


if __name__ == "__main__":
    fig8_recovery(); fig9_endpoints(); fig10_loo()
