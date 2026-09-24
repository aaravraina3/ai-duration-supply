"""Is the announcement effect risk compensation, or dealer hedging flow?

REVISED 23 SEP after the adversarial review (research/09, F1).

The first version separated flow from premium using a 20y10y forward built from
GSW. That failed: GSW is a Svensson fit with few bonds past 20 years, so its far
forward is dominated by parameter noise. Its R2 with the cash 10Y was 0.063; the
same forward built from observed CMT points has R2 = 0.623, and the two versions
correlate at 0.384. The "orthogonal segment" was an extrapolation artifact.

This version does three things.

1. CMT FORWARDS ARE PRIMARY. Forwards are built from FRED constant-maturity
   points, which are anchored on traded securities at each tenor. GSW versions
   are kept only to show the artifact.

2. A NEW FLOW TEST THAT NEEDS NO SWAP DATA: THE ON-THE-RUN SPREAD.
   Rate-lock hedges around new corporate issues are put on by selling the most
   liquid Treasuries, which are the on-the-run issues (or futures, which track
   them). FRED CMT is built from on-the-run securities. GSW explicitly excludes
   on-the-runs and first off-the-runs and fits only seasoned paper. So

       otr_spread(n)  =  CMT par yield(n)  -  GSW par yield(n)   [SVENPY]

   is a proxy for the on-the-run's cheapness relative to seasoned bonds, in the
   same par convention.

   PREDICTIONS, written before running:
     hedging flow        -> on-the-runs are sold -> otr_spread RISES on deal days
     premium repricing   -> all bonds reprice together -> otr_spread ~ unchanged
     Treasury buybacks   -> Treasury buys OFF-the-runs -> GSW yields fall
                            -> otr_spread RISES

   Caveats, also written before running: CMT is interpolated between on-the-run
   points, GSW has its own fitting error, and the on-the-run premium resets at
   every auction, so auction-day supply is controlled for. At 10y the GSW fit is
   well constrained, unlike the far forward, so the 10y spread is the primary.

3. TIPS. A pure nominal rate-lock flow should move nominal yields more than real
   yields. A broad repricing of duration risk should move both. The LP is run on
   the 10Y real yield (DFII10) as a secondary check. This is weak evidence either
   way: TIPS are arbitraged against nominals and breakevens absorb the gap.
"""
import numpy as np, pandas as pd, statsmodels.api as sm, requests, io
from config import PROC, RAW
import curve as C, localproj as L


def _gsw_par(start="2024-01-01"):
    g = pd.read_csv(PROC / "gsw.csv", parse_dates=["Date"]).set_index("Date")
    g.index.name = "date"
    return g[[c for c in g.columns if c.startswith("SVENPY")]].loc[start:]


def _fred_series(sid):
    p = RAW / f"fred_{sid}.csv"
    if not p.exists():
        r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=90)
        r.raise_for_status(); p.write_bytes(r.content)
    d = pd.read_csv(p); d.columns = ["date", sid]
    d["date"] = pd.to_datetime(d.date); d[sid] = pd.to_numeric(d[sid], errors="coerce")
    return d.set_index("date")[sid]


def forwards():
    """GSW zero-curve forwards, kept to document the artifact. Do not use as primary."""
    z = C.load_gsw(start="2024-01-01")
    f = pd.DataFrame(index=z.index)
    f["gsw_f5y5y"] = (10 * z[10.0] - 5 * z[5.0]) / 5 * 100
    f["gsw_f10y10y"] = (20 * z[20.0] - 10 * z[10.0]) / 10 * 100
    f["gsw_f20y10y"] = (30 * z[30.0] - 20 * z[20.0]) / 10 * 100
    return f


def panel():
    p = L.panel()
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    fr = fred.reindex(p.index).ffill()
    # primary: forwards from observed CMT par points (par-yield approximation)
    p["spot10"] = fr.DGS10 * 100
    p["f5y5y"] = (10 * fr.DGS10 - 5 * fr.DGS5) / 5 * 100
    p["f10y10y"] = (20 * fr.DGS20 - 10 * fr.DGS10) / 10 * 100
    p["f20y10y"] = (30 * fr.DGS30 - 20 * fr.DGS20) / 10 * 100
    # GSW versions, for the artifact comparison only
    p = p.join(forwards().reindex(p.index).ffill())
    # on-the-run spread: CMT (on-the-run based) minus GSW par (seasoned paper only)
    gp = _gsw_par().reindex(p.index)
    for n, col in [(10, "DGS10"), (20, "DGS20"), (30, "DGS30")]:
        p[f"otr{n}"] = (fr[col] - gp[f"SVENPY{n:02d}"]) * 100
    # real yield
    p["real10"] = _fred_series("DFII10").reindex(p.index).ffill() * 100
    return p


