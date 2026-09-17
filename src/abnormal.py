"""An event-study statistic that survives smooth published curves.

The cross-sectional estimator in concession.py asks "is the bump local in TENOR",
which a 6-parameter fitted curve cannot answer. This module asks the question a
smooth curve can answer: "did the tenors the deal issued into cheapen by more
than the front end and breakevens imply", residualizing in the TIME series rather
than across the curve. Smoothing does not destroy that, because the same smooth
statistic is compared on event and non-event days.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, EVENT_WINDOW, N_PLACEBO, RANDOM_SEED
import curve as C
from concession import MAXT, tenor_weights

H = EVENT_WINDOW[1] - EVENT_WINDOW[0]     # 2 business days from t-1 to t+1

def panel():
    z = C.load_gsw(start="2024-01-01")
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    df = z.join(fred[["DGS2", "T10YIE", "VIXCLS", "DCOILWTICO"]], how="inner").ffill().dropna()
    return df, z.columns.tolist()

def hwin(s, h=H):
    """h-business-day change, in bp for yields."""
    return (s - s.shift(h)) * 100.0

def build_windows(df, tenors, h=H):
    out = pd.DataFrame(index=df.index)
    for t in tenors:
        out[f"dy{int(t)}"] = hwin(df[t], h)
    out["d2y"] = hwin(df["DGS2"], h)
    out["dbe"] = hwin(df["T10YIE"], h)
    out["dvix"] = df["VIXCLS"] - df["VIXCLS"].shift(h)
    out["doil"] = 100 * (np.log(df["DCOILWTICO"]) - np.log(df["DCOILWTICO"].shift(h)))
    return out.dropna()

def abnormal(events, tr, W, controls=("d2y", "dbe"), verbose=True, window=EVENT_WINDOW, h=H):
    """Fit the normal relation on NON-event windows, read the event residual."""
    ev_dates = [pd.Timestamp(a) for a in events.announce]
    idx = W.index
    ev_end = []
    for a in ev_dates:
        p = idx.searchsorted(a)
        p = min(p, len(idx) - 1)
        e = p + window[1]
        ev_end.append(idx[e] if e < len(idx) else None)
    # estimation sample: windows that do not overlap ANY event window
    contaminated = set()
    for e in ev_end:
        if e is None: continue
        p = idx.get_loc(e)
        contaminated |= {idx[j] for j in range(max(0, p - h - 1), min(len(idx), p + h + 2))}
    est = W[~W.index.isin(contaminated)]
    X = sm.add_constant(est[list(controls)])
    models = {}
    for t in range(1, MAXT + 1):
        models[t] = sm.OLS(est[f"dy{t}"], X).fit(cov_type="HAC",
                                                 cov_kwds={"maxlags": max(h,1), "use_correction": True})
    if verbose:
        m10 = models[10]
        print(f"  normal-relation sample: {len(est)} non-event {H}-bday windows")
        print(f"  10y on 2y/BE: beta2y={m10.params['d2y']:.3f} betaBE={m10.params['dbe']:.3f} "
              f"R2={m10.rsquared:.3f}  resid sd={np.std(m10.resid):.2f}bp")
    rows, det = [], []
    for (_, e), end in zip(events.iterrows(), ev_end):
        if end is None: continue
        w = W.loc[end]
        tw = tenor_weights(tr, e.issuer, e.announce)
        xa = np.array([1.0] + [w[c] for c in controls])
        num = den = 0.0
        for t, dur in tw.items():
            pred = float(models[t].params.values @ xa)
            res = w[f"dy{t}"] - pred
            det.append(dict(announce=e.announce, issuer=e.issuer, tenor=t,
                            dy_bp=w[f"dy{t}"], pred_bp=pred, abn_bp=res, dur_w=dur))
            num += dur * res; den += dur
        rows.append(dict(issuer=e.issuer, announce=e.announce, end=end,
                         total_usd=e.total_usd, dollar_dur=e.dollar_dur,
                         tenyr_equiv=e.tenyr_equiv, abn_bp=num / den,
                         dy10=w["dy10"], d2y=w["d2y"], dbe=w["dbe"]))
    return pd.DataFrame(rows), pd.DataFrame(det), models, est

def agg(res, col="abn_bp"):
    c, w = res[col].values, res.dollar_dur.values
    T = len(c); L = int(np.floor(4 * (T / 100) ** (2 / 9)))
    m = sm.WLS(c, np.ones((T, 1)), weights=w).fit(cov_type="HAC",
              cov_kwds={"maxlags": L, "use_correction": True})
    return dict(mean=float(np.average(c, weights=w)), unw=float(c.mean()),
                t=float(m.tvalues[0]), se=float(m.bse[0]), p=float(m.pvalues[0]), L=L, n=T)

def placebo(events, tr, W, models, n=N_PLACEBO, seed=RANDOM_SEED, controls=("d2y", "dbe")):
    rng = np.random.default_rng(seed)
    idx = W.index
    real = set()
    for a in events.announce:
        p = idx.searchsorted(pd.Timestamp(a)); p = min(p, len(idx) - 1)
        real |= {idx[j] for j in range(max(0, p - 5), min(len(idx), p + 6))}
    pool = np.array([i for i, d in enumerate(idx) if d not in real])
    specs = [(tenor_weights(tr, e.issuer, e.announce), e.dollar_dur) for _, e in events.iterrows()]
    out = []
    for _ in range(n):
        pick = rng.choice(pool, size=len(specs), replace=False)
        num = den = 0.0
        for (tw, dd), p in zip(specs, pick):
            w = W.iloc[p]
            xa = np.array([1.0] + [w[c] for c in controls])
            a = sum(dur * (w[f"dy{t}"] - float(models[t].params.values @ xa)) for t, dur in tw.items()) \
                / sum(tw.values())
            num += dd * a; den += dd
        out.append(num / den)
    return np.array(out)

if __name__ == "__main__":
    events = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    df, tenors = panel()
    W = build_windows(df, tenors)
    print("--- normal relation ---")
    res, det, models, est = abnormal(events, tr, W)
    pd.set_option("display.width", 250)
    print("\n--- per-event abnormal move at target tenors (bp, 3-bday window) ---")
    print(res[["issuer","announce","end","total_usd","dy10","d2y","dbe","abn_bp"]]
          .assign(total_usd=lambda x:(x.total_usd/1e9).round(1),
                  **{c:(lambda c: (lambda x: x[c].round(2)))(c) for c in ["dy10","d2y","dbe","abn_bp"]})
          .to_string(index=False))
    a = agg(res)
    print(f"\nX2 duration-weighted abnormal cheapening = {a['mean']:+.2f} bp  "
          f"(unweighted {a['unw']:+.2f})")
    print(f"   Newey-West t = {a['t']:+.2f} (L={a['L']}, se={a['se']:.2f}, p={a['p']:.3f}), N={a['n']}")
    pl = placebo(events, tr, W, models)
    print(f"   placebo ({len(pl)} draws): mean={pl.mean():+.3f} sd={pl.std():.2f} "
          f"95% CI [{np.percentile(pl,2.5):+.2f},{np.percentile(pl,97.5):+.2f}]")
    print(f"   two-sided placebo p-value = {float((np.abs(pl)>=abs(a['mean'])).mean()):.4f}")
    res.to_csv(PROC / "abnormal_events.csv", index=False)
    det.to_csv(PROC / "abnormal_detail.csv", index=False)
    np.save(PROC / "abnormal_placebo.npy", pl)
