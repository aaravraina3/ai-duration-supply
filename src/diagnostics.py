"""Phase B assumption tests, B1 to B3 (research/12_DIAGNOSTICS.md).

Two targets, both from the existing code:
  daily  dTP10 on dD and regression.CTRL (regression.py, the duration-stock shock)
  lp_h   localproj.project at h = 0..5, dTP over t-1..t+h on the deal shock

B1 serial correlation of residuals: Ljung-Box and Breusch-Godfrey at 1, 5, 10.
B2 Newey-West bandwidth: fixed lags 0, 2, 5, 10, 20, the repo's rule, and the
   Newey-West (1994) automatic bandwidth.
B3 why HAC came out smaller than OLS, and two HAC corrections with better
   small-sample behaviour: equal-weighted cosine (EWC) with t critical values, and
   the Bartlett kernel with Kiefer-Vogelsang fixed-b critical values, both with
   the bandwidths Lazarus, Lewis, Stock and Watson (2018) recommend.

Every number goes to output/tables/diagnostics_*.csv.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, acorr_breusch_godfrey
from config import TAB, FIG, RANDOM_SEED
import localproj as L, regression as R

LP_CTRL = ("dbe", "doil", "dvix", "auc_10y")


def target_daily():
    df = R.dataset()
    X = sm.add_constant(df[["dD"] + R.CTRL])
    return df["dTP10"], X, "dD"


def target_lp(h):
    P = L.panel(); sh = L.shocks()
    x = sh.reindex(P.index).fillna(0.0)
    y = P.TP10.shift(-h) - P.TP10.shift(1)
    X = sm.add_constant(pd.DataFrame({"shock": x, **{c: P[c] for c in LP_CTRL}}))
    ok = y.notna() & X.notna().all(axis=1)
    return y[ok], X[ok], "shock"


def score(y, X, k):
    """Frisch-Waugh: the coefficient on k equals sum(xt*y)/sum(xt^2), with xt the
    part of k orthogonal to the other columns. Its sampling error is driven by the
    score u = xt * e."""
    others = X.drop(columns=k)
    xt = sm.OLS(X[k], others).fit().resid.values
    e = sm.OLS(y, X).fit().resid.values
    return xt, e, xt * e


def autocov(u, j):
    u = u - u.mean()
    return float(np.dot(u[j:], u[:len(u) - j]) / len(u))


def nw1994_lags(u):
    """Newey and West (1994) automatic bandwidth for the Bartlett kernel."""
    T = len(u)
    n = int(np.floor(4 * (T / 100) ** (2 / 9)))
    g = [autocov(u, j) for j in range(n + 1)]
    s0 = g[0] + 2 * sum(g[1:])
    s1 = 2 * sum(j * g[j] for j in range(1, n + 1))
    gamma = 1.1447 * ((s1 / s0) ** 2) ** (1 / 3)
    return int(np.floor(gamma * T ** (1 / 3)))


def bartlett_lrv(u, M):
    """Long-run variance with Bartlett weights 1 - j/M, j < M (fixed-b form)."""
    return autocov(u, 0) + 2 * sum((1 - j / M) * autocov(u, j) for j in range(1, M))


def ewc_lrv(u, B):
    T = len(u); t = np.arange(1, T + 1)
    lam = [np.sqrt(2 / T) * np.sum(np.cos(np.pi * j * (t - 0.5) / T) * u) for j in range(1, B + 1)]
    return float(np.mean(np.square(lam)))


def fixedb_null(T, M, reps=5000, seed=RANDOM_SEED):
    """Simulated Kiefer-Vogelsang fixed-b null distribution of |t| for the
    Bartlett kernel at b = M/T. The fixed-b limit is the same as for a location
    model, so iid normal draws at the sample's T and M reproduce it."""
    rng = np.random.default_rng(seed)
    out = np.empty(reps)
    for r in range(reps):
        u = rng.standard_normal(T)
        lrv = bartlett_lrv(u, M)
        out[r] = abs(u.mean() / np.sqrt(lrv / T))
    return out