def lp_row(df, shock, dep, h, extra_ctrl=()):
    # no dropna here: dropping mid-sample gaps would make shift(-h) span extra
    # calendar days. project() masks missing values itself.
    ctrl = ("dbe", "doil", "dvix", "auc_10y") + tuple(extra_ctrl)
    r = L.project(df, shock[shock.index.isin(df.index)], dep=dep, hmax=h, ctrl=ctrl)
    return r[r.h == h].iloc[0]


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    df = panel()
    ai = L.shocks(); ai = ai[ai.index.isin(df.index)]
    bbd = pd.read_csv(PROC / "buybacks_daily.csv", parse_dates=["date"]).set_index("date")
    bb = bbd.bb_long[bbd.bb_long > 0]
    bbs = bbd.bb_long_surprise[bbd.bb_long_surprise != 0]

    print("=" * 78)
    print("1. FORWARDS: observed CMT (primary) vs GSW Svensson (the artifact)")
    print("=" * 78)
    d10 = df.spot10.diff()
    print(f"  {'dependent':12s} {'R2 vs d10Y':>10} {'AI h0':>18} {'AI h2':>18} {'buyback h0':>18}")
    for dep in ["spot10", "f5y5y", "f10y10y", "f20y10y", "gsw_f10y10y", "gsw_f20y10y", "TP10"]:
        y = df[dep].diff(); ok = y.notna() & d10.notna()
        r2 = sm.OLS(y[ok], sm.add_constant(d10[ok])).fit().rsquared
        a0, a2, b0 = lp_row(df, ai, dep, 0), lp_row(df, ai, dep, 2), lp_row(df, bb, dep, 0)
        print(f"  {dep:12s} {r2:10.3f} {a0.b:+8.4f}({a0.t:+5.2f}) {a2.b:+8.4f}({a2.t:+5.2f}) "
              f"{b0.b:+8.4f}({b0.t:+5.2f})")
    c = df[["gsw_f20y10y", "f20y10y"]].diff().dropna().corr().iloc[0, 1]
    print(f"\n  corr of daily changes, GSW vs CMT 20y10y: {c:.3f}")
    print("  On observed points no forward is close to orthogonal to the 10Y, so the")
    print("  forward curve cannot separate a cash-market flow from a premium repricing.")

    print("\n" + "=" * 78)
    print("2. ON-THE-RUN SPREAD: CMT par minus GSW (seasoned-only) par")
    print("=" * 78)
    print("  flow predicts RISE on deal days; premium repricing predicts ~0;")
    print("  buybacks (Treasury buys off-the-runs) predict RISE.\n")
    for n in (10, 20, 30):
        s = df[f"otr{n}"]
        print(f"  otr{n}: mean {s.mean():+.2f} bp, sd of daily change {s.diff().std():.2f} bp, "
              f"n={s.notna().sum()}")
    rows = []
    print(f"\n  {'dependent':8s} {'shock':18s} {'h0':>17} {'h1':>17} {'h2':>17}")
    for dep in ["otr10", "otr20", "otr30"]:
        for lab, sh in [("AI issuance", ai), ("buybacks raw", bb), ("buybacks surprise", bbs)]:
            cells = []
            for h in (0, 1, 2):
                r = lp_row(df, sh, dep, h)
                cells.append(f"{r.b:+8.4f}({r.t:+5.2f})")
                rows.append(dict(dep=dep, shock=lab, h=h, b=r.b, t=r.t))
            print(f"  {dep:8s} {lab:18s} " + " ".join(c.rjust(17) for c in cells))
    pd.DataFrame(rows).to_csv(PROC / "otr_spread_lp.csv", index=False)

    print("\n" + "=" * 78)
    print("3. REAL YIELD (TIPS): does the effect reach real yields too?")
    print("=" * 78)
    for dep in ["spot10", "real10"]:
        cells = []
        for h in (0, 2):
            r = lp_row(df, ai, dep, h)
            cells.append(f"h{h} {r.b:+.4f} (t{r.t:+.2f})")
        print(f"  {dep:8s} " + "   ".join(cells))
    a_nom = lp_row(df, ai, "spot10", 0).b; a_real = lp_row(df, ai, "real10", 0).b
    print(f"  real / nominal response at h0 = {a_real / a_nom:.2f}")
    df.to_csv(PROC / "hedgeflow_panel.csv")
