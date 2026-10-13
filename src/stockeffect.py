"""C3: the stock half of flow versus stock (D'Amico and King 2013). Registered in
commit 96cd725.

Monthly: cumulative outstanding AI 10y-equivalent duration (no decay) against
the ACM TP10 level. Levels only if cointegrated; otherwise monthly changes on
monthly new issuance, with permutation inference across months.
"""
import json
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from config import PROC, TAB, RANDOM_SEED, SAMPLE_START, SAMPLE_END
import regression as R

N_PERM = 10_000


def monthly():
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date").loc[SAMPLE_START:SAMPLE_END]
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date").loc[SAMPLE_START:SAMPLE_END]
    deals = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    auc = R.treasury_supply()["auc_10y"].loc[SAMPLE_START:SAMPLE_END]
    m = pd.DataFrame({"TP10": acm.ACMTP10.resample("ME").last() * 100})
    m["issuance"] = (deals.set_index("announce").tenyr_equiv / 1e9).resample("ME").sum().reindex(m.index).fillna(0.0)
    m["stock"] = m.issuance.cumsum()
    m["be"] = fred.T10YIE.resample("ME").last() * 100
    m["vix"] = fred.VIXCLS.resample("ME").last()
    m["oil"] = np.log(fred.DCOILWTICO.resample("ME").last()) * 100
    m["auc_10y"] = auc.resample("ME").sum().reindex(m.index).fillna(0.0)
    m["dTP"] = m.TP10.diff(); m["dbe"] = m.be.diff(); m["dvix"] = m.vix.diff(); m["doil"] = m.oil.diff()
    return m


def stationarity(s):
    s = s.dropna()
    return dict(adf_p=float(adfuller(s, autolag="AIC")[1]), kpss_p=float(kpss(s, regression="c", nlags="auto")[1]))


def main():
    m = monthly()
    out = dict(registered_in="96cd725", months=int(len(m)), first=str(m.index[0].date()), last=str(m.index[-1].date()),
               stationarity={"TP10 level": stationarity(m.TP10), "stock": stationarity(m.stock)})
    lv = m[["TP10", "stock"]].dropna()
    eg = coint(lv.TP10, lv.stock)
    jo = coint_johansen(lv.values, det_order=0, k_ar_diff=1)
    out["engle_granger_p"] = float(eg[1])
    out["johansen_trace_r0"] = dict(stat=float(jo.lr1[0]), cv95=float(jo.cvt[0, 1]),
                                    reject=bool(jo.lr1[0] > jo.cvt[0, 1]))
    cointegrated = out["engle_granger_p"] < 0.05 or out["johansen_trace_r0"]["reject"]
    out["cointegrated"] = bool(cointegrated)

    d = m.dropna(subset=["dTP", "dbe", "dvix", "doil"])
    ctrl = ["dbe", "doil", "dvix", "auc_10y"]
    X = sm.add_constant(d[["issuance"] + ctrl])
    fit = sm.OLS(d.dTP, X).fit()
    nw = sm.OLS(d.dTP, X).fit(cov_type="HAC", cov_kwds={"maxlags": 2, "use_correction": True})
    rng = np.random.default_rng(RANDOM_SEED)
    null = np.empty(N_PERM)
    for k in range(N_PERM):
        Xp = X.copy(); Xp["issuance"] = rng.permutation(d.issuance.values)
        null[k] = sm.OLS(d.dTP, Xp).fit().params["issuance"]
    b = float(fit.params["issuance"])
    sd = float(null.std())
    out["changes_on_issuance"] = dict(
        n=int(len(d)), b=b, permutation_p=float(np.mean(np.abs(null) >= abs(b))), permutation_sd=sd,
        newey_west_t=float(nw.tvalues["issuance"]), newey_west_p=float(nw.pvalues["issuance"]),
        mde80_two_sided=float((1.96 + 0.8416) * sd),
        implied_2026_bp=float(b * m.loc["2026"].issuance.sum()))
    if cointegrated:
        lvfit = sm.OLS(lv.TP10, sm.add_constant(lv.stock)).fit(cov_type="HAC", cov_kwds={"maxlags": 2, "use_correction": True})
        # not in the registration: a Newey-West t so the levels estimate is not reported bare (DECISIONS D-17)
        out["levels"] = dict(b=float(lvfit.params["stock"]), newey_west_t=float(lvfit.tvalues["stock"]),
                             r2=float(lvfit.rsquared))
    (TAB / "stockeffect.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
