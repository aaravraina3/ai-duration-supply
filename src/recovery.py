"""How much of a REAL maturity-localized concession could this estimator even see?

Published curves are smooth by construction. GSW is a 6-parameter Svensson fit to
off-the-run bonds, and three principal components span ~99.2% of its daily
variation. So a genuinely local bump at 10y is attenuated twice:
  (i) the Svensson fit smooths it before it is ever published,
  (ii) the 3-factor residualization removes more of what is left.
We inject a bump of known size and measure what comes back out.
"""
import numpy as np, pandas as pd
from config import PROC, EXCL_BAND_YEARS
import curve as C
from concession import concession_for, split_tenors, MAXT

TAU = np.arange(1, MAXT + 1, dtype=float)

def bump(targets, amp=5.0, width=1.5, tau=TAU):
    """Gaussian cheapening centred on each target tenor, amp in bp."""
    b = np.zeros_like(tau)
    for t in targets:
        b += amp * np.exp(-0.5 * ((tau - min(t, MAXT)) / width) ** 2)
    return np.minimum(b, amp * 1.6)          # overlapping tranches do not stack without limit

def refit_svensson(y, tau=TAU, l1g=None, l2g=None):
    """Mimic the GSW publication step: re-fit 6-parameter Svensson to the bumped curve."""
    l1g = np.linspace(0.3, 6.0, 30) if l1g is None else l1g
    l2g = np.linspace(2.0, 25.0, 40) if l2g is None else l2g
    best, bf = np.inf, None
    for l1 in l1g:
        for l2 in l2g:
            if l2 <= l1 + 0.25: continue
            X = C.nss_basis(tau, l1, l2)
            b, *_ = np.linalg.lstsq(X, y, rcond=None)
            r = y - X @ b; s = float(r @ r)
            if s < best: best, bf = s, X @ b
    return bf

def experiment(targets, dur_w, V, amp=5.0, width=1.5, base=None, n_days=60, seed=7):
    """Return the duration-weighted concession recovered from a known injected bump."""
    rng = np.random.default_rng(seed)
    z = C.load_gsw(start="2024-01-01")
    dz = (z.diff().dropna()) * 100.0
    picks = rng.choice(len(dz) - 2, size=n_days, replace=False)
    b = bump(targets, amp, width)
    truth = float(np.average([b[int(t) - 1] for t in targets],
                             weights=[dur_w[t] for t in targets]))
    raw, smoothed = [], []
    for p in picks:
        d0 = dz.iloc[p].values                       # a real daily curve change, bp
        for mode, store in (("raw", raw), ("smoothed", smoothed)):
            y = d0 + b
            if mode == "smoothed":
                y = refit_svensson(y)                # attenuation (i)
            o = concession_for(pd.Series(y, index=TAU), targets, V, tenors=TAU)  # attenuation (ii)
            ti = {t: i for i, t in enumerate(o["tenors"])}
            store.append(sum(dur_w[t] * o["resid"][ti[int(t)]] for t in targets) /
                         sum(dur_w.values()))
    return truth, float(np.mean(raw)), float(np.mean(smoothed))

if __name__ == "__main__":
    import concession as K
    events = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    z = C.load_gsw(start="2024-01-01"); V, _ = K.loadings(z)
    print(f"{'event':32s} {'true bump':>10} {'PCA only':>10} {'+Svensson':>11} {'recovery':>9}")
    rec_pca, rec_all = [], []
    for _, e in events.iterrows():
        tw = K.tenor_weights(tr, e.issuer, e.announce)
        tg = sorted(tw)
        truth, raw, sm = experiment(tg, tw, V)
        rec_pca.append(raw / truth); rec_all.append(sm / truth)
        print(f"{e.issuer+' '+str(e.announce.date()):32s} {truth:9.2f}bp {raw:9.2f}bp "
              f"{sm:10.2f}bp {sm/truth:8.1%}")
    print(f"\nmean recovery, 3-PC residualization only : {np.mean(rec_pca):.1%}")
    print(f"mean recovery, Svensson re-fit then 3-PC : {np.mean(rec_all):.1%}")
    print(f"=> an estimate of X must be divided by ~{np.mean(rec_all):.3f} to read as a true concession")
    np.save(PROC / "recovery.npy", np.array([np.mean(rec_pca), np.mean(rec_all)]))
