"""Phase 1: Treasury buybacks as the mirror image of corporate issuance.

Treasury removes long-end duration on announced, dated days, in the same market,
at the same daily frequency as a jumbo corporate deal adds it. If the term
premium responds to duration absorption, the buyback coefficient must be
NEGATIVE and comparable in magnitude per $bn to the issuance coefficient. If it
is zero or positive, the issuance result is more likely a dealer hedging flow
than a change in required risk compensation.

Pre-registered before running (see research/02_HYPOTHESES.md H7):
  expected sign  : negative
  expected scale : same order as +0.080 bp per $bn 10-year-equivalent
  decision rule  : zero-or-positive => demote H1 to a flow finding

Treasury doubled 10Y-30Y operation sizes to at least $4B effective 2026-09-09.
"""
import json, numpy as np, pandas as pd, requests, statsmodels.api as sm
from config import RAW, PROC, SEC_UA
from eventlist import mod_duration, DUR10

URL = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/"
       "accounting/od/buybacks_operations?page%5Bsize%5D=1000&sort=-operation_date")

# Bucket midpoints. Treasury reports a range, not a tenor, so the midpoint is an
# assumption. Recorded here rather than buried; sensitivity is run in main().
BUCKET_MID = {
    "1Mo to 2Y": 1.0, "2Y to 3Y": 2.5, "3Y to 5Y": 4.0, "5Y to 7Y": 6.0,
    "7Y to 10Y": 8.5, "10Y to 20Y": 15.0, "20Y to 30Y": 25.0, "10Y to 30Y": 20.0,
}
LONG_BUCKETS = {"7Y to 10Y", "10Y to 20Y", "20Y to 30Y", "10Y to 30Y"}


def fetch():
    p = RAW / "buybacks.json"
    if not p.exists():
        r = requests.get(URL, headers={"User-Agent": SEC_UA}, timeout=180)
        r.raise_for_status(); p.write_bytes(r.content)
    return pd.DataFrame(json.loads(p.read_text())["data"])


def build(edge=0.0):
    """edge shifts the bucket midpoint assumption, for sensitivity."""
    d = fetch()
    d["operation_date"] = pd.to_datetime(d.operation_date)
    d["par"] = pd.to_numeric(d.total_par_amt_accepted, errors="coerce")
    d = d[d.par > 0].copy()
    d["tenor"] = d.maturity_bucket.map(BUCKET_MID) + edge
    d = d.dropna(subset=["tenor"])
    d["dur"] = d.tenor.map(lambda t: mod_duration(t, 4.5))
    d["ten10"] = d.par * d.dur / DUR10 / 1e9          # $bn of 10-year equivalents
    d["is_long"] = d.maturity_bucket.isin(LONG_BUCKETS)
    return d


def daily_series(d, start="2024-01-01", end="2026-09-18"):
    idx = pd.bdate_range(start, end)
    g = d[d.is_long].groupby("operation_date").ten10.sum()
    a = d.groupby("operation_date").ten10.sum()
    return pd.DataFrame({
        "bb_long": g.reindex(idx).fillna(0.0),
        "bb_all": a.reindex(idx).fillna(0.0),
    }).rename_axis("date")


