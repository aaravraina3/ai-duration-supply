"""C5: does the chance of a deal on a given day depend on market conditions
known before it? Greenwood, Hanson and Stein (2010) show firms time long-dated
issuance around Treasury supply, a direct reverse-causality worry. Registered
in commit 96cd725.
"""
import json
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, TAB, RANDOM_SEED, SAMPLE_END
import localproj as L, altdv as A

N_PERM = 10_000
N_POWER = 1000
N_PERM_POWER = 200
REG = ["auction_day", "d10y_5d", "slope_10s2s", "baa_spread"]


def design():
    P = A.panel()
    extra = pd.read_csv(PROC / "fred_extra.csv", parse_dates=["date"]).set_index("date").loc[:SAMPLE_END]
    X = pd.DataFrame(index=P.index)
    X["auction_day"] = (P.auc_10y > 0).astype(float)
    X["d10y_5d"] = (P.DGS10.shift(1) - P.DGS10.shift(6))
    X["slope_10s2s"] = P["10s2s"].shift(1)
    X["baa_spread"] = extra.BAA10Y.reindex(P.index).ffill().shift(1) * 100
    sh = L.shocks()
    y = pd.Series(P.index.isin(sh.index).astype(float), index=P.index)
    ok = X.notna().all(axis=1)
    Xs = (X[ok] - X[ok].mean()) / X[ok].std()
    return y[ok], sm.add_constant(Xs)


def lr(y, X):
    m = sm.Logit(y, X).fit(disp=0)
    m0 = sm.Logit(y, X[["const"]]).fit(disp=0)
    return 2 * (m.llf - m0.llf), m


def perm_p(y, X, rng, n):
    obs, _ = lr(y, X)
    null = np.empty(n)
    for k in range(n):
        null[k] = lr(pd.Series(rng.permutation(y.values), index=y.index), X)[0]
    return float(np.mean(null >= obs)), obs


def main():
    y, X = design()
    rng = np.random.default_rng(RANDOM_SEED)
    p, stat = perm_p(y, X, rng, N_PERM)
    _, m = lr(y, X)
    out = dict(registered_in="96cd725", days=int(len(y)), deals=int(y.sum()), lr_stat=float(stat), permutation_p=p,
               coefficients={k: dict(b=float(m.params[k]), wald_p=float(m.pvalues[k])) for k in REG})
    # power: one regressor (the slope) with odds ratio 2 per sd, 16 events on average
    base = np.log(16 / len(y))
    hits = 0
    for _ in range(N_POWER):
        eta = base + np.log(2.0) * X.slope_10s2s.values
        prob = 1 / (1 + np.exp(-eta)); prob *= 16 / prob.sum()
        ysim = pd.Series((rng.random(len(y)) < prob).astype(float), index=y.index)
        if ysim.sum() < 3:
            continue
        hits += perm_p(ysim, X, rng, N_PERM_POWER)[0] < 0.05
    out["power_or2_per_sd"] = float(hits / N_POWER)
    (TAB / "timing.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
