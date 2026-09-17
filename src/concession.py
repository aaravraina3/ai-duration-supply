"""§4.4 concession measurement.

For each event, take the event-window change in the zero curve, project it onto
the three PCA loading shapes using ONLY tenors far from the deal's tranches, then
read the out-of-sample residual at the tenors the deal actually issued into.
Positive residual = the target tenors cheapened beyond the curve-wide move.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, EXCL_BAND_YEARS, EVENT_WINDOW, N_PLACEBO, RANDOM_SEED, MACRO_EXCL_BDAYS
import curve as C

MAXT = 30      # no Treasury beyond 30y; a 40y corporate tranche hedges at the 30y point

def loadings(z):
    _, V, ev, _ = C.pca_factors(z)
    return V[:, :3], ev

def event_window_change(z, ann, w=EVENT_WINDOW):
    idx = z.index
    pos = idx.searchsorted(pd.Timestamp(ann))
    if pos >= len(idx) or idx[pos] != pd.Timestamp(ann):
        pos = min(pos, len(idx) - 1)          # announcement on a non-quote day
    i0, i1 = pos + w[0], pos + w[1]
    if i0 < 0 or i1 >= len(idx): return None, None, None
    return (z.iloc[i1] - z.iloc[i0]) * 100.0, idx[i0], idx[i1]   # bp

def split_tenors(targets, band=EXCL_BAND_YEARS, tenors=None):
    tenors = np.arange(1, MAXT + 1) if tenors is None else np.asarray(tenors)
    tg = sorted({min(t, MAXT) for t in targets})
    dist = np.array([min(abs(t - g) for g in tg) for t in tenors])
    return tenors[dist == 0], tenors[dist > band], tg

def concession_for(dy, targets, V, tenors=None, band=EXCL_BAND_YEARS):
    """Fit a+b*f1+c*f2+d*f3 on control tenors, predict at target tenors."""
    tenors = np.arange(1, MAXT + 1) if tenors is None else np.asarray(tenors)
    tgt, ctl, tg = split_tenors(targets, band=band, tenors=tenors)
    if len(ctl) < 6: return None
    ti = {t: i for i, t in enumerate(tenors)}
    X = np.column_stack([np.ones(len(tenors)), V[:, 0], V[:, 1], V[:, 2]])
    ci = [ti[t] for t in ctl]
    beta, *_ = np.linalg.lstsq(X[ci], dy.values[ci], rcond=None)
    pred = X @ beta
    resid = dy.values - pred
    return dict(tenors=tenors, targets=tg, ctl=ctl, resid=resid, pred=pred,
                r2_ctl=1 - ((dy.values[ci]-pred[ci])**2).sum() /
                           ((dy.values[ci]-dy.values[ci].mean())**2).sum())

def tenor_weights(tr, issuer, ann):
    """Dollar duration the deal supplies at each (capped) target tenor."""
    d = tr[(tr.announce == pd.Timestamp(ann)) & (~tr.floating)]
    if issuer and "+" not in issuer:
        d = d[d.issuer == issuer]
    w = {}
    for _, r in d.iterrows():
        w[min(int(r.tenor), MAXT)] = w.get(min(int(r.tenor), MAXT), 0.0) + r.dollar_dur
    return w

def run(events, tr, z, V, window=EVENT_WINDOW, band=EXCL_BAND_YEARS):
    rows, detail = [], []
    for _, e in events.iterrows():
        dy, d0, d1 = event_window_change(z, e.announce, w=window)
        if dy is None: continue
        tw = tenor_weights(tr, e.issuer, e.announce)
        out = concession_for(dy, list(tw), V, band=band)
        if out is None: continue
        ti = {t: i for i, t in enumerate(out["tenors"])}
        num = sum(tw[t] * out["resid"][ti[t]] for t in out["targets"])
        den = sum(tw[t] for t in out["targets"])
        ce = num / den
        rows.append(dict(issuer=e.issuer, announce=e.announce, d0=d0, d1=d1,
                         total_usd=e.total_usd, dollar_dur=e.dollar_dur,
                         tenyr_equiv=e.tenyr_equiv, concession_bp=ce,
                         dy10=dy[10.0], n_ctl=len(out["ctl"]), r2_ctl=out["r2_ctl"],
                         targets=out["targets"]))
        for t in out["targets"]:
            detail.append(dict(announce=e.announce, issuer=e.issuer, tenor=t,
                               dy_bp=dy[float(t)], pred_bp=out["pred"][ti[t]],
                               resid_bp=out["resid"][ti[t]], dur_w=tw[t]))
    return pd.DataFrame(rows), pd.DataFrame(detail)

def aggregate(ev):
    w = ev.dollar_dur.values
    c = ev.concession_bp.values
    cbar = float(np.average(c, weights=w))
    # Newey-West on the event series (WLS of concession on a constant)
    T = len(c); L = int(np.floor(4 * (T / 100) ** (2 / 9)))
    m = sm.WLS(c, np.ones((T, 1)), weights=w).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": True})
    simple = sm.OLS(c, np.ones((T, 1))).fit()
    return dict(cbar=cbar, nw_t=float(m.tvalues[0]), nw_se=float(m.bse[0]), nw_lags=L,
                nw_p=float(m.pvalues[0]), unweighted=float(c.mean()),
                ols_t=float(simple.tvalues[0]), n=T)

def placebo(events, tr, z, V, n=N_PLACEBO, seed=RANDOM_SEED, exclude=None):
    """Randomize event dates, keep each deal's target tenors and duration weights."""
    rng = np.random.default_rng(seed)
    idx = z.index
    lo, hi = 5, len(idx) - 5
    real = {pd.Timestamp(a) for a in events.announce}
    banned = set()
    for a in real:
        p = idx.searchsorted(a)
        banned |= {idx[j] for j in range(max(0, p - 5), min(len(idx), p + 6))}
    if exclude is not None:
        banned |= set(exclude)
    pool = np.array([i for i in range(lo, hi) if idx[i] not in banned])
    specs = []
    for _, e in events.iterrows():
        tw = tenor_weights(tr, e.issuer, e.announce)
        specs.append((tw, e.dollar_dur))
    out = []
    for _ in range(n):
        pick = rng.choice(pool, size=len(specs), replace=False)
        num = den = 0.0
        for (tw, dd), p in zip(specs, pick):
            dy = (z.iloc[p + EVENT_WINDOW[1]] - z.iloc[p + EVENT_WINDOW[0]]) * 100.0
            o = concession_for(dy, list(tw), V)
            if o is None: continue
            ti = {t: i for i, t in enumerate(o["tenors"])}
            ce = sum(tw[t] * o["resid"][ti[t]] for t in o["targets"]) / sum(tw[t] for t in o["targets"])
            num += dd * ce; den += dd
        if den: out.append(num / den)
    return np.array(out)

