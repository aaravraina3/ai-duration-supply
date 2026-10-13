"""Phase B, B4 to B8 (research/12_DIAGNOSTICS.md). Inference for every corrected
estimate is the volatility-matched placebo V1 (registered in f304594), with the
lag-only placebo alongside.

B4 heteroskedasticity: Breusch-Pagan, White, ARCH LM; volatility-scaled and
   weighted least squares versions of the h = 0 estimate
B5 stationarity: ADF and KPSS on every series; specs that put a nonstationary
   regressor on a stationary dependent variable are flagged
B6 fat tails and influence: Jarque-Bera, Cook's distance, Huber and median
   regression versions of the h = 0 estimate
B7 multicollinearity: VIFs
B8 stability: Chow test at 2025-01-01, expanding-window h = 0 coefficient
"""
import json, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, het_white, het_arch
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import jarque_bera
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.regression.quantile_regression import QuantReg
from config import TAB, FIG, RANDOM_SEED, VOL_WINDOW
import localproj as L, placebo_matched as PM, regression as R

warnings.filterwarnings("ignore")
CTRL = ["dbe", "doil", "dvix", "auc_10y"]
N_DRAW = 2000


def design(P, sh):
    """h = 0 design with the trailing-volatility scale (t-20 .. t-1 only)."""
    y = P.TP10 - P.TP10.shift(1)
    sig = P.TP10.diff().shift(1).rolling(VOL_WINDOW).std()
    X = sm.add_constant(pd.DataFrame({"shock": sh.reindex(P.index).fillna(0.0), **{c: P[c] for c in CTRL}}))
    ok = y.notna() & X.notna().all(axis=1) & sig.notna()
    return y[ok], X[ok], sig[ok]


ESTIMATORS = {
    "OLS": lambda y, X, s: sm.OLS(y, X).fit().params["shock"],
    "OLS on vol-scaled dTP": lambda y, X, s: sm.OLS(y / s, X).fit().params["shock"],
    "WLS, weights 1/vol^2": lambda y, X, s: sm.WLS(y, X, weights=1 / s ** 2).fit().params["shock"],
    "Huber": lambda y, X, s: sm.RLM(y, X, M=sm.robust.norms.HuberT()).fit().params["shock"],
    "median regression": lambda y, X, s: QuantReg(y, X).fit(q=0.5).params["shock"],
}


def corrected_estimates():
    P = L.panel(); sh = L.shocks(); sh = sh[sh.index.isin(P.index)]
    y, X, s = design(P, sh)
    lt = PM.add_vol_tercile(PM.lag_table(P.index), P)
    obs = {k: float(f(y, X, s)) for k, f in ESTIMATORS.items()}
    null = {k: {"vol-matched": [], "lag-only": []} for k in ESTIMATORS}
    stats = {}
    for kind, seed_off in (("vol-matched", 0), ("lag-only", 1)):
        rng = np.random.default_rng(RANDOM_SEED + seed_off)
        for _ in range(N_DRAW):
            f = PM.draw_vol_matched(sh, lt, rng, stats=stats) if kind == "vol-matched" else PM.draw_matched(sh, lt, rng)
            Xp = X.copy(); Xp["shock"] = f.reindex(X.index).fillna(0.0)
            for k, est in ESTIMATORS.items():
                null[k][kind].append(est(y, Xp, s))
    rows = []
    for k in ESTIMATORS:
        r = dict(estimator=k, b=obs[k])
        for kind in ("vol-matched", "lag-only"):
            b = np.array(null[k][kind])
            r[f"{kind} placebo sd"] = float(b.std())
            r[f"{kind} p"] = float(np.mean(np.abs(b) >= abs(obs[k])))
        rows.append(r)
    fallback = stats.get("fallback", 0) / max(stats.get("slots", 1), 1)
    return pd.DataFrame(rows), fallback


def b4_tests(y, X, name):
    m = sm.OLS(y, X).fit()
    bp = het_breuschpagan(m.resid, X); wh = het_white(m.resid, X); ar = het_arch(m.resid, nlags=5)
    return dict(target=name, breusch_pagan_p=float(bp[1]), white_p=float(wh[1]), arch_lm5_p=float(ar[1]))