if __name__ == "__main__":
    import regression as R, localproj as L
    pd.set_option("display.width", 220)
    d = build()
    print("=" * 76)
    print("TREASURY BUYBACK OPERATIONS")
    print("=" * 76)
    print(f"  operations: {len(d)}  {d.operation_date.min().date()} -> {d.operation_date.max().date()}")
    s = d[d.operation_date >= "2024-01-01"]
    print(f"  since 2024: {len(s)} ops, {s.ten10.sum():.1f} $bn 10y-equiv removed "
          f"({s[s.is_long].ten10.sum():.1f} $bn from long buckets)")
    print("\n  by maturity bucket, 2024 onward:")
    print(s.groupby("maturity_bucket").agg(ops=("par", "size"), par_bn=("par", lambda x: x.sum()/1e9),
                                           ten10_bn=("ten10", "sum")).round(1).to_string())

    print("\n  the 2026-09-09 size doubling, long buckets only:")
    lg = s[s.is_long].copy()
    pre = lg[lg.operation_date < "2026-09-09"]; post = lg[lg.operation_date >= "2026-09-09"]
    print(f"    before: {len(pre):3d} ops, mean par ${pre.par.mean()/1e9:.2f}B, "
          f"mean 10y-equiv {pre.ten10.mean():.2f} $bn")
    print(f"    after : {len(post):3d} ops, mean par ${post.par.mean()/1e9:.2f}B, "
          f"mean 10y-equiv {post.ten10.mean():.2f} $bn")

    # ---------------------------------------------------- the mirror regression
    bb = daily_series(d)
    df = R.dataset().join(bb, how="left").fillna({"bb_long": 0.0, "bb_all": 0.0})
    print("\n" + "=" * 76)
    print("THE MIRROR TEST: issuance and buybacks in the same regression")
    print("=" * 76)
    print(f"  sample {df.index.min().date()} -> {df.index.max().date()}, n={len(df)}")
    print(f"  AI supply     : {df.dD[df.dD>0].sum():7.1f} $bn 10y-equiv added (announcement days)")
    print(f"  buybacks long : {df.bb_long.sum():7.1f} $bn 10y-equiv removed")

    for label, cols in [("AI only", ["dD"]),
                        ("buyback long only", ["bb_long"]),
                        ("both", ["dD", "bb_long"]),
                        ("both + all-maturity buybacks", ["dD", "bb_all"])]:
        X = sm.add_constant(df[cols + R.CTRL])
        m = sm.OLS(df.dTP10, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": True})
        parts = "  ".join(f"{c}={m.params[c]:+.4f} (t={m.tvalues[c]:+.2f})" for c in cols)
        print(f"\n  {label:30s} {parts}")

    # ---------------------------------------------------- impulse responses
    print("\n" + "=" * 76)
    print("IMPULSE RESPONSES, same spec both sides (bp per $bn 10y-equiv)")
    print("=" * 76)
    pnl = L.panel()
    ai_sh = L.shocks()
    bb_sh = df.bb_long[df.bb_long > 0]
    print(f"  {'h':>3} {'AI b':>9} {'AI t':>7} | {'buyback b':>10} {'bb t':>7}")
    rows = []
    for h in (0, 1, 2, 3, 5, 10, 20):
        a = L.project(pnl, ai_sh, dep="TP10", hmax=h); a = a[a.h == h].iloc[0]
        b = L.project(pnl, bb_sh, dep="TP10", hmax=h); b = b[b.h == h].iloc[0]
        rows.append(dict(h=h, ai_b=a.b, ai_t=a.t, bb_b=b.b, bb_t=b.t))
        print(f"  {h:3d} {a.b:9.4f} {a.t:7.2f} | {b.b:10.4f} {b.t:7.2f}")
    pd.DataFrame(rows).to_csv(PROC / "buyback_vs_ai_lp.csv", index=False)

    # ---------------------------------------------------- randomization test
    print("\n  randomization test on the buyback h=0 coefficient:")
    rng = np.random.default_rng(20261015)
    idxs = pnl.index
    real = set()
    for a in bb_sh.index:
        p = idxs.searchsorted(a)
        real |= {idxs[j] for j in range(max(0, p - 5), min(len(idxs), p + 6))}
    pool = np.array([i for i, x in enumerate(idxs) if x not in real and 5 < i < len(idxs) - 65])
    obs = L.project(pnl, bb_sh, dep="TP10", hmax=0).iloc[0].b
    draws = []
    for _ in range(500):
        pick = rng.choice(pool, size=len(bb_sh), replace=False)
        fake = pd.Series(bb_sh.values, index=idxs[pick]).groupby(level=0).sum()
        draws.append(L.project(pnl, fake, dep="TP10", hmax=0).iloc[0].b)
    dr = np.array(draws)
    print(f"    observed {obs:+.4f} | placebo mean {dr.mean():+.4f} sd {dr.std():.4f} "
          f"p={np.mean(np.abs(dr) >= abs(obs)):.4f}")

    # ---------------------------------------------------- bucket sensitivity
    print("\n  bucket-midpoint sensitivity (h=0 buyback coefficient):")
    for e in (-2.0, 0.0, +2.0):
        de = build(edge=e); bbe = daily_series(de).bb_long
        se = bbe[bbe > 0]
        r = L.project(pnl, se, dep="TP10", hmax=0).iloc[0]
        print(f"    midpoint {e:+.0f}y: b={r.b:+.4f} t={r.t:+.2f}")

    daily_series(d).to_csv(PROC / "buybacks_daily.csv")
