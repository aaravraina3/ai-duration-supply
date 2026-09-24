"""Figures for the writeup."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import PROC, FIG
import curve as C

plt.rcParams.update({"figure.dpi": 140, "font.size": 9, "axes.grid": True,
                     "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED, GREY = "#1f4e79", "#c0392b", "#7f8c8d"


def f1_curve():
    z = C.load_gsw(start="2024-01-01")
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    picks = ["2026-01-02", "2026-03-31", "2026-06-30", "2026-09-11"]
    for d in picks:
        s = z.loc[:d].iloc[-1]
        ax[0].plot(s.index, s.values, label=pd.Timestamp(d).date(), lw=1.6)
    ax[0].set_title("GSW zero curve through 2026"); ax[0].set_xlabel("maturity (y)")
    ax[0].set_ylabel("%"); ax[0].legend(frameon=False, fontsize=7)
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    s = fred.DGS10.dropna().loc["2024-01-01":]
    ax[1].plot(s.index, s.values, color=BLUE, lw=1.2, label="10Y CMT")
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date").loc["2024-01-01":]
    ax[1].plot(acm.index, acm.ACMTP10, color=RED, lw=1.2, label="ACM 10Y term premium")
    ax[1].axhline(5.0, color=GREY, ls=":", lw=.8)
    ev = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    for a in ev.announce:
        ax[1].axvline(a, color="k", alpha=.18, lw=.9)
    ax[1].set_title("10Y and term premium, events marked"); ax[1].set_ylabel("%")
    ax[1].legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "fig1_curve.png"); plt.close(fig)


def f2_pca():
    z = C.load_gsw(start="2024-01-01")
    f, V, ev, dz = C.pca_factors(z)
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    for k, (lab, col) in enumerate(zip(["PC1 level", "PC2 slope", "PC3 curvature"],
                                       [BLUE, RED, "#27ae60"])):
        ax.plot(z.columns, V[:, k], label=f"{lab} ({ev[k]*100:.1f}%)", color=col, lw=1.6)
    ax.axhline(0, color="k", lw=.6)
    ax.set_xlabel("maturity (y)"); ax.set_ylabel("loading")
    ax.set_title("PCA of daily zero-curve changes"); ax.legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "fig2_pca.png"); plt.close(fig)


def f3_supply():
    d = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    col = {"Amazon": "#e67e22", "Alphabet": BLUE, "Meta": "#8e44ad", "Oracle": RED}
    for iss, g in d.groupby("issuer"):
        ax.bar(g.announce, g.tenyr_equiv / 1e9, width=9, label=iss,
               color=col.get(iss, GREY), alpha=.9)
    ax.axhline(0, color="k", lw=.6)
    ax.set_ylabel("$bn, 10-year equivalents"); ax.legend(frameon=False, fontsize=7, ncol=4)
    ax.set_title("USD duration supply from the five issuers (announcement dated)")
    fig.tight_layout(); fig.savefig(FIG / "fig3_supply.png"); plt.close(fig)


def f4_localproj():
    lp = pd.read_csv(PROC / "localproj_all.csv")
    fig, ax = plt.subplots(figsize=(7.4, 2.9))
    ax.plot(lp.h, lp.b, color=BLUE, lw=1.6)
    ax.fill_between(lp.h, lp.b - 1.96 * lp.se, lp.b + 1.96 * lp.se, color=BLUE, alpha=.15)
    ax.axhline(0, color="k", lw=.8)
    ax.set_xlabel("business days after announcement")
    ax.set_ylabel("bp per $bn 10y-equivalent")
    ax.set_title("Term premium response to AI duration supply")
    fig.tight_layout(); fig.savefig(FIG / "fig4_localproj.png"); plt.close(fig)


def f5_placebo():
    pl = np.load(PROC / "abnormal_placebo.npy")
    res = pd.read_csv(PROC / "abnormal_events.csv")
    x = float(np.average(res.abn_bp, weights=res.dollar_dur))
    fig, ax = plt.subplots(figsize=(5.0, 3.2))
    ax.hist(pl, bins=60, color=GREY, alpha=.7)
    ax.axvline(x, color=RED, lw=2, label=f"actual {x:+.2f} bp")
    ax.axvline(0, color="k", lw=.8)
    ax.set_xlabel("duration-weighted abnormal move (bp)"); ax.set_ylabel("placebo draws")
    ax.set_title(f"Placebo: {len(pl)} randomised event-date sets")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig5_placebo.png"); plt.close(fig)


def f6_decomp():
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    a = acm.loc["2026-01-01":]
    base = a.iloc[0]
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.plot(a.index, (a.ACMY10 - base.ACMY10) * 100, color="k", lw=1.5, label="10Y zero yield")
    ax.plot(a.index, (a.ACMRNY10 - base.ACMRNY10) * 100, color=BLUE, lw=1.4,
            label="expected short rates")
    ax.plot(a.index, (a.ACMTP10 - base.ACMTP10) * 100, color=RED, lw=1.4, label="term premium")
    ax.axhline(0, color="k", lw=.6)
    ax.set_ylabel("bp change since 2 Jan 2026")
    ax.set_title("2026 decomposition: the move is expectations, not term premium")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "fig6_decomp.png"); plt.close(fig)


def f7_nlp():
    s = pd.read_csv(PROC / "nlp_index.csv", parse_dates=["date"]).set_index("date")
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ax.plot(s.index, s.S, color=BLUE, lw=1.3)
    ax.axhline(0, color="k", lw=.6)
    ax.set_title("NLP supply-pressure index $S_t$ (30-day half-life)")
    ax.set_ylabel("index")
    fig.tight_layout(); fig.savefig(FIG / "fig7_nlp.png"); plt.close(fig)


if __name__ == "__main__":
    for fn in (f1_curve, f2_pca, f3_supply, f4_localproj, f5_placebo, f6_decomp, f7_nlp):
        fn(); print("wrote", fn.__name__)
    print("figures in", FIG)
