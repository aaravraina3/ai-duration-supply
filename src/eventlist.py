"""Step 4: deals -> events. Applies the pre-registered filters from config.py
in a fixed order and logs every drop, so the funnel is auditable."""
import numpy as np, pandas as pd
from config import (PROC, JUMBO_USD, MACRO_EXCL_BDAYS, CLUSTER_MERGE_BDAYS, SAMPLE_START)
from deals import build_deals

def mod_duration(tenor, coupon, floating=False):
    """Modified duration of a semiannual bullet priced at par. A floater resets
    quarterly, so its rate duration is ~0.25y, not its maturity."""
    if floating or coupon is None:
        return 0.25
    y = c = coupon / 100.0
    n = int(round(tenor * 2))
    if n <= 0: return 0.0
    t = np.arange(1, n + 1) / 2.0
    cf = np.full(n, c / 2 * 100.0); cf[-1] += 100.0
    df = (1 + y / 2) ** (-np.arange(1, n + 1))
    P = (cf * df).sum()
    mac = (t * cf * df).sum() / P
    return mac / (1 + y / 2)

DUR10 = mod_duration(10, 4.5)     # 10-year-equivalent denominator, fixed

def build():
    d = build_deals()
    rows = []
    for _, r in d.iterrows():
        ann = pd.Timestamp(r.announce)
        for t in r.tranches:
            tenor = t["mat_year"] - ann.year
            md = mod_duration(tenor, t["coupon"], t["floating"])
            rows.append(dict(issuer=r.issuer, announce=ann, final_filing=r.final_filing,
                             tenor=tenor, coupon=t["coupon"], floating=t["floating"],
                             notional=t["notional"], mod_dur=md,
                             dollar_dur=t["notional"] * md,
                             tenyr_equiv=t["notional"] * md / DUR10))
    tr = pd.DataFrame(rows)
    tr.to_csv(PROC / "tranches.csv", index=False)

    g = tr.groupby(["issuer", "announce"], as_index=False).agg(
        total_usd=("notional", "sum"), n_tranches=("notional", "size"),
        dollar_dur=("dollar_dur", "sum"), tenyr_equiv=("tenyr_equiv", "sum"),
        max_tenor=("tenor", "max"), wavg_tenor=("tenor", lambda s: np.nan))
    # duration-weighted average tenor
    w = tr.groupby(["issuer", "announce"]).apply(
        lambda x: np.average(x.tenor, weights=x.dollar_dur) if x.dollar_dur.sum() > 0 else np.nan,
        include_groups=False).rename("wavg_tenor")
    g = g.drop(columns="wavg_tenor").merge(w, on=["issuer", "announce"])
    g["target_tenors"] = [sorted(set(tr[(tr.issuer == i) & (tr.announce == a) & (~tr.floating)].tenor))
                          for i, a in zip(g.issuer, g.announce)]
    return g.sort_values("announce").reset_index(drop=True), tr

def filter_events(g, verbose=True, excl=None, jumbo=None, merge=None):
    excl  = MACRO_EXCL_BDAYS   if excl  is None else excl
    jumbo = JUMBO_USD          if jumbo is None else jumbo
    merge = CLUSTER_MERGE_BDAYS if merge is None else merge
    cal = pd.read_csv(PROC / "macro_calendar.csv", parse_dates=["date"])
    log = []
    g = g[g.announce >= SAMPLE_START].copy()
    log.append(("in sample window", len(g)))

    g["jumbo"] = g.total_usd >= jumbo
    log.append((f"total >= ${jumbo/1e9:.0f}B", int(g.jumbo.sum())))

    bd = pd.bdate_range(SAMPLE_START, "2026-12-31")
    pos = {d: i for i, d in enumerate(bd)}
    macro_pos = sorted({pos[d] for d in cal.date if d in pos})
    def near_macro(a):
        i = pos.get(pd.Timestamp(a))
        if i is None: return True
        return any(abs(i - m) <= excl for m in macro_pos)
    g["macro_conflict"] = g.announce.map(near_macro)
    g["macro_which"] = [
        ", ".join(f"{k}@{str(dd.date())}" for dd, k in zip(cal.date, cal.kind)
                  if abs((pd.Timestamp(a) - dd).days) <= excl + 5
                  and abs(pos.get(pd.Timestamp(a), 10**6) - pos.get(dd, -10**6)) <= excl)
        for a in g.announce]
    keep = g[g.jumbo & ~g.macro_conflict].copy()
    log.append((f"and >{excl} bdays from FOMC/CPI/NFP", len(keep)))

    # merge clustered jumbos
    keep = keep.sort_values("announce").reset_index(drop=True)
    grp, cur = [], 0
    for i in range(len(keep)):
        if i and len(pd.bdate_range(keep.announce[i-1], keep.announce[i])) - 1 <= merge:
            pass
        else:
            cur += 1
        grp.append(cur)
    keep["cluster"] = grp
    merged = keep.groupby("cluster").agg(
        issuer=("issuer", lambda s: "+".join(sorted(set(s)))),
        announce=("announce", "min"), total_usd=("total_usd", "sum"),
        n_tranches=("n_tranches", "sum"), dollar_dur=("dollar_dur", "sum"),
        tenyr_equiv=("tenyr_equiv", "sum"), max_tenor=("max_tenor", "max"),
        wavg_tenor=("wavg_tenor", "mean"), n_deals=("issuer", "size"),
        target_tenors=("target_tenors", lambda s: sorted({t for x in s for t in x})),
    ).reset_index(drop=True)
    log.append((f"after merging jumbos <= {merge} bdays apart", len(merged)))
    if verbose:
        print("\n--- event funnel ---")
        for k, v in log: print(f"  {k:52s} {v:3d}")
    return merged, g

if __name__ == "__main__":
    g, tr = build()
    pd.set_option("display.width", 260, "display.max_columns", 30)
    print("--- all USD deals ---")
    print(g.assign(total=lambda x:(x.total_usd/1e9).round(2), d10=lambda x:(x.tenyr_equiv/1e9).round(1))
           [["issuer","announce","total","n_tranches","d10","wavg_tenor","max_tenor","target_tenors"]].to_string(index=False))
    ev, allg = filter_events(g)
    print("\n--- final event sample ---")
    print(ev.assign(total=lambda x:(x.total_usd/1e9).round(2), d10=lambda x:(x.tenyr_equiv/1e9).round(1))
            [["issuer","announce","total","n_deals","d10","wavg_tenor","target_tenors"]].to_string(index=False))
    ev.to_csv(PROC / "events.csv", index=False)
    allg.to_csv(PROC / "deals_all.csv", index=False)
    print("\ndropped for macro proximity:")
    for _, r in allg[allg.jumbo & allg.macro_conflict].iterrows():
        print(f"  {r.issuer:10s} {str(r.announce.date())} ${r.total_usd/1e9:5.1f}B  <- {r.macro_which}")
