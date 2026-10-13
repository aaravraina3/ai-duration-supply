"""D2: does supply information improve out-of-sample forecasts of term premium
changes? Registered in commit 96cd725. Model ladder rungs 0 to 2 (UPGRADE_PLAN
5.0); climbing further needs a written diagnosis first.
"""
import json
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from config import TAB
import localproj as L, regression as R

WARM = 250
MACRO = ["dTP", "dbe", "doil", "dvix", "auc_10y"]
SUPPLY = ["shock", "dD"]


def data():
    P = L.panel()
    df = pd.DataFrame(index=P.index)
    df["dTP"] = P.TP10.diff()
    for c in ("dbe", "doil", "dvix", "auc_10y"):
        df[c] = P[c]
    df["shock"] = L.shocks().reindex(P.index).fillna(0.0)
    df["dD"] = R.ai_supply().dD.reindex(P.index).fillna(0.0)
    df["TP"] = P.TP10
    return df


def run(df, h):
    y = (df.TP.shift(-h) - df.TP).values
    idx = np.arange(len(df))
    pred = {k: np.full(len(df), np.nan) for k in ("mean", "zero", "macro", "macro+supply")}
    for t in range(WARM, len(df) - h):
        tr = idx[1:t - h + 1]                          # labels end at t - h + h = t: purge the last h
        tr = tr[~np.isnan(y[tr])]
        pred["mean"][t] = y[tr].mean(); pred["zero"][t] = 0.0
        for k, cols in (("macro", MACRO), ("macro+supply", MACRO + SUPPLY)):
            X = sm.add_constant(df[cols].values[tr], has_constant="add")
            b = np.linalg.lstsq(X, y[tr], rcond=None)[0]
            pred[k][t] = np.r_[1.0, df[cols].values[t]] @ b
    ok = ~np.isnan(pred["mean"]) & ~np.isnan(y)
    return y[ok], {k: v[ok] for k, v in pred.items()}


def clark_west(y, small, big):
    f = (y - small) ** 2 - ((y - big) ** 2 - (small - big) ** 2)
    m = sm.OLS(f, np.ones(len(f))).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    return float(m.params[0] / m.bse[0]), float(stats.norm.sf(m.params[0] / m.bse[0]))


def diebold_mariano(y, a, b, h):
    d = (y - a) ** 2 - (y - b) ** 2
    m = sm.OLS(d, np.ones(len(d))).fit(cov_type="HAC", cov_kwds={"maxlags": max(h, 1)})
    return float(m.params[0] / m.bse[0]), float(2 * stats.norm.sf(abs(m.params[0] / m.bse[0])))


def main():
    df = data()
    out = dict(registered_in="96cd725", warm_up=WARM)
    for h in (1, 3):
        y, p = run(df, h)
        mse = {k: float(np.mean((y - v) ** 2)) for k, v in p.items()}
        r2 = {k: float(1 - mse[k] / mse["mean"]) for k in mse}
        cw_t, cw_p = clark_west(y, p["macro"], p["macro+supply"])
        dm_t, dm_p = diebold_mariano(y, p["zero"], p["macro"], h)
        # residual check for climbing to rung 4: do rung-2 errors depend on the volatility regime?
        e = y - p["macro+supply"]
        vol = df.dTP.shift(1).rolling(20).std().values[WARM:WARM + len(y)]
        okv = ~np.isnan(vol)
        res = sm.OLS(e[okv] ** 2, sm.add_constant(vol[okv])).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        out[f"h{h}"] = dict(n=int(len(y)), mse=mse, oos_r2_vs_mean=r2, clark_west_t=cw_t, clark_west_p=cw_p,
                            dm_zero_vs_macro_t=dm_t, dm_p=dm_p,
                            rung4_check_vol_on_sq_error_t=float(res.tvalues[1]),
                            rung4_check_vol_on_error_t=float(sm.OLS(e[okv], sm.add_constant(vol[okv])).fit(
                                cov_type="HAC", cov_kwds={"maxlags": 5}).tvalues[1]))
    (TAB / "oos_forecast.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
