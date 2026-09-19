"""Why is the strategy P&L so volatile? Decompose it.

The per-trade standard deviation is 62bp of price against a 19bp mean. That
noise-to-signal of ~3.2x is what makes the t-stat 1.24 on 16 trades. This module
asks where the 62bp comes from, because the answer determines whether it can be
engineered away or not.

Hypothesis: almost none of it is about the bond deal. The trade is an OUTRIGHT
duration position, so it inherits the full 5-day volatility of the 10Y, which is
driven by CPI prints, Fed speakers, oil and everything else. The deal-related
signal is a couple of basis points sitting inside a ten-basis-point random walk.

If that is right, the fix is not a better signal, it is hedging out the market
exposure that the signal was never about. Note that the hypothesis was TESTED
with controls for the 2Y and breakevens (abnormal.py) and then TRADED without
them. That inconsistency is the bug.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC
import curve as C, strategy as S

MODDUR = S.MODDUR_10Y


def decompose(hold=5):
    """Split each trade's P&L into a deal-size component and a market component."""
    z = C.load_gsw(start="2024-01-01")
    y10, y2, y5, y30 = z[10.0] * 100, z[2.0] * 100, z[5.0] * 100, z[30.0] * 100
    ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    idx = z.index
    rows = []
    for _, e in ev.iterrows():
        p = idx.searchsorted(pd.Timestamp(e.announce))
        if p >= len(idx) or p + hold >= len(idx):
            continue
        rows.append(dict(
            announce=e.announce, size10=e.tenyr_equiv / 1e9,
            dy10=y10.iloc[p + hold] - y10.iloc[p],
            dy2=y2.iloc[p + hold] - y2.iloc[p],
            dy5=y5.iloc[p + hold] - y5.iloc[p],
            dy30=y30.iloc[p + hold] - y30.iloc[p]))
    return pd.DataFrame(rows)


