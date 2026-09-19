"""Phase 3 / H6: the FX-hedged Japanese investor channel.

WHY THIS HYPOTHESIS
Japanese institutions hold ~$1T of Treasuries, the largest foreign position, and
sold $29.6B in Q1 2026. That stock dwarfs the 194 $bn of 10-year-equivalent
duration the AI names supplied in 2026. If the marginal foreign buyer of US
duration withdraws, the term premium should rise, and unlike the issuance channel
this is a LEVEL effect rather than a three-day announcement effect.

THE MATH, AND WHY THIS FORM

A JPY-based investor buying a USD Treasury and hedging the currency with rolling
forwards earns, to first order under covered interest parity,

    hedged yield  =  y^UST(10)  -  (r^USD - r^JPY)  -  b

where (r^USD - r^JPY) is the short-rate differential paid away in the forward
points and b is the cross-currency basis. The decision variable against holding
domestic paper is the pickup

    pi_t  =  y^UST(10)  -  (r^USD_3m - r^JPY_3m)  -  b_t  -  y^JGB(10)

pi_t > 0 means hedged Treasuries beat JGBs and Japan is a buyer of US duration.
pi_t < 0 means the marginal buyer goes home.

Prediction: d(term premium) should be NEGATIVELY related to pi. A fatter pickup
pulls foreign money in and compresses US term premium.

CHOICES, AND WHAT I REJECTED

1. Hedging tenor = 3 months.
   Why: rolling 3m forwards is the institutional convention for FX-hedged bond
   books, and it is the tenor most hedge-ratio disclosures reference.
   Rejected 1m: cheaper carry but more roll risk, and it over-weights
   month-to-month funding noise that has nothing to do with the bond decision.
   Rejected 12m: less roll risk, but it embeds a full year of expected policy
   divergence into what should be a funding cost, and free 12m JPY rates are
   worse quality than 3m.

2. Covered interest parity approximation, basis omitted.
   Why: no free daily or monthly JPY cross-currency basis series was reachable.
   COST, AND THE SIGN OF THE BIAS: the JPY basis has been persistently NEGATIVE
   (roughly -20 to -50bp in recent years), which makes hedging USD assets more
   expensive than the pure rate differential implies. Omitting it therefore
   biases pi UPWARD, i.e. it makes hedged Treasuries look better than they are.
   Any finding that the pickup has already gone negative is CONSERVATIVE under
   this bias. A finding that it is still positive is not.

3. Monthly frequency.
   Forced, not chosen. Free JGB 10Y is FRED IRLTLT01JPM156N, monthly. MOF's
   daily CSV endpoints return HTML error pages. That leaves ~32 observations for
   2024-2026, which is the binding constraint on this whole hypothesis and the
   reason it is tested third despite being the largest flow.

4. Levels regression alongside changes.
   Unusual, and deliberate. The issuance channel is an announcement effect, so
   changes are right. This channel is a portfolio-allocation margin, so the LEVEL
   of the pickup should map to the LEVEL of compensation demanded. I run both and
   report both, because a levels regression on 32 points with two trending series
   is exactly how people manufacture spurious results. Newey-West with a lag long
   enough to matter, and a first-difference specification next to it, is the
   minimum honesty here.
"""
import io, numpy as np, pandas as pd, requests, statsmodels.api as sm
from config import PROC, RAW

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SERIES = {
    "jgb10": "IRLTLT01JPM156N",   # Japan 10Y benchmark, monthly
    "jpy3m": "IR3TIB01JPM156N",   # Japan 3m interbank, monthly
    "ust10": "DGS10",             # daily, taken to month end
    "usd3m": "DTB3",              # 3m T-bill, daily, month end
    "usdjpy": "DEXJPUS",
}


def _get(sid):
    p = RAW / f"fred_{sid}.csv"
    if not p.exists():
        r = requests.get(FRED.format(sid), timeout=90); r.raise_for_status()
        p.write_bytes(r.content)
    d = pd.read_csv(io.StringIO(p.read_text()))
    d.columns = ["date", sid]
    d["date"] = pd.to_datetime(d.date)
    d[sid] = pd.to_numeric(d[sid], errors="coerce")
    return d.dropna().set_index("date")[sid]


def build(start="2023-06-01"):
    raw = {k: _get(v) for k, v in SERIES.items()}
    m = pd.DataFrame({k: s.resample("ME").last() for k, s in raw.items()})
    m = m[m.index >= start].dropna(subset=["jgb10", "ust10", "usd3m"])
    m["jpy3m"] = m.jpy3m.ffill()          # publishes one month later than the rest
    m["hedge_cost"] = m.usd3m - m.jpy3m
    m["hedged_ust"] = m.ust10 - m.hedge_cost
    m["pickup"] = m.hedged_ust - m.jgb10
    m["d_pickup"] = m.pickup.diff()

    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    m["tp10"] = (acm.ACMTP10.resample("ME").last() * 100).reindex(m.index)
    m["d_tp10"] = m.tp10.diff()
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    m["be10"] = (fred.T10YIE.resample("ME").last() * 100).reindex(m.index)
    m["d_be10"] = m.be10.diff()
    m["vix"] = fred.VIXCLS.resample("ME").last().reindex(m.index)
    m["d_vix"] = m.vix.diff()
    return m.dropna(subset=["pickup", "tp10"])