def hac_table(y, X, k, name, rule=None):
    ols = sm.OLS(y, X).fit()
    xt, e, u = score(y, X, k)
    T = len(u); b = float(ols.params[k]); sxx = float(np.sum(xt ** 2))
    rows = [dict(target=name, method="OLS (iid)", lags=None, se=float(ols.bse[k]),
                 t=float(ols.tvalues[k]), p=float(ols.pvalues[k]))]
    auto = nw1994_lags(u)
    lagset = [(0, "fixed"), (2, "fixed"), (5, "fixed"), (10, "fixed"), (20, "fixed"), (auto, "NW1994 automatic")]
    if rule is not None:
        lagset.append((rule, "repo rule"))
    for lag, kind in lagset:
        m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lag, "use_correction": True})
        rows.append(dict(target=name, method=f"Newey-West, {kind}", lags=lag, se=float(m.bse[k]),
                         t=float(m.tvalues[k]), p=float(m.pvalues[k])))
    # LLSW (2018) recommendations: EWC with B = 0.4 T^(2/3); NW with S = 1.3 T^(1/2), fixed-b
    B = int(np.floor(0.4 * T ** (2 / 3)))
    se = np.sqrt(T * ewc_lrv(u, B)) / sxx
    tt = b / se
    rows.append(dict(target=name, method="EWC, t critical values (LLSW 2018)", lags=B, se=se, t=tt,
                     p=float(2 * stats.t.sf(abs(tt), B))))
    M = int(np.ceil(1.3 * np.sqrt(T)))
    se = np.sqrt(T * bartlett_lrv(u, M)) / sxx
    tt = b / se
    null = fixedb_null(T, M)
    rows.append(dict(target=name, method="Bartlett, Kiefer-Vogelsang fixed-b", lags=M, se=se, t=tt,
                     p=float(np.mean(null >= abs(tt))), cv5=float(np.quantile(null, 0.95))))
    return rows, dict(target=name, b=b, T=T, nw1994_lags=auto, ewc_B=B, fixedb_M=M)


def serial_rows(y, X, name):
    m = sm.OLS(y, X).fit()
    lb = acorr_ljungbox(m.resid, lags=[1, 5, 10])
    rows = []
    for lag in (1, 5, 10):
        lm, lmp, _, _ = acorr_breusch_godfrey(m, nlags=lag)
        rows.append(dict(target=name, lag=lag, ljung_box=float(lb.loc[lag, "lb_stat"]),
                         ljung_box_p=float(lb.loc[lag, "lb_pvalue"]),
                         breusch_godfrey=float(lm), breusch_godfrey_p=float(lmp)))
    return rows, m.resid


def b3_diagnose(y, X, k, name):
    xt, e, u = score(y, X, k)
    x = X[k].values
    top = np.sort(x ** 2)[::-1][:16].sum() / np.sum(x ** 2)
    on = np.zeros(len(x), bool); on[np.argsort(x ** 2)[::-1][:16]] = True   # the 16 deal days
    topt = np.sort(xt ** 2)[::-1][:16].sum() / np.sum(xt ** 2)
    acf_e = [pd.Series(e).autocorr(j) for j in range(1, 6)]
    acf_u = [pd.Series(u).autocorr(j) for j in range(1, 6)]
    return dict(target=name, share_regressor_ss_top16=float(top), share_partialled_ss_top16=float(topt),
                **{f"resid_acf{j}": float(v) for j, v in enumerate(acf_e, 1)},
                **{f"score_acf{j}": float(v) for j, v in enumerate(acf_u, 1)},
                score_lrv_over_var=float(bartlett_lrv(u, 6) / autocov(u, 0)),
                resid_sd_shock_days=float(e[on].std(ddof=1)),
                resid_sd_other_days=float(e[~on].std(ddof=1)),
                **{f"{c}_t": float(sm.OLS(y, X).fit(cov_type=c).tvalues[k]) for c in ("HC0", "HC2", "HC3")})


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    targets = [("daily dD", *target_daily(), R.nw_lags(len(target_daily()[0])))]
    for h in range(6):
        targets.append((f"lp h={h}", *target_lp(h), h + 5))

    serial, hac, meta, b3, resids = [], [], [], [], {}
    for name, y, X, k, rule in targets:
        s, r = serial_rows(y, X, name); serial += s; resids[name] = r
        h, m = hac_table(y, X, k, name, rule); hac += h; meta.append(m)
        b3.append(b3_diagnose(y, X, k, name))
        print("done", name, flush=True)
    pd.DataFrame(serial).to_csv(TAB / "diagnostics_serial.csv", index=False)
    pd.DataFrame(hac).to_csv(TAB / "diagnostics_hac.csv", index=False)
    pd.DataFrame(meta).to_csv(TAB / "diagnostics_bandwidths.csv", index=False)
    pd.DataFrame(b3).to_csv(TAB / "diagnostics_b3.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.0))
    for ax, name in zip(axes, ["daily dD", "lp h=0"]):
        r = resids[name].values
        ac = [pd.Series(r).autocorr(j) for j in range(1, 21)]
        band = 1.96 / np.sqrt(len(r))
        ax.bar(range(1, 21), ac, color="#1f4e79")
        ax.axhspan(-band, band, color="grey", alpha=.2)
        ax.axhline(0, color="k", lw=.8)
        ax.set_title(f"Residual autocorrelation, {name}", fontsize=9)
        ax.set_xlabel("lag (business days)")
    fig.tight_layout(); fig.savefig(FIG / "diagnostics_acf.png", dpi=140); plt.close(fig)
    return pd.DataFrame(serial), pd.DataFrame(hac), pd.DataFrame(b3)


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    s, h, b = main()
    print(s.round(4).to_string(index=False))
    print(h.round(4).to_string(index=False))
    print(b.round(3).T.to_string())