def b5_stationarity():
    df = R.dataset()
    P = L.panel()
    acm = pd.read_csv(L.PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    series = {
        "TP10 level": acm.ACMTP10.loc[df.index] * 100, "dTP10": df.dTP10,
        "D (decayed stock)": df.D, "dD": df.dD, "S (retired text index)": df.S, "dS": df.dS,
        "deal shock": L.shocks().reindex(P.index).fillna(0.0),
        "dbe": df.dbe, "doil": df.doil, "dvix": df.dvix, "auc_10y": df.auc_10y, "auc_surprise": df.auc_surprise,
    }
    rows = []
    for k, s in series.items():
        s = s.dropna()
        a = adfuller(s, autolag="AIC")
        kp = kpss(s, regression="c", nlags="auto")
        stat = "stationary" if (a[1] < 0.05 and kp[1] > 0.05) else (
            "nonstationary" if (a[1] >= 0.05 and kp[1] <= 0.05) else "ambiguous")
        rows.append(dict(series=k, n=len(s), adf_p=float(a[1]), kpss_p=float(kp[1]), verdict=stat))
    t = pd.DataFrame(rows)
    verdict = dict(zip(t.series, t.verdict))
    specs = []
    for dep in ("dTP10", "dRN10"):
        for sup, ser in (("S", "S (retired text index)"), ("D", "D (decayed stock)"), ("dS", "dS"), ("dD", "dD")):
            for reg in ([True, False] if sup in ("S", "D") else [False]):
                v = verdict[ser]
                specs.append(dict(spec=f"{dep} ~ {sup}{' x regime' if reg else ''}", regressor=ser,
                                  regressor_verdict=v,
                                  breaks_rule=v != "stationary"))
    return t, pd.DataFrame(specs)


def b6(y, X, name):
    m = sm.OLS(y, X).fit()
    jb = jarque_bera(m.resid)
    cook = m.get_influence().cooks_distance[0]
    on = X.index.isin(L.shocks().index)            # the 16 announcement days, for both targets
    order = np.argsort(cook)[::-1][:10]
    top = [dict(date=str(X.index[i].date()), cooks_d=float(cook[i]), deal_day=bool(on[i])) for i in order]
    return dict(target=name, jarque_bera=float(jb[0]), jarque_bera_p=float(jb[1]), skew=float(jb[2]),
                kurtosis=float(jb[3]), cooks_threshold_4_over_n=4 / len(y), top10=top), m, cook, on


def b7(X, name):
    Xv = X.values
    return [dict(target=name, variable=c, vif=float(variance_inflation_factor(Xv, i)))
            for i, c in enumerate(X.columns) if c != "const"]


def b8():
    P = L.panel(); sh = L.shocks(); sh = sh[sh.index.isin(P.index)]
    y = P.TP10 - P.TP10.shift(1)
    X = sm.add_constant(pd.DataFrame({"shock": sh.reindex(P.index).fillna(0.0), **{c: P[c] for c in CTRL}}))
    ok = y.notna() & X.notna().all(axis=1); y, X = y[ok], X[ok]
    pre = X.index < "2025-01-01"
    full = sm.OLS(y, X).fit(); a = sm.OLS(y[pre], X[pre]).fit(); b = sm.OLS(y[~pre], X[~pre]).fit()
    k = X.shape[1]; n = len(y)
    F = ((full.ssr - a.ssr - b.ssr) / k) / ((a.ssr + b.ssr) / (n - 2 * k))
    from scipy import stats
    chow = dict(break_date="2025-01-01", F=float(F), p=float(stats.f.sf(F, k, n - 2 * k)),
                deals_before=int((sh.index < "2025-01-01").sum()), deals_after=int((sh.index >= "2025-01-01").sum()),
                b_before=float(a.params["shock"]), b_after=float(b.params["shock"]))
    path = []
    for i, d in enumerate(sorted(sh.index)):
        if i < 3:
            continue
        cut = X.index <= d
        m = sm.OLS(y[cut], X[cut]).fit()
        path.append(dict(through=str(d.date()), n_deals=i + 1, b=float(m.params["shock"]), se=float(m.bse["shock"])))
    return chow, pd.DataFrame(path)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from diagnostics import target_daily, target_lp
    out = {}
    yd, Xd, _ = target_daily(); yl, Xl, _ = target_lp(0)
    Xd2 = Xd.rename(columns={"dD": "shock"})

    out["B4_tests"] = [b4_tests(yd, Xd, "daily dD"), b4_tests(yl, Xl, "lp h=0")]
    est, fallback = corrected_estimates()
    est.to_csv(TAB / "diagnostics_b4b6_estimates.csv", index=False)
    out["V1_fallback_rate"] = fallback

    st, sp = b5_stationarity()
    st.to_csv(TAB / "diagnostics_b5_stationarity.csv", index=False)
    sp.to_csv(TAB / "diagnostics_b5_specs.csv", index=False)

    b6d, _, _, _ = b6(yd, Xd2, "daily dD")
    b6l, m, cook, on = b6(yl, Xl, "lp h=0")
    out["B6"] = [b6d, b6l]
    fig, ax = plt.subplots(1, 2, figsize=(9.4, 3.2))
    sm.qqplot(m.resid, line="s", ax=ax[0], markersize=2.5); ax[0].set_title("QQ plot, h = 0 residuals", fontsize=9)
    ax[1].scatter(np.arange(len(cook))[~on], cook[~on], s=4, color="#7f8c8d", label="other days")
    ax[1].scatter(np.arange(len(cook))[on], cook[on], s=18, color="#c0392b", label="deal days")
    ax[1].axhline(4 / len(cook), color="k", ls="--", lw=.8, label="4/n")
    ax[1].set_title("Cook's distance, h = 0", fontsize=9); ax[1].legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "diagnostics_tails.png", dpi=140); plt.close(fig)

    pd.DataFrame(b7(Xd, "daily dD") + b7(Xl, "lp h=0")).to_csv(TAB / "diagnostics_b7_vif.csv", index=False)

    chow, path = b8()
    out["B8_chow"] = chow
    path.to_csv(TAB / "diagnostics_b8_expanding.csv", index=False)
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ax.errorbar(range(len(path)), path.b, yerr=1.96 * path.se, fmt="o", color="#1f4e79", ms=4, capsize=2)
    ax.set_xticks(range(len(path))); ax.set_xticklabels(path.through, rotation=60, fontsize=6.5)
    ax.axhline(0, color="k", lw=.8); ax.set_ylabel("h = 0 coefficient")
    ax.set_title("h = 0 coefficient using data through each deal (OLS 95% bands)", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / "diagnostics_expanding.png", dpi=140); plt.close(fig)

    (TAB / "diagnostics_b4_b8.json").write_text(json.dumps(out, indent=2))
    pd.set_option("display.width", 220)
    print(json.dumps({k: v for k, v in out.items() if k != "B6"}, indent=1))
    for d in out["B6"]:
        print({k: v for k, v in d.items() if k != "top10"}, [t for t in d["top10"] if t["deal_day"]])
    print(est.round(4).to_string(index=False))
    print(st.round(4).to_string(index=False)); print(sp.to_string(index=False))
    print(pd.read_csv(TAB / "diagnostics_b7_vif.csv").round(2).to_string(index=False))
    print(path.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