def nw(y, X, lags):
    return sm.OLS(y, sm.add_constant(X)).fit(
        cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": True})


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    m = build()
    print("=" * 78)
    print("H6: FX-HEDGED PICKUP FOR A JAPANESE INVESTOR")
    print("=" * 78)
    print(f"  monthly sample {m.index.min().date()} -> {m.index.max().date()}, n={len(m)}")
    print("\n  pi = UST10 - (USD3m - JPY3m) - JGB10,  in percent")
    print(m[["ust10", "usd3m", "jpy3m", "hedge_cost", "hedged_ust", "jgb10", "pickup"]]
          .tail(14).round(3).to_string())

    p = m.pickup
    print(f"\n  pickup: first {p.iloc[0]:+.3f}  last {p.iloc[-1]:+.3f}  "
          f"min {p.min():+.3f} ({p.idxmin().date()})  max {p.max():+.3f} ({p.idxmax().date()})")
    neg = (p < 0).sum()
    print(f"  months with NEGATIVE pickup (Japan should repatriate): {neg} of {len(p)}")
    if neg:
        print(f"  first negative month: {p[p < 0].index[0].date()}")
    print("  reminder: omitting the cross-currency basis biases pickup UP by roughly")
    print("  20-50bp, so the true pickup is lower than every number printed above.")

    # ------------------------------------------------ the regressions
    L = int(np.floor(4 * (len(m) / 100) ** (2 / 9)))
    print("\n" + "=" * 78)
    print(f"REGRESSIONS (Newey-West, L={L} on n={len(m)} monthly obs)")
    print("=" * 78)
    print("  prediction: pickup coefficient NEGATIVE (fatter pickup pulls in")
    print("  foreign demand and compresses US term premium)\n")

    specs = [
        ("levels:  TP10 ~ pickup",            m.tp10,   m[["pickup"]]),
        ("levels:  TP10 ~ pickup + controls", m.tp10,   m[["pickup", "be10", "vix"]]),
        ("changes: dTP10 ~ d_pickup",         m.d_tp10, m[["d_pickup"]]),
        ("changes: dTP10 ~ d_pickup + ctrl",  m.d_tp10, m[["d_pickup", "d_be10", "d_vix"]]),
    ]
    for name, y, X in specs:
        ok = y.notna() & X.notna().all(axis=1)
        r = nw(y[ok], X[ok], L)
        k = X.columns[0]
        print(f"  {name:36s} coef={r.params[k]:+8.4f}  t={r.tvalues[k]:+6.2f}  "
              f"p={r.pvalues[k]:.3f}  R2={r.rsquared:.3f}  n={int(r.nobs)}")

    # ------------------------------------------------ spurious-regression guard
    print("\n  stationarity guard (levels regressions on trending series are a trap):")
    from statsmodels.tsa.stattools import adfuller
    for c in ["tp10", "pickup"]:
        s = m[c].dropna()
        a = adfuller(s, maxlag=4, autolag=None)
        print(f"    ADF on {c:8s}: stat={a[0]:+.2f} p={a[1]:.3f} "
              f"-> {'stationary' if a[1] < 0.10 else 'CANNOT reject unit root'}")
    print("    If both carry a unit root, the levels R2 above is not evidence.")
    print("    The change specification is the one to read.")

    # ------------------------------------------------ scale comparison
    print("\n" + "=" * 78)
    print("SCALE: Japan vs AI supply, same units")
    print("=" * 78)
    ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    ai26 = ev[ev.announce >= "2026-01-01"].tenyr_equiv.sum() / 1e9
    # $29.6B of net Treasury sales in Q1 2026 (sourced, not computed here).
    # Convert to 10y-equivalents using the average duration of foreign official
    # holdings, roughly a 7y bullet, as a stated assumption.
    from eventlist import mod_duration, DUR10
    jp_q1_10y = 29.6 * mod_duration(7, 4.5) / DUR10
    print(f"  AI issuance 2026 YTD          : {ai26:6.1f} $bn 10y-equivalents")
    print(f"  Japan net UST sales Q1 2026   : {jp_q1_10y:6.1f} $bn 10y-equivalents "
          f"(from $29.6B face, 7y duration assumption)")
    print(f"  ratio Japan Q1 / AI full year : {jp_q1_10y / ai26:.2f}x")
    print("  Japanese holdings at risk     : ~$1,000 $bn face, roughly "
          f"{1000 * mod_duration(7, 4.5) / DUR10:.0f} $bn 10y-equivalents")
    m.to_csv(PROC / "japan_channel.csv")
