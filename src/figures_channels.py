"""Figure: where on the curve each duration flow shows up."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import PROC, FIG
import localproj as L, hedgeflow as H

plt.rcParams.update({"figure.dpi": 140, "font.size": 9, "axes.grid": True,
                     "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED = "#1f4e79", "#c0392b"

DEPS = [("spot10", "10Y spot"), ("f5y5y", "5y5y fwd"),
        ("f10y10y", "10y10y fwd"), ("f20y10y", "20y10y fwd")]


def main():
    df = H.panel()
    ai = L.shocks()
    bb = pd.read_csv(PROC / "buybacks_daily.csv", parse_dates=["date"]).set_index("date").bb_long
    bb = bb[bb > 0]

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.4), sharey=False)
    for ax, (shock, name, col, sign) in zip(
            axes, [(ai, "AI corporate issuance\n(adds duration)", BLUE, +1),
                   (bb, "Treasury buybacks\n(removes duration)", RED, -1)]):
        b, se, labs = [], [], []
        for key, lab in DEPS:
            r = L.project(df, shock, dep=key, hmax=0).iloc[0]
            b.append(r.b); se.append(r.se); labs.append(lab)
        x = np.arange(len(labs))
        ax.bar(x, b, 0.6, color=col, alpha=.9)
        ax.errorbar(x, b, yerr=1.96 * np.array(se), fmt="none", ecolor="k", lw=1, capsize=3)
        ax.axhline(0, color="k", lw=.8)
        ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=8)
        ax.set_title(name, fontsize=9)
        ax.set_ylabel("bp per $bn 10y-equiv" if sign > 0 else "")
    fig.suptitle("Announcement-day response by curve segment, with 95% bands", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig11_channels.png")
    plt.close(fig)

    # how orthogonal each segment is to the cash 10Y
    import statsmodels.api as sm
    d10 = df.spot10.diff()
    r2 = []
    for key, lab in DEPS:
        y = df[key].diff(); ok = y.notna() & d10.notna()
        r2.append(sm.OLS(y[ok], sm.add_constant(d10[ok])).fit().rsquared)
    fig, ax = plt.subplots(figsize=(5.0, 2.8))
    ax.bar([l for _, l in DEPS], r2, color="#7f8c8d")
    ax.set_ylabel("R² with d(10Y spot)"); ax.set_ylim(0, 1.05)
    ax.set_title("How mechanically tied to the cash 10Y is each segment?", fontsize=9)
    for i, v in enumerate(r2):
        ax.text(i, v + .03, f"{v:.2f}", ha="center", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig12_orthogonality.png"); plt.close(fig)
    print("wrote fig11_channels.png, fig12_orthogonality.png")
    print("R2 vs 10Y:", dict(zip([l for _, l in DEPS], np.round(r2, 3))))


if __name__ == "__main__":
    main()
