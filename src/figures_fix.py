"""Figures regenerated after the adversarial review.

fig8   recovery experiment, legend moved off the bars (m6)
fig11  curve-segment responses on OBSERVED CMT forwards, replacing the GSW version
       whose 20y10y result was a Svensson artifact (F1)
fig12  the artifact itself: R2 with the cash 10Y, GSW vs CMT, per segment
fig15  timing-matched placebo against the uniform placebo (M1)
fig16  on-the-run spread response, the new flow test
"""
import numpy as np, pandas as pd, statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import PROC, FIG
import localproj as L, hedgeflow as H

plt.rcParams.update({"figure.dpi": 140, "font.size": 9, "axes.grid": True,
                     "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED, GREY, GREEN = "#1f4e79", "#c0392b", "#7f8c8d", "#27ae60"


def fig8():
    import curve as C, concession as K, recovery as RC
    ev = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    z = C.load_gsw(start="2024-01-01"); V, _ = K.loadings(z)
    lab, tru, raw, sm_ = [], [], [], []
    for _, e in ev.iterrows():
        tw = K.tenor_weights(tr, e.issuer, e.announce)
        t, r, s = RC.experiment(sorted(tw), tw, V)
        lab.append(f"{e.issuer}\n{e.announce.date()}"); tru.append(t); raw.append(r); sm_.append(s)
    x = np.arange(len(lab)); w = .27
    fig, ax = plt.subplots(figsize=(8.2, 3.6))
    ax.bar(x - w, tru, w, label="injected bump (truth)", color=GREY)
    ax.bar(x, raw, w, label="recovered, 3-PC residualisation only", color=BLUE)
    ax.bar(x + w, sm_, w, label="recovered, after GSW's Svensson re-fit", color=RED)
    ax.axhline(0, color="k", lw=.8)
    ax.set_xticks(x); ax.set_xticklabels(lab, fontsize=6.5); ax.set_ylabel("bp")
    ax.set_ylim(min(sm_) - 1.2, max(tru) + 2.4)
    ax.legend(frameon=False, fontsize=7.5, loc="upper center", ncol=3, bbox_to_anchor=(.5, 1.0))
    ax.set_title("A known 5bp localised bump, put in and taken back out", pad=16)
    fig.tight_layout(); fig.savefig(FIG / "fig8_recovery.png"); plt.close(fig)


def fig11_12():
    df = H.panel()
    ai = L.shocks(); ai = ai[ai.index.isin(df.index)]
    bbd = pd.read_csv(PROC / "buybacks_daily.csv", parse_dates=["date"]).set_index("date")
    bb = bbd.bb_long[bbd.bb_long > 0]
    segs = [("spot10", "10Y spot"), ("f5y5y", "5y5y"), ("f10y10y", "10y10y"), ("f20y10y", "20y10y")]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4))
    for ax, (shock, name, col) in zip(axes, [(ai, "AI corporate issuance (adds duration)", BLUE),
                                             (bb, "Treasury buybacks (removes duration)", RED)]):
        b, se = [], []
        for key, _ in segs:
            r = H.lp_row(df, shock, key, 0); b.append(r.b); se.append(r.se)
        x = np.arange(len(segs))
        ax.bar(x, b, .6, color=col, alpha=.9)
        ax.errorbar(x, b, yerr=1.96 * np.array(se), fmt="none", ecolor="k", lw=1, capsize=3)
        ax.axhline(0, color="k", lw=.8)
        ax.set_xticks(x); ax.set_xticklabels([l for _, l in segs], fontsize=8)
        ax.set_title(name, fontsize=9)
    axes[0].set_ylabel("bp per $bn 10y-equiv, day 0")
    fig.suptitle("Response by curve segment, forwards built from observed CMT points", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig11_channels.png"); plt.close(fig)

    d10 = df.spot10.diff()
    def r2(col):
        y = df[col].diff(); ok = y.notna() & d10.notna()
        return sm.OLS(y[ok], sm.add_constant(d10[ok])).fit().rsquared
    pairs = [("10y10y", "gsw_f10y10y", "f10y10y"), ("20y10y", "gsw_f20y10y", "f20y10y")]
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    x = np.arange(len(pairs)); w = .36
    g = [r2(a) for _, a, _ in pairs]; c = [r2(b) for _, _, b in pairs]
    ax.bar(x - w / 2, g, w, color=GREY, label="GSW (Svensson fit)")
    ax.bar(x + w / 2, c, w, color=BLUE, label="CMT (observed points)")
    for i in range(len(pairs)):
        ax.text(x[i] - w / 2, g[i] + .03, f"{g[i]:.2f}", ha="center", fontsize=8)
        ax.text(x[i] + w / 2, c[i] + .03, f"{c[i]:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([p for p, _, _ in pairs]); ax.set_ylim(0, 1.05)
    ax.set_ylabel("R² with daily change in cash 10Y")
    ax.set_title("The far forward only looked independent on the fitted curve", fontsize=9)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.tight_layout(); fig.savefig(FIG / "fig12_orthogonality.png"); plt.close(fig)


def fig15():
    pm = pd.read_csv(PROC / "placebo_matched.csv")
    obs = pm[pm.h == 0].b_obs.iloc[0]
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    for name, col, fname in [("uniform", GREY, "placebo_uniform.npy"),
                             ("matched on lag", BLUE, "placebo_matched_on_lag.npy"),
                             ("matched on lag and release type", GREEN,
                              "placebo_matched_on_lag_and_release_type.npy")]:
        b = np.load(PROC / fname)
        p = pm[(pm.h == 0) & (pm.placebo == name)].p.iloc[0]
        short = {"uniform": "uniform", "matched on lag": "matched on lag",
                 "matched on lag and release type": "matched on lag + type"}[name]
        ax.hist(b, bins=60, histtype="step", lw=1.4, color=col, label=f"{short}, p = {p:.3f}")
    ax.axvline(obs, color=RED, lw=2, label=f"observed {obs:+.3f}")
    ax.axvline(0, color="k", lw=.7)
    ax.set_xlabel("day-0 coefficient under placebo dates (bp per $bn)")
    ax.set_ylabel("draws"); ax.legend(frameon=False, fontsize=7.2, loc="upper right")
    ax.set_title("Placebo dates drawn at the same lag after a macro release", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / "fig15_placebo_matched.png"); plt.close(fig)


def fig16():
    o = pd.read_csv(PROC / "otr_spread_lp.csv")
    df = H.panel(); ai = L.shocks(); ai = ai[ai.index.isin(df.index)]
    tot = H.lp_row(df, ai, "spot10", 0)
    s = o[(o.shock == "AI issuance") & (o.dep == "otr10")].set_index("h")
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    bars = [tot.b, s.loc[0, "b"]]
    ax.bar(["10Y yield,\nall bonds", "on-the-run minus\nseasoned (10y)"], bars,
           color=[BLUE, RED], width=.55)
    for i, v in enumerate(bars):
        ax.text(i, v + .004, f"{v:+.3f}", ha="center", fontsize=8.5)
    ax.axhline(0, color="k", lw=.8)
    ax.set_ylim(0, max(bars) * 1.25)
    ax.set_ylabel("bp per $bn 10y-equiv, day 0")
    ax.set_title("If hedgers were selling on-the-runs, the red bar would be large", fontsize=9, pad=10)
    fig.tight_layout(); fig.savefig(FIG / "fig16_otr_spread.png"); plt.close(fig)


if __name__ == "__main__":
    for fn in (fig8, fig11_12, fig15, fig16):
        fn(); print("wrote", fn.__name__)
