"""The signal-vs-noise picture. The most intuitive idea in the project and the
one with no figure: a 2.56bp effect sitting inside an 11.36bp distribution."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import PROC, FIG
import curve as C

plt.rcParams.update({"figure.dpi": 140, "font.size": 9, "axes.grid": True,
                     "grid.alpha": .25, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED, GREY = "#1f4e79", "#c0392b", "#7f8c8d"


def main():
    z = C.load_gsw(start="2024-01-01")
    y10 = z[10.0] * 100
    dy5 = (y10.shift(-5) - y10).dropna()
    sig = 0.123 * 20.8          # LP h0->h5 coefficient x mean deal size, bp

    fig, ax = plt.subplots(1, 2, figsize=(9.4, 3.3))

    # left: the distribution the signal has to be seen through
    ax[0].hist(dy5, bins=60, color=GREY, alpha=.75)
    ax[0].axvline(0, color="k", lw=.8)
    ax[0].axvspan(0, sig, color=RED, alpha=.85)
    ax[0].annotate(f"the effect\n{sig:.1f} bp", xy=(sig, ax[0].get_ylim()[1] * .55),
                   xytext=(sig + 14, ax[0].get_ylim()[1] * .75), color=RED, fontsize=8.5,
                   arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
    ax[0].set_xlabel("5-day change in the 10Y yield (bp)")
    ax[0].set_ylabel("days")
    ax[0].set_title(f"What you are looking through\nsd = {dy5.std():.1f} bp", fontsize=9)

    # right: how many trades before the effect is visible
    n = np.arange(5, 201)
    snr = sig / dy5.std()
    t = snr * np.sqrt(n)
    ax[1].plot(n, t, color=BLUE, lw=1.8)
    ax[1].axhline(2, color=RED, ls="--", lw=1.2, label="t = 2")
    ax[1].axvline(16, color="k", ls=":", lw=1.2, label="what we have (16)")
    n80 = int(np.ceil((2 / snr) ** 2))
    ax[1].axvline(n80, color=GREY, ls=":", lw=1.2, label=f"what we need ({n80})")
    ax[1].set_xlabel("number of events")
    ax[1].set_ylabel("expected t-statistic")
    ax[1].set_title(f"Signal-to-noise = {snr:.2f}", fontsize=9)
    ax[1].legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig13_signal_noise.png")
    plt.close(fig)
    print(f"sd(5d) = {dy5.std():.2f} bp | signal {sig:.2f} bp | snr {snr:.3f} | need n={n80}")


if __name__ == "__main__":
    main()
