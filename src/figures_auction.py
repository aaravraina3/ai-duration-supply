"""Auction demand figure: where the 23 September five-year sits, and whether
weak demand maps to a higher term premium."""
import numpy as np, pandas as pd, statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import PROC, FIG

plt.rcParams.update({"figure.dpi": 140, "font.size": 9, "axes.grid": True,
                     "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED, GREY = "#1f4e79", "#c0392b", "#7f8c8d"


def main():
    det = pd.read_csv(PROC / "auction_detail.csv", parse_dates=["date"])
    det = det[det.date >= "2024-01-01"].dropna(subset=["btc_norm"])
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    det["dTP"] = det.date.map(acm.ACMTP10.diff() * 100)

    fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.4))

    # left: 5y bid-to-cover history with 23 Sep flagged
    five = det[det.tenor == 5].sort_values("date")
    ax[0].plot(five.date, five.bid_to_cover_ratio, "o-", color=GREY, ms=3.5, lw=1)
    s23 = five[five.date == "2026-09-23"]
    if len(s23):
        ax[0].plot(s23.date, s23.bid_to_cover_ratio, "o", color=RED, ms=8, zorder=5)
        ax[0].annotate("23 Sep\n2.21", xy=(s23.date.iloc[0], s23.bid_to_cover_ratio.iloc[0]),
                       xytext=(-52, 14), textcoords="offset points", color=RED, fontsize=8,
                       arrowprops=dict(arrowstyle="->", color=RED, lw=1.1))
    ax[0].set_ylabel("bid-to-cover"); ax[0].set_title("Five-year auctions", fontsize=9)
    ax[0].tick_params(axis="x", rotation=30, labelsize=7)

    # right: demand surprise vs term premium change, 7-10y where it bites
    s = det[(det.tenor >= 7) & (det.tenor <= 10)].dropna(subset=["dTP"])
    ax[1].scatter(s.btc_norm, s.dTP, s=18, color=BLUE, alpha=.65)
    m = sm.OLS(s.dTP, sm.add_constant(s[["btc_norm"]])).fit()
    xs = np.linspace(s.btc_norm.min(), s.btc_norm.max(), 50)
    ax[1].plot(xs, m.params["const"] + m.params["btc_norm"] * xs, color=RED, lw=1.6)
    ax[1].axhline(0, color="k", lw=.7); ax[1].axvline(0, color="k", lw=.7)
    ax[1].set_xlabel("bid-to-cover surprise  (weak <- 0 -> strong)")
    ax[1].set_ylabel("same-day change in 10Y term premium (bp)")
    ax[1].set_title(f"7-10y auctions, n={len(s)}, slope {m.params['btc_norm']:.1f} "
                    f"(t={m.tvalues['btc_norm']:.2f})", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / "fig14_auction_demand.png"); plt.close(fig)
    print("wrote fig14_auction_demand.png")
    print(f"  7-10y slope {m.params['btc_norm']:+.2f} t={m.tvalues['btc_norm']:+.2f} n={len(s)}")


if __name__ == "__main__":
    main()
