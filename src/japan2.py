"""H6, corrected. The naive pickup regression is mechanically contaminated.

THE PROBLEM WITH THE FIRST SPECIFICATION

    pickup = ust10 - (usd3m - jpy3m) - jgb10

contains ust10. The dependent variable, ACM TP10, is 64% explained by the 10Y
on its own (R2 measured in hedgeflow.py). So regressing TP10 on pickup is partly
regressing the 10Y on the 10Y, and a positive coefficient is close to mechanical.
That is the same trap that made the original concession estimator meaningless,
and it produced a +65.7 coefficient with t = 8.2 that means nothing.

THE FIX: SPLIT THE PICKUP INTO ITS US AND NON-US HALVES

    pickup = ust10  -  hurdle,        hurdle = jgb10 + (usd3m - jpy3m)

`hurdle` is what a hedged Treasury has to clear to beat domestic JGBs. It is
built entirely from Japanese yields and the short-rate differential, so it
contains no US long yield. If the repatriation channel is real, a rising hurdle
means the marginal Japanese buyer withdraws and the US term premium should rise.

    PREDICTION: coefficient on `hurdle` is POSITIVE.

Note the prediction flips sign relative to `pickup` because hurdle enters with
the opposite sign. Writing that down before running it, since it would be easy
to claim either result as confirmation afterwards.

REMAINING CONFOUND, AND HOW IT IS HANDLED

Global long rates rose together over 2024-2026. JGB 10Y went from roughly 0.4%
to 2.94%, and US yields rose too. A naive TP10-on-hurdle regression will load on
that common global factor whatever the true Japanese channel is.

Three layers of defence, weakest to strongest:

  (a) control for the US expectations component, ACM RNY10. Whatever the Fed path
      explains is then removed, and the hurdle coefficient picks up only what is
      left in compensation.
  (b) control for the US 2Y as well, a second read on the domestic policy path.
  (c) orthogonalise: regress hurdle on the US expectations component first, keep
      the residual. That residual is the part of the Japanese hurdle unexplained
      by US policy, which is the closest this data gets to an exogenous mover.

Layer (c) is the one to believe, and it is also the one with the least power.

WHY NOT A VAR OR AN IRF
Considered and rejected. A VAR on 38 monthly observations with 3-4 endogenous
variables burns degrees of freedom on lag structure I cannot estimate, and the
identification would still rest on an ordering assumption I have no basis for.
Single-equation with an explicit orthogonalisation is more honest about what is
being assumed.

WHY NOT AN INSTRUMENT
The right instrument for Japanese domestic yields is a BOJ policy surprise, which
needs intraday JGB futures around policy announcements. Not free, and there have
only been a handful of BOJ moves in the sample.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC
import japan as J


def build():
    m = J.build()
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    m["rny10"] = (acm.ACMRNY10.resample("ME").last() * 100).reindex(m.index)
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    m["ust2"] = (fred.DGS2.resample("ME").last() * 100).reindex(m.index)

    m["hurdle"] = m.jgb10 * 100 + m.hedge_cost * 100     # bp, no US long yield in it
    m["d_hurdle"] = m.hurdle.diff()
    m["d_rny10"] = m.rny10.diff()
    m["d_ust2"] = m.ust2.diff()
    m["d_jgb10"] = (m.jgb10 * 100).diff()
    return m.dropna(subset=["hurdle", "tp10", "rny10"])


def nw(y, X, L):
    ok = y.notna() & X.notna().all(axis=1)
    return sm.OLS(y[ok], sm.add_constant(X[ok])).fit(
        cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": True})


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    m = build()
    n = len(m)
    L = int(np.floor(4 * (n / 100) ** (2 / 9)))
    print("=" * 78)
    print(f"H6 CORRECTED: the Japanese hurdle rate  (n={n} monthly, NW L={L})")
    print("=" * 78)
    print("  hurdle = JGB10 + (USD3m - JPY3m), in bp. Contains no US long yield.")
    print(f"  hurdle: {m.hurdle.iloc[0]:.0f}bp -> {m.hurdle.iloc[-1]:.0f}bp   "
          f"(JGB10 {m.jgb10.iloc[0]*100:.0f} -> {m.jgb10.iloc[-1]*100:.0f}, "
          f"hedge cost {m.hedge_cost.iloc[0]*100:.0f} -> {m.hedge_cost.iloc[-1]*100:.0f})")
    print("\n  PREDICTION, written before running: coefficient on hurdle POSITIVE.\n")

    print("  --- changes specifications (the stationary ones) ---")
    rows = [
        ("(0) dTP10 ~ d_hurdle",                 m.d_tp10, m[["d_hurdle"]]),
        ("(a) + US expectations",                m.d_tp10, m[["d_hurdle", "d_rny10"]]),
        ("(b) + US expectations + 2Y",           m.d_tp10, m[["d_hurdle", "d_rny10", "d_ust2"]]),
        ("    + breakeven, VIX too",             m.d_tp10, m[["d_hurdle", "d_rny10", "d_ust2",
                                                              "d_be10", "d_vix"]]),
        ("    JGB10 alone, no hedge cost",       m.d_tp10, m[["d_jgb10", "d_rny10"]]),
    ]
    for name, y, X in rows:
        r = nw(y, X, L)
        k = X.columns[0]
        print(f"  {name:36s} {k:10s}={r.params[k]:+7.3f}  t={r.tvalues[k]:+6.2f}  "
              f"p={r.pvalues[k]:.3f}  R2={r.rsquared:.3f}")

    # ---------------- layer (c): orthogonalised hurdle
    print("\n  --- (c) orthogonalised: hurdle purged of US policy expectations ---")
    ok = m.d_hurdle.notna() & m.d_rny10.notna()
    first = sm.OLS(m.d_hurdle[ok], sm.add_constant(m.d_rny10[ok])).fit()
    m.loc[ok, "d_hurdle_orth"] = first.resid
    print(f"    first stage: d_hurdle on d_rny10, R2={first.rsquared:.3f} "
          f"(so {first.rsquared*100:.0f}% of hurdle moves are US-policy co-movement)")
    r = nw(m.d_tp10, m[["d_hurdle_orth"]], L)
    print(f"    dTP10 ~ d_hurdle_orth        coef={r.params['d_hurdle_orth']:+7.3f}  "
          f"t={r.tvalues['d_hurdle_orth']:+6.2f}  p={r.pvalues['d_hurdle_orth']:.3f}  "
          f"R2={r.rsquared:.3f}")

    # ---------------- placebo: does the hurdle also "explain" US expectations?
    print("\n  --- falsification: the hurdle should NOT explain US expectations ---")
    r2 = nw(m.d_rny10, m[["d_hurdle_orth"]], L)
    print(f"    dRNY10 ~ d_hurdle_orth       coef={r2.params['d_hurdle_orth']:+7.3f}  "
          f"t={r2.tvalues['d_hurdle_orth']:+6.2f}  p={r2.pvalues['d_hurdle_orth']:.3f}")
    print("    by construction the orthogonalised regressor is uncorrelated with")
    print("    d_rny10, so this is a sanity check on the arithmetic, not a test.")

    # ---------------- reverse direction
    print("\n  --- reverse causality: does the US term premium move the hurdle? ---")
    m["d_tp_lag"] = m.d_tp10.shift(1)
    r3 = nw(m.d_hurdle, m[["d_tp_lag"]], L)
    print(f"    d_hurdle ~ lagged dTP10      coef={r3.params['d_tp_lag']:+7.3f}  "
          f"t={r3.tvalues['d_tp_lag']:+6.2f}  p={r3.pvalues['d_tp_lag']:.3f}")
    m["d_hurdle_lag"] = m.d_hurdle.shift(1)
    r4 = nw(m.d_tp10, m[["d_hurdle_lag"]], L)
    print(f"    dTP10 ~ lagged d_hurdle      coef={r4.params['d_hurdle_lag']:+7.3f}  "
          f"t={r4.tvalues['d_hurdle_lag']:+6.2f}  p={r4.pvalues['d_hurdle_lag']:.3f}")
    print("    a clean channel runs hurdle -> TP, not the reverse.")

    # ---------------- economic magnitude
    print("\n" + "=" * 78)
    print("MAGNITUDE")
    print("=" * 78)
    rb = nw(m.d_tp10, m[["d_hurdle", "d_rny10"]], L)
    b = rb.params["d_hurdle"]
    tot = m.hurdle.iloc[-1] - m.hurdle.iloc[0]
    print(f"  coefficient (spec a)                : {b:+.3f} bp TP per bp of hurdle")
    print(f"  total hurdle move over the sample   : {tot:+.0f} bp")
    print(f"  implied cumulative TP contribution  : {b*tot:+.0f} bp")
    tp_tot = m.tp10.iloc[-1] - m.tp10.iloc[0]
    print(f"  actual TP10 move over the sample    : {tp_tot:+.0f} bp")
    if abs(tp_tot) > 1e-9:
        print(f"  share of the realised TP move       : {b*tot/tp_tot:.0%}")
    print("\n  Compare: AI issuance contributed an estimated +15.6bp of")
    print("  announcement-day impact across all of 2026, none of it persistent.")
    m.to_csv(PROC / "japan_hurdle.csv")
