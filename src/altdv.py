"""C1: does the effect depend on the ACM model? Registered in commit 96cd725.

Same local projection, other dependent variables: the Kim-Wright term premium
(another affine model) and observed CMT yields and slopes (model-free).
"""
import json
import numpy as np, pandas as pd
from config import PROC, TAB, RANDOM_SEED, SAMPLE_END
import localproj as L, placebo_matched as PM, speccurve as SC

CTRL = ["dbe", "doil", "dvix", "auc_10y"]
TENORS = ["DGS2", "DGS5", "DGS7", "DGS10", "DGS20", "DGS30"]


def panel():
    P = L.panel()
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    extra = pd.read_csv(PROC / "fred_extra.csv", parse_dates=["date"]).set_index("date").loc[:SAMPLE_END]
    for c in TENORS:
        P[c] = fred[c].reindex(P.index).ffill() * 100
    P["Kim-Wright TP10"] = extra.THREEFYTP10.reindex(P.index).ffill() * 100
    P["ACM TP10"] = P.TP10
    P["10s2s"] = P.DGS10 - P.DGS2
    P["30s10s"] = P.DGS30 - P.DGS10
    return P


def main():
    P = panel()
    d, lt = SC.deal_table(P)
    pos = SC.draw_assignments(P, d, lt, PM.N_DRAW, RANDOM_SEED)
    s = d.tenyr_equiv.values / 1e9
    n = len(P)
    obs = np.zeros(n); np.add.at(obs, [P.index.get_loc(t) for t in d.announce], s)
    plac = np.zeros((n, PM.N_DRAW))
    for k in range(PM.N_DRAW):
        np.add.at(plac[:, k], pos[k], s)
    S = np.column_stack([obs, plac])
    C_all = np.column_stack([np.ones(n)] + [P[c].values for c in CTRL])
    sh = L.shocks(); sh = sh[sh.index.isin(P.index)]
    deps = ["ACM TP10", "Kim-Wright TP10"] + TENORS + ["10s2s", "30s10s"]
    rows = []
    for dep in deps:
        nw = L.project(P, sh, dep=dep, hmax=5)
        bh = {}
        for h in (0, 1, 2):
            y = (P[dep].shift(-h) - P[dep].shift(1)).values
            ok = ~np.isnan(y) & ~np.isnan(C_all).any(1)
            bh[h] = SC.fwl_b(y[ok], C_all[ok], S[ok])
        pooled = np.mean([bh[0], bh[1], bh[2]], axis=0)
        r = dict(dep=dep)
        for h in range(6):
            q = nw[nw.h == h].iloc[0]
            r[f"b_h{h}"] = float(q.b); r[f"nw_t_h{h}"] = float(q.t)
        for lab, b in (("h0", bh[0]), ("pooled0to2", pooled)):
            r[f"placebo_p_{lab}"] = float(np.mean(np.abs(b[1:]) >= abs(b[0])))
            r[f"placebo_sd_{lab}"] = float(b[1:].std())
        r["pooled0to2"] = float(pooled[0])
        rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "altdv.csv", index=False)
    pd.set_option("display.width", 220)
    print(t[["dep", "b_h0", "nw_t_h0", "placebo_p_h0", "pooled0to2", "placebo_p_pooled0to2", "b_h5"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
