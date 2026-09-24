"""Week 4: vary every researcher degree of freedom and report the whole grid,
including the specifications that kill the result.

Varied: jumbo threshold, macro-exclusion width, event window, tenor exclusion
band, HMM state count, and the choice of curve.
"""
import numpy as np, pandas as pd
from config import PROC, TAB, JUMBO_USD, EXCL_BAND_YEARS, EVENT_WINDOW, MACRO_EXCL_BDAYS
import curve as C, concession as K, abnormal as A, eventlist as E


def spec_grid():
    g, tr = E.build()
    z = C.load_gsw(start="2024-01-01")
    V, _ = K.loadings(z)
    df, tn = A.panel()
    rows = []

    def one(label, excl=MACRO_EXCL_BDAYS, jumbo=JUMBO_USD, window=EVENT_WINDOW,
            band=EXCL_BAND_YEARS):
        ev, _ = E.filter_events(g, verbose=False, excl=excl, jumbo=jumbo)
        if len(ev) < 3:
            rows.append(dict(spec=label, N=len(ev), X_pca=np.nan, t_pca=np.nan,
                             X_abn=np.nan, t_abn=np.nan))
            return
        res, _ = K.run(ev, tr, z, V, window=window, band=band)
        a1 = K.aggregate(res)
        h = window[1] - window[0]
        W = A.build_windows(df, tn, h=h)
        res2, _, _, _ = A.abnormal(ev, tr, W, verbose=False, window=window, h=h)
        a2 = A.agg(res2)
        rows.append(dict(spec=label, N=len(ev), X_pca=a1["cbar"], t_pca=a1["nw_t"],
                         X_abn=a2["mean"], t_abn=a2["t"]))

    one(f"BASE: >=$10B, macro+/-1, window(-1,+1), band 2y")
    for j in (5e9, 7.5e9, 15e9, 20e9):
        one(f"jumbo >= ${j/1e9:g}B", jumbo=j)
    for x in (0, 2, 3):
        one(f"macro +/-{x} bdays", excl=x)
    for w in [(-1, 0), (0, 1), (-2, 2), (-1, 2), (-5, 5)]:
        one(f"window {w}", window=w)
    for b in (1.0, 3.0, 4.0):
        one(f"exclusion band {b:g}y", band=b)
    return pd.DataFrame(rows)


def hmm_grid():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'archive'))
    import regime, regression as R   # retired module, see archive/README.md
    out = []
    for Kk in (2, 3, 4):
        m, ll, desc, post, f, extras = regime.build(K=Kk)
        post.to_csv(PROC / f"_post_K{Kk}.csv")
        bic = -2 * ll + np.log(len(f)) * (Kk * Kk + Kk * 3 + Kk * 6)
        out.append(dict(K=Kk, logL=ll, BIC=bic,
                        min_dwell=float((1 / (1 - np.diag(m.transmat_))).min()),
                        max_share=float(post[[c for c in post.columns if "smooth" in c]].mean().max())))
    return pd.DataFrame(out)


def curve_grid():
    """Does the concession survive on the FRED par grid instead of GSW zeros?"""
    import eventlist as E
    g, tr = E.build()
    ev, _ = E.filter_events(g, verbose=False)
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    cols = {"DGS1": 1, "DGS2": 2, "DGS3": 3, "DGS5": 5, "DGS7": 7,
            "DGS10": 10, "DGS20": 20, "DGS30": 30}
    z = fred[list(cols)].dropna()
    z.columns = [float(v) for v in cols.values()]
    z = z.loc["2024-01-01":]
    _, V, evr, _ = C.pca_factors(z)
    ten = np.array(sorted(cols.values()), dtype=float)
    rows = []
    for band in (0.5, 1.0, 2.0):
        res, nctl = [], []
        for _, e in ev.iterrows():
            dy, d0, d1 = K.event_window_change(z, e.announce)
            if dy is None: continue
            tw = {float(k): v for k, v in K.tenor_weights(tr, e.issuer, e.announce).items()}
            _, ctl, _ = K.split_tenors(list(tw), band=band, tenors=ten)
            nctl.append(len(ctl))
            o = K.concession_for(dy, list(tw), V[:, :3], tenors=ten, band=band)
            if o is None: continue
            ti = {float(t): i for i, t in enumerate(o["tenors"])}
            tg = [float(t) for t in o["targets"] if float(t) in ti]
            if not tg: continue
            res.append(dict(dollar_dur=e.dollar_dur,
                            concession_bp=sum(tw[t] * o["resid"][ti[t]] for t in tg) /
                                          sum(tw[t] for t in tg)))
        r = pd.DataFrame(res)
        row = dict(curve="FRED par (8 tenors)", band=band, N=len(r),
                   mean_ctl_tenors=float(np.mean(nctl)) if nctl else 0.0,
                   var3=evr[:3].sum())
        if len(r) >= 3:
            a = K.aggregate(r)
            row.update(X=a["cbar"], t=a["nw_t"])
        else:
            row.update(X=np.nan, t=np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    print("=== event-study specification grid ===")
    g = spec_grid()
    print(g.round(3).to_string(index=False))
    g.to_csv(TAB / "robustness_specs.csv", index=False)

    print("\n=== HMM state count ===")
    h = hmm_grid()
    print(h.round(2).to_string(index=False))
    h.to_csv(TAB / "robustness_hmm.csv", index=False)

    print("\n=== alternative curve ===")
    c = curve_grid()
    print(c.round(3).to_string(index=False))
    c.to_csv(TAB / "robustness_curve.csv", index=False)
