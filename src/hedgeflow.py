"""Phase 2: is the announcement effect risk compensation, or dealer hedging flow?

The counterargument to H1 (see research/02_HYPOTHESES.md H10) is that ACM TP10 is
96% explained by five PCs of the same zero curve, so anything that moves the cash
10Y moves the measured "term premium" mechanically. Underwriters rate-locking a
jumbo deal sell cash Treasuries around the 10Y point, which produces the observed
pattern without any change in required risk compensation.

Separation: a rate-lock hedge concentrates where the hedge is put on and unwinds.
A genuine repricing of duration risk should also show in the 5y5y forward, which
is far from the hedging point, and in the far forward curve generally.

Pre-registered predictions:
  flow story  -> effect in the 10Y spot, little or nothing at 5y5y
  premium story -> effect present at 5y5y, same sign
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC
import curve as C, localproj as L


def forwards():
    """Build forward rates from the GSW zero curve. The n1-to-n2 forward is
    (n2*y(n2) - n1*y(n1)) / (n2 - n1) under continuous-ish compounding."""
    z = C.load_gsw(start="2024-01-01")
    f = pd.DataFrame(index=z.index)
    f["spot10"] = z[10.0] * 100
    f["spot5"] = z[5.0] * 100
    f["spot30"] = z[30.0] * 100
    f["f5y5y"] = (10 * z[10.0] - 5 * z[5.0]) / 5 * 100
    f["f10y10y"] = (20 * z[20.0] - 10 * z[10.0]) / 10 * 100
    f["f20y10y"] = (30 * z[30.0] - 20 * z[20.0]) / 10 * 100
    return f


def panel():
    p = L.panel()                       # TP10, RN10, controls
    f = forwards().reindex(p.index).ffill()
    return p.join(f)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    df = panel()
    ai = L.shocks()
    bb = pd.read_csv(PROC / "buybacks_daily.csv", parse_dates=["date"]).set_index("date").bb_long
    bb = bb[bb > 0]

    print("=" * 78)
    print("WHERE ON THE CURVE DOES THE ANNOUNCEMENT EFFECT LIVE?")
    print("=" * 78)
    print("  flow story predicts: 10Y spot yes, 5y5y little. premium story: both.\n")
    deps = ["spot10", "f5y5y", "f10y10y", "f20y10y", "TP10"]
    print(f"  {'dependent':10s} " + "  ".join(f"h={h}".rjust(16) for h in (0, 2, 5)))
    for dep in deps:
        cells = []
        for h in (0, 2, 5):
            lp = L.project(df, ai, dep=dep, hmax=h)
            r = lp[lp.h == h].iloc[0]
            cells.append(f"{r.b:+7.4f}({r.t:+5.2f})")
        print(f"  {dep:10s} " + "  ".join(c.rjust(16) for c in cells))

    print("\n  same, for Treasury buybacks (duration removal, sign should flip):")
    for dep in deps:
        cells = []
        for h in (0, 2, 5):
            lp = L.project(df, bb, dep=dep, hmax=h)
            r = lp[lp.h == h].iloc[0]
            cells.append(f"{r.b:+7.4f}({r.t:+5.2f})")
        print(f"  {dep:10s} " + "  ".join(c.rjust(16) for c in cells))

    # ---- how mechanical is each dependent variable relative to the 10Y?
    print("\n" + "=" * 78)
    print("HOW MECHANICALLY TIED TO THE CASH 10Y IS EACH DEPENDENT VARIABLE?")
    print("=" * 78)
    d10 = df.spot10.diff()
    for dep in ["TP10", "spot10", "f5y5y", "f10y10y", "f20y10y"]:
        y = df[dep].diff()
        ok = y.notna() & d10.notna()
        r2 = sm.OLS(y[ok], sm.add_constant(d10[ok])).fit().rsquared
        print(f"  R2 of d({dep}) on d(10Y spot): {r2:.3f}")
    print("\n  A dependent variable with R2 near 1 cannot distinguish a flow in the")
    print("  cash 10Y from a change in required compensation. 5y5y is the test.")

    # ---- ratio diagnostic
    print("\n" + "=" * 78)
    print("VERDICT DIAGNOSTIC")
    print("=" * 78)
    b10 = L.project(df, ai, dep="spot10", hmax=0).iloc[0]
    b55 = L.project(df, ai, dep="f5y5y", hmax=0).iloc[0]
    print(f"  AI h=0 on 10Y spot : {b10.b:+.4f} (t={b10.t:+.2f})")
    print(f"  AI h=0 on 5y5y fwd : {b55.b:+.4f} (t={b55.t:+.2f})")
    if abs(b10.b) > 1e-9:
        print(f"  ratio 5y5y / spot10 = {b55.b / b10.b:+.2f}")
        print("  near 0 => localised flow around the hedging point")
        print("  near 1 or above => the whole forward curve repriced")