def unconditional_vol(hold=5):
    """What does a random 5-day 10Y position look like? The benchmark for noise."""
    z = C.load_gsw(start="2024-01-01")
    y10 = z[10.0] * 100
    dy = (y10.shift(-hold) - y10).dropna()
    return dy.std(), (y10.diff().dropna()).std()


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    d = decompose()
    d["pnl"] = -d.dy10 * MODDUR

    print("=" * 76)
    print("WHERE THE 62bp COMES FROM")
    print("=" * 76)
    sd5, sd1 = unconditional_vol()
    print(f"  10Y daily yield sd, 2024-2026        : {sd1:.2f} bp")
    print(f"  10Y 5-day yield sd (sqrt(5) x daily) : {sd1*np.sqrt(5):.2f} bp  "
          f"(actual overlapping: {sd5:.2f} bp)")
    print(f"  => 5-day price sd of an outright 10Y : {sd5*MODDUR:.0f} bp")
    print(f"  observed strategy P&L sd             : {d.pnl.std(ddof=1):.0f} bp")
    print("\n  The strategy's volatility IS the 10Y's volatility. Holding a bond for")
    print("  five days is the entire risk; the deal is incidental to it.")

    print("\n" + "=" * 76)
    print("HOW MUCH OF THE P&L IS ACTUALLY ABOUT THE DEAL?")
    print("=" * 76)
    m = sm.OLS(d.pnl, sm.add_constant(d[["size10"]])).fit()
    print(f"  P&L on deal size      : coef={m.params['size10']:+.3f} bp per $bn, "
          f"t={m.tvalues['size10']:+.2f}, R2={m.rsquared:.3f}")
    m2 = sm.OLS(d.dy10, sm.add_constant(d[["dy2"]])).fit()
    print(f"  dy10 on dy2 (market)  : beta={m2.params['dy2']:+.3f}, R2={m2.rsquared:.3f}")
    print(f"\n  {m.rsquared*100:.0f}% of P&L variance is explained by how big the deal was.")
    print(f"  {m2.rsquared*100:.0f}% of the 10Y move is explained by the 2Y, i.e. by the")
    print("  market-wide rate move that has nothing to do with the issuance.")

    print("\n  signal vs noise, in yield terms:")
    exp_sig = 0.123 * d.size10.mean()        # bp, from the local projection h0->h5
    print(f"    expected deal effect on a mean-size deal : {exp_sig:.2f} bp of yield")
    print(f"    5-day noise in the 10Y                   : {sd5:.2f} bp of yield")
    print(f"    signal-to-noise ratio                    : {exp_sig/sd5:.2f}")
    print("    To see a 0.25 signal-to-noise effect at t=2 you need roughly")
    print(f"    {int(np.ceil((2/(exp_sig/sd5))**2))} trades. We have 16.")

    # ------------------------------------------------------ the hedged versions
    print("\n" + "=" * 76)
    print("HEDGING OUT THE MARKET: P&L = -(dy10 - beta*dy2) x ModDur")
    print("=" * 76)
    print("  beta=0     outright 10Y, what the strategy currently does")
    print("  beta=0.664 the empirical hedge ratio from abnormal.py's normal relation")
    print("  beta=1     DV01-neutral 2s10s spread\n")
    span = (d.announce.max() - d.announce.min()).days / 365.25
    freq = len(d) / span
    print(f"  {'hedge':>22} {'mean':>8} {'sd':>8} {'t':>7} {'Sharpe':>8} {'hit':>6}")
    best = None
    for name, beta in [("beta=0 (outright)", 0.0), ("beta=0.664 (empirical)", 0.664),
                       ("beta=1 (2s10s)", 1.0), ("beta=1 vs 5Y (5s10s)", None),
                       ("10s30s", "30")]:
        if beta is None:
            pnl = -(d.dy10 - d.dy5) * MODDUR
        elif beta == "30":
            pnl = -(d.dy30 - d.dy10) * MODDUR
        else:
            pnl = -(d.dy10 - beta * d.dy2) * MODDUR
        pnl = pnl - 3.0 if beta in (0.0,) else pnl - 6.0     # two legs cost double
        mu, sd = pnl.mean(), pnl.std(ddof=1)
        t = mu / (sd / np.sqrt(len(pnl)))
        sh = mu / sd * np.sqrt(freq)
        print(f"  {name:>22} {mu:+8.2f} {sd:8.2f} {t:+7.2f} {sh:+8.2f} {np.mean(pnl>0):6.0%}")
        if best is None or t > best[1]:
            best = (name, t, sh, mu, sd)

    print(f"\n  best by t-stat: {best[0]}  t={best[1]:+.2f}  Sharpe={best[2]:+.2f}")
    print("  NOTE: that is a selection over 5 hedge ratios on 16 trades. Treat the")
    print("  winner as a hypothesis to test out of sample, not as a result.")

    # ------------------------------------------------------ does the signal survive?
    print("\n" + "=" * 76)
    print("DOES THE DEAL SIGNAL SURVIVE THE HEDGE?")
    print("=" * 76)
    print("  If issuance is a pure LEVEL shock, a curve trade cancels the signal")
    print("  along with the noise. Checking whether the effect differs across the")
    print("  curve, because only the differential survives a spread.\n")
    for lab, series in [("dy10 (outright)", d.dy10), ("dy10 - dy2", d.dy10 - d.dy2),
                        ("dy10 - dy5", d.dy10 - d.dy5), ("dy30 - dy10", d.dy30 - d.dy10)]:
        r = sm.OLS(series, sm.add_constant(d[["size10"]])).fit()
        print(f"  {lab:18s} on deal size: coef={r.params['size10']:+.4f} "
              f"t={r.tvalues['size10']:+5.2f}  R2={r.rsquared:.3f}")
    d.to_csv(PROC / "variance_decomp.csv", index=False)
