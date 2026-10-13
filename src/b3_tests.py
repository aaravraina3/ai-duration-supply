"""T1 to T4 in research/11_UPGRADE_PREREG.md (registered in f304594).

T1 deal-day residuals quieter than chance?
T2 calmer markets in the days before deals?
T3 does the deal-day variance gap explain OLS vs Newey-West?
T4 are deals priced just after macro releases more often than chance?

Writes output/tables/b3_tests.json.
"""
import json
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from config import PROC, TAB, RANDOM_SEED, JUMBO_USD
import localproj as L, placebo_matched as PM, diagnostics as D

N_DRAW = 10_000
CTRL = ["dbe", "doil", "dvix", "auc_10y"]


def setup():
    P = L.panel()
    sh = L.shocks(); sh = sh[sh.index.isin(P.index)]
    lt = PM.lag_table(P.index)
    return P, sh, lt


def placebo_stat(stat, sh, lt, rng, kind):
    draw = (lambda: PM.draw_matched(sh, lt, rng)) if kind == "matched" else (lambda: PM.draw_uniform(sh, lt, rng))
    return np.array([stat(draw().index) for _ in range(N_DRAW)])


def t1(P, sh, lt):
    y, X, k = D.target_lp(0)
    e0 = sm.OLS(y, X.drop(columns=k)).fit().resid          # controls only (primary)
    e1 = sm.OLS(y, X).fit().resid                          # with the shock (secondary)
    out = {}
    for name, e in [("controls_only", e0), ("full_model", e1)]:
        on = e.index.isin(sh.index)
        sd_obs = float(e[on].std(ddof=1))
        bf = stats.levene(e[on], e[~on], center="median")
        res = dict(sd_deal=sd_obs, sd_other=float(e[~on].std(ddof=1)),
                   brown_forsythe_W=float(bf.statistic), brown_forsythe_p=float(bf.pvalue))
        for kind in ("matched", "uniform"):
            rng = np.random.default_rng(RANDOM_SEED)
            null = placebo_stat(lambda d: float(e.reindex(d).dropna().std(ddof=1)), sh, lt, rng, kind)
            res[f"{kind}_placebo_median_sd"] = float(np.median(null))
            res[f"{kind}_p_one_sided"] = float(np.mean(null <= sd_obs))
        out[name] = res
    return out


def t2(P, sh, lt):
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    dtp = P.TP10.diff()
    vol = dtp.shift(1).rolling(20).std()                    # t-20 .. t-1 only
    vix = fred.VIXCLS.reindex(P.index).ffill().shift(1)      # close on t-1
    out = {}
    for name, s in [("trailing_20d_tp_vol", vol), ("vix_prior_close", vix)]:
        obs = float(s.reindex(sh.index).median())
        res = dict(deal_median=obs, all_days_median=float(s.median()),
                   deal_percentiles={str(d.date()): float((s.dropna() <= s[d]).mean()) for d in sh.index})
        for kind in ("matched", "uniform"):
            rng = np.random.default_rng(RANDOM_SEED)
            null = placebo_stat(lambda d: float(s.reindex(d).median()), sh, lt, rng, kind)
            res[f"{kind}_placebo_median"] = float(np.median(null))
            res[f"{kind}_p_one_sided"] = float(np.mean(null <= obs))
        out[name] = res
    return out


def t3():
    y, X, k = D.target_lp(0)
    xt, e, u = D.score(y, X, k)
    T, kx = len(e), X.shape[1]
    sxx = np.sum(xt ** 2)
    on = X[k].values != 0

    def ses(e):
        s2 = np.sum(e ** 2) / (T - kx)
        uu = xt * e
        lrv = D.autocov(uu, 0) + 2 * sum((1 - j / 6) * D.autocov(uu, j) for j in range(1, 6))
        return dict(ols=float(np.sqrt(s2 / sxx)),
                    hc0=float(np.sqrt(np.sum(uu ** 2)) / sxx),
                    nw5=float(np.sqrt(T * lrv) / sxx))
    act = ses(e)
    ec = e.copy()
    ec[on] = ec[on] * (e[~on].std(ddof=1) / e[on].std(ddof=1))
    cf = ses(ec)
    closed = (np.log(cf["nw5"] ** 2) - np.log(act["nw5"] ** 2)) / (np.log(act["ols"] ** 2) - np.log(act["nw5"] ** 2))
    return dict(actual=act, counterfactual=cf,
                cf_nw_over_ols=float(cf["nw5"] / act["ols"]),
                share_of_log_variance_gap_closed=float(closed),
                holds_within_10pct=bool(abs(cf["nw5"] / act["ols"] - 1) <= 0.10))


def t4(P, sh, lt):
    lag = lt.lag
    rel = pd.read_csv(PROC / "macro_calendar.csv", parse_dates=["date"]).date
    deals = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    out = {"primary_all_16": {}, "secondary_11_dropped_by_3day_rule": {}}
    rng = np.random.default_rng(RANDOM_SEED)
    lagv = lag.values
    for kk in (1, 2, 3):
        hit = (lag >= 1) & (lag <= kk)
        base = float(hit.mean())
        n_obs = int(hit.reindex(sh.index).sum())
        perm = np.array([hit.values[rng.choice(len(lagv), 16, replace=False)].sum() for _ in range(100_000)])
        out["primary_all_16"][f"within_{kk}"] = dict(
            count=n_obs, n=16, share=n_obs / 16, base_rate=base,
            binom_p=float(stats.binomtest(n_obs, 16, base, alternative="greater").pvalue),
            perm_p=float(np.mean(perm >= n_obs)))
    # the 11 jumbos within +/-3 business days of a release
    near = lambda d: any(abs(np.busday_count(np.datetime64(r.date()), np.datetime64(d.date()))) <= 3 for r in rel)
    jumbo = deals[deals.total_usd >= JUMBO_USD].announce
    dropped = [d for d in jumbo if near(d)]
    in_win = pd.Series([near(d) for d in lag.index], index=lag.index)
    hit3 = (lag >= 1) & (lag <= 3)
    n_obs = int(hit3.reindex(dropped).sum())
    for name, base in [("unconditional", float(hit3.mean())),
                       ("conditional_on_within_3_of_release", float(hit3[in_win].mean()))]:
        out["secondary_11_dropped_by_3day_rule"][name] = dict(
            count=n_obs, n=len(dropped), base_rate=base,
            binom_p=float(stats.binomtest(n_obs, len(dropped), base, alternative="greater").pvalue))
    return out


def main():
    P, sh, lt = setup()
    res = dict(registered_in="f304594", draws=N_DRAW, T1=t1(P, sh, lt), T2=t2(P, sh, lt), T3=t3(), T4=t4(P, sh, lt))
    (TAB / "b3_tests.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "T2"}, indent=1))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "deal_percentiles"} for k, v in res["T2"].items()}, indent=1))


if __name__ == "__main__":
    main()