if __name__ == "__main__":
    events = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    z = C.load_gsw(start="2024-01-01")
    V, ev_share = loadings(z)
    res, det = run(events, tr, z, V)
    pd.set_option("display.width", 260)
    print("--- per-event concession (bp) ---")
    print(res[["issuer","announce","d0","d1","total_usd","concession_bp","dy10","n_ctl","r2_ctl","targets"]]
          .assign(total_usd=lambda x:(x.total_usd/1e9).round(1),
                  concession_bp=lambda x:x.concession_bp.round(2),
                  dy10=lambda x:x.dy10.round(2), r2_ctl=lambda x:x.r2_ctl.round(3)).to_string(index=False))
    agg = aggregate(res)
    print(f"\nX  duration-weighted mean concession = {agg['cbar']:+.2f} bp")
    print(f"   unweighted mean                   = {agg['unweighted']:+.2f} bp")
    print(f"   Newey-West t = {agg['nw_t']:+.2f} (L={agg['nw_lags']}, se={agg['nw_se']:.2f}, p={agg['nw_p']:.3f}), N={agg['n']}")
    pl = placebo(events, tr, z, V)
    p2 = float((np.abs(pl) >= abs(agg['cbar'])).mean())
    print(f"\n   placebo ({len(pl)} draws): mean={pl.mean():+.3f} bp, sd={pl.std():.2f}, "
          f"95% CI [{np.percentile(pl,2.5):+.2f},{np.percentile(pl,97.5):+.2f}]")
    print(f"   two-sided placebo p-value for X   = {p2:.4f}")
    res.to_csv(PROC / "concessions.csv", index=False)
    det.to_csv(PROC / "concession_detail.csv", index=False)
    np.save(PROC / "placebo.npy", pl)
