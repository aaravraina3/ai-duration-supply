"""C2: is the move concentrated at the tenors the deal issued? Registered in 96cd725.

Each tranche's 10y-equivalent duration is split between the two neighbouring CMT
tenors by linear weights in maturity. Panel of six tenors by day:
    dy(k,t) = day FE + tenor FE + beta * exposure(k,t) + e
Day fixed effects absorb any curve-wide move, so beta only picks up whether
tenors with more of the deal move more than other tenors that same day.
Observed CMT yields only.
"""
import json
import numpy as np, pandas as pd
from config import PROC, TAB, RANDOM_SEED
import placebo_matched as PM, speccurve as SC, altdv as A

GRID = [2, 5, 7, 10, 20, 30]
COLS = [f"DGS{g}" for g in GRID]


def weights(maturity):
    """Split one unit of duration between the neighbouring grid tenors."""
    m = float(np.clip(maturity, GRID[0], GRID[-1]))
    w = np.zeros(len(GRID))
    j = np.searchsorted(GRID, m)
    if GRID[min(j, len(GRID) - 1)] == m:
        w[j] = 1.0
    else:
        lo, hi = GRID[j - 1], GRID[j]
        w[j - 1], w[j] = (hi - m) / (hi - lo), (m - lo) / (hi - lo)
    return w


def exposure_by_deal(d):
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    out = {}
    for _, r in d.iterrows():
        rows = tr[(tr.issuer == r.issuer) & (tr.announce == r.announce)]
        out[r.announce] = sum(t.tenyr_equiv / 1e9 * weights(t.tenor) for _, t in rows.iterrows())
    return out


def twoway_demean(M):
    """M is days x tenors (x draws). Remove day and tenor means (balanced panel)."""
    return M - M.mean(axis=1, keepdims=True) - M.mean(axis=0, keepdims=True) + M.mean(axis=(0, 1), keepdims=True)


def main():
    P = A.panel()
    d, lt = SC.deal_table(P)
    pos = SC.draw_assignments(P, d, lt, PM.N_DRAW, RANDOM_SEED)
    ex = exposure_by_deal(d)
    dy = (P[COLS] - P[COLS].shift(1)).values               # days x tenors
    ok = ~np.isnan(dy).any(1)
    n = len(P)

    def exposure_matrix(day_pos):
        E = np.zeros((n, len(GRID)))
        for i, (_, r) in enumerate(d.iterrows()):
            E[day_pos[i]] += ex[r.announce]
        return E
    real_pos = [P.index.get_loc(t) for t in d.announce]
    Y = twoway_demean(dy[ok])

    def beta(E):
        X = twoway_demean(E[ok])
        return float((X * Y).sum() / (X ** 2).sum())
    b_obs = beta(exposure_matrix(real_pos))
    null = np.array([beta(exposure_matrix(pos[k])) for k in range(PM.N_DRAW)])
    share = {f"DGS{g}": float(sum(ex[a][i] for a in ex) / sum(ex[a].sum() for a in ex)) for i, g in enumerate(GRID)}
    res = dict(registered_in="96cd725", beta=b_obs, placebo_sd=float(null.std()),
               placebo_p=float(np.mean(np.abs(null) >= abs(b_obs))),
               exposure_share_by_tenor=share, n_days=int(ok.sum()), draws=PM.N_DRAW)
    (TAB / "tenorlocal.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
