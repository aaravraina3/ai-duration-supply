"""§4.7 HMM regime detection on the curve factors.

Gaussian emissions on the three PCA factors, fit by Baum-Welch with random
restarts. States are relabelled after fitting by a fixed criterion (mean level
loading) so indices are comparable across runs. Smoothed posteriors are used for
description only; anything that feeds a predictive regression uses FILTERED
posteriors, which condition on the past alone.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np, pandas as pd
from hmmlearn.hmm import GaussianHMM
from config import PROC, HMM_K, HMM_RESTARTS, RANDOM_SEED
import curve as C


def fit_hmm(F, K=HMM_K, restarts=HMM_RESTARTS, seed=RANDOM_SEED):
    """EM hits local optima, so keep the best of `restarts` random starts."""
    best, best_ll = None, -np.inf
    for i in range(restarts):
        m = GaussianHMM(n_components=K, covariance_type="full", n_iter=500,
                        tol=1e-6, random_state=seed + i, init_params="stmc")
        try:
            m.fit(F)
            ll = m.score(F)
        except Exception:
            continue
        if np.isfinite(ll) and ll > best_ll:
            best, best_ll = m, ll
    return best, best_ll


def relabel(m):
    """Label switching: sort states by mean loading on factor 1 (the level factor)."""
    order = np.argsort(m.means_[:, 0])
    m.startprob_ = m.startprob_[order]
    m.transmat_ = m.transmat_[np.ix_(order, order)]
    m.means_ = m.means_[order]
    m.covars_ = m.covars_[order]
    return m


def filtered_posteriors(m, F):
    """P(z_t = k | f_1..f_t). hmmlearn's predict_proba is SMOOTHED and uses the
    whole sample, which would leak the future into any predictive regression."""
    logB = m._compute_log_likelihood(F)
    B = np.exp(logB - logB.max(axis=1, keepdims=True))
    T, K = B.shape
    A, pi = m.transmat_, m.startprob_
    a = np.zeros((T, K))
    v = pi * B[0]
    a[0] = v / v.sum()
    for t in range(1, T):
        v = (a[t - 1] @ A) * B[t]
        s = v.sum()
        a[t] = v / s if s > 0 else 1.0 / K
    return a


def describe(m, F, z_smooth, extras=None):
    K = m.n_components
    rows = []
    dwell = 1.0 / (1.0 - np.diag(m.transmat_))
    for k in range(K):
        w = z_smooth[:, k]
        r = dict(state=k, share=w.mean(), dwell_days=dwell[k],
                 mu_f1=m.means_[k, 0], mu_f2=m.means_[k, 1], mu_f3=m.means_[k, 2],
                 sd_f1=np.sqrt(m.covars_[k][0, 0]))
        if extras is not None:
            for c in extras.columns:
                x = extras[c].values
                r[f"mean_{c}"] = float(np.average(x, weights=w))
            # does the long end move WITH breakevens in this state?
            if {"dbe", "dy10"} <= set(extras.columns):
                x, y = extras["dbe"].values, extras["dy10"].values
                xm = np.average(x, weights=w); ym = np.average(y, weights=w)
                cov = np.average((x - xm) * (y - ym), weights=w)
                r["corr_be_y10"] = cov / (np.sqrt(np.average((x - xm) ** 2, weights=w)) *
                                          np.sqrt(np.average((y - ym) ** 2, weights=w)))
        rows.append(r)
    return pd.DataFrame(rows)


def build(K=HMM_K):
    z = C.load_gsw(start="2024-01-01")
    f, V, ev, dz = C.pca_factors(z)
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    extras = pd.DataFrame({
        "dy10": z[10.0].diff() * 100,
        "dy30": z[30.0].diff() * 100,
        "slope_30_10": (z[30.0] - z[10.0]).diff() * 100,
        "dbe": fred["T10YIE"].reindex(z.index).ffill().diff() * 100,
    }).reindex(f.index).dropna()
    f = f.reindex(extras.index)
    F = f.values
    m, ll = fit_hmm(F, K=K)
    m = relabel(m)
    sm = m.predict_proba(F)
    fl = filtered_posteriors(m, F)
    desc = describe(m, F, sm, extras)
    post = pd.DataFrame(fl, index=f.index, columns=[f"p{k}_filt" for k in range(K)])
    for k in range(K):
        post[f"p{k}_smooth"] = sm[:, k]
    return m, ll, desc, post, f, extras


if __name__ == "__main__":
    pd.set_option("display.width", 250, "display.max_columns", 30)
    for K in (2, 3):
        m, ll, desc, post, f, extras = build(K)
        print(f"\n=== K={K}  logL={ll:.1f}  BIC={-2*ll + np.log(len(f))*(K*K + K*3 + K*6):.1f} ===")
        print(desc.round(3).to_string(index=False))
        print("transition matrix:\n", np.round(m.transmat_, 3))
        if K == HMM_K:
            post.to_csv(PROC / "regime_posteriors.csv")
            desc.to_csv(PROC / "regime_describe.csv", index=False)
            corr = np.corrcoef(post[[f"p{k}_filt" for k in range(K)]].values.T,
                               post[[f"p{k}_smooth" for k in range(K)]].values.T)
            print("\nfiltered vs smoothed posterior correlation, per state:",
                  np.round([corr[k, K + k] for k in range(K)], 3))
