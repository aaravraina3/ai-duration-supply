"""Is the supply effect on the term premium permanent or transitory?

The daily regression in regression.py says announced AI duration moves the ACM
term premium on the day. That is not the same as saying it explains the level of
the term premium a year later. Local projections settle it: regress the h-day
cumulative change in TP on the announcement-day duration shock, for h = 0..60,
and read the impulse response.

  TP_{t+h} - TP_{t-1} = a_h + b_h * shock_t + theta_h' Z_t + e_{t+h}

b_h is the effect h business days after a $1bn 10-year-equivalent announcement.
Overlapping windows make the residuals autocorrelated, so Newey-West uses
maxlags = h + 5.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, SAMPLE_END, JUMBO_USD
import regression as R

HMAX = 60


def shocks(jumbo_only=False):
    ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    if jumbo_only:
        ev = ev[ev.total_usd >= JUMBO_USD]
    s = ev.groupby("announce").tenyr_equiv.sum() / 1e9
    return s


def panel():
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    idx = acm.loc["2024-01-01":SAMPLE_END].index
    df = pd.DataFrame(index=idx)
    df["TP10"] = acm.ACMTP10 * 100
    df["RN10"] = acm.ACMRNY10 * 100
    df["Y10"] = acm.ACMY10 * 100
    df["dbe"] = fred.T10YIE.reindex(idx).ffill().diff() * 100
    df["dvix"] = fred.VIXCLS.reindex(idx).ffill().diff()
    df["doil"] = 100 * np.log(fred.DCOILWTICO.reindex(idx).ffill()).diff()
    T = R.treasury_supply()
    for c in ["auc_10y", "auc_surprise"]:
        df[c] = T[c].reindex(idx).fillna(0.0)
    return df.dropna()


def project(df, sh, dep="TP10", hmax=HMAX, ctrl=("dbe", "doil", "dvix", "auc_10y")):
    x = sh.reindex(df.index).fillna(0.0)
    rows = []
    for h in range(0, hmax + 1):
        y = df[dep].shift(-h) - df[dep].shift(1)
        X = pd.DataFrame({"shock": x})
        for c in ctrl:
            X[c] = df[c]
        X = sm.add_constant(X)
        ok = y.notna() & X.notna().all(axis=1)
        m = sm.OLS(y[ok], X[ok]).fit(cov_type="HAC",
                                     cov_kwds={"maxlags": h + 5, "use_correction": True})
        rows.append(dict(h=h, b=m.params["shock"], se=m.bse["shock"],
                         t=m.tvalues["shock"], p=m.pvalues["shock"], n=int(m.nobs)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = panel()
    for jumbo in (False, True):
        sh = shocks(jumbo_only=jumbo)
        lab = "jumbo only" if jumbo else "all USD deals"
        print(f"\n=== local projection, {lab} (n_shocks={len(sh)}, "
              f"total {sh.sum():.0f} $bn 10y-equiv) ===")
        for dep in ("TP10", "RN10"):
            lp = project(df, sh, dep=dep)
            print(f"\n  dep = {dep}   (bp per $bn 10y-equivalent)")
            print(f"  {'h':>4} {'b_h':>9} {'se':>8} {'t':>7} {'p':>7}")
            for h in [0, 1, 2, 3, 5, 10, 20, 30, 45, 60]:
                r = lp[lp.h == h].iloc[0]
                print(f"  {h:4d} {r.b:9.4f} {r.se:8.4f} {r.t:7.2f} {r.p:7.3f}")
            if dep == "TP10":
                pk = lp.loc[lp.b.abs().idxmax()]
                print(f"  peak |b| at h={int(pk.h)}: {pk.b:+.4f} bp/$bn (t={pk.t:.2f})")
                lp.to_csv(PROC / f"localproj_{'jumbo' if jumbo else 'all'}.csv", index=False)

    # -------------------------------------------------- 2026 attribution
    print("\n" + "=" * 78)
    ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    e26 = ev[ev.announce >= "2026-01-01"]
    tot = e26.tenyr_equiv.sum() / 1e9
    lp = pd.read_csv(PROC / "localproj_all.csv")
    print(f"2026 USD AI issuance: ${e26.total_usd.sum()/1e9:.1f}B face, "
          f"{tot:.0f} $bn 10-year-equivalent duration, {len(e26)} deals")
    for h in (0, 5, 20, 60):
        b = lp[lp.h == h].iloc[0]
        print(f"  h={h:2d}: implied cumulative dTP from 2026 supply = "
              f"{b.b*tot:+6.1f} bp   (b={b.b:+.4f}, t={b.t:.2f})")
