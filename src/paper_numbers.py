"""Every number PAPER.pdf quotes that headline.json does not already carry.

Each value is computed here from committed inputs and written to
output/tables/paper_numbers.json next to the string the paper prints. A value
that no longer rounds to the printed string is reported as a mismatch, so the
paper cannot drift from the code without the check failing.

    .venv/bin/python src/paper_numbers.py
"""
import json, sys
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, TAB, SAMPLE_START, SAMPLE_END, JUMBO_USD
import curve as C, concession as K, localproj as L, hedgeflow as H

OUT = {}


def put(key, value, printed, source, scale=1.0, nd=None):
    """Record a value with the paper's printed form. `nd` is the number of
    decimals the paper uses; `scale` converts units (100 for a percentage)."""
    v = float(value) * scale
    if nd is None:
        nd = len(printed.split(".")[1]) if "." in printed else 0
    shown = f"{abs(v):.{nd}f}" if printed.lstrip("+-−").replace(".", "").isdigit() else None
    want = printed.lstrip("+-−")
    ok = shown == want if shown is not None else None
    OUT[key] = dict(value=float(value), printed=printed, matches=ok, source=source)


def bdays_between(a, b):
    return int(np.busday_count(np.datetime64(a.date()), np.datetime64(b.date())))


def main():
    deals = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])

    # ------------------------------------------------------------ deal counts
    put("n_tranches", len(tr), "103", "tranches.csv rows")
    put("n_floating_tranches", int(tr.floating.astype(bool).sum()), "7", "tranches.csv floating")
    big = deals.sort_values("total_usd").iloc[-1]
    put("largest_deal_usd_bn", big.total_usd / 1e9, "37", f"deals_all.csv, {big.issuer} {big.announce.date()}")
    put("largest_deal_tranches", big.n_tranches, "11", "deals_all.csv n_tranches")
    put("mean_deal_10y_equiv_bn", deals.tenyr_equiv.mean() / 1e9, "21", "deals_all.csv tenyr_equiv")

    # ------------------------------------------------------- macro timing
    cal = pd.read_csv(PROC / "macro_calendar.csv", parse_dates=["date"])
    rel = sorted(set(cal.date))
    days = pd.bdate_range(SAMPLE_START, SAMPLE_END)
    near = lambda d, k: any(abs(bdays_between(r, d)) <= k for r in rel)
    clean3 = np.mean([not near(d, 3) for d in days])
    put("share_bdays_clean_3day_rule", clean3, "37", "macro_calendar.csv, +/-3 bdays of FOMC/CPI/NFP", scale=100)

    def lag_after(d):
        prior = [r for r in rel if r <= d]
        return bdays_between(prior[-1], d) if prior else None

    jumbo = deals[deals.total_usd >= JUMBO_USD]
    killed = jumbo[[near(d, 3) for d in jumbo.announce]]
    put("jumbos_killed_by_3day_rule", len(killed), "11", "deals_all.csv + macro_calendar.csv")
    put("killed_priced_1to3_after_release",
        sum(1 <= (lag_after(d) or -1) <= 3 for d in killed.announce), "8", "same")
    put("all_deals_1to3_after_release",
        sum(1 <= (lag_after(d) or -1) <= 3 for d in deals.announce), "9", "same")

    # ------------------------------------------------ curve and concession
    z = C.load_gsw(start="2024-01-01")
    V, evr = K.loadings(z)
    put("three_factor_variance_share", np.sum(evr[:3]), "99.2", "gsw.csv PCA, concession.loadings", scale=100)
    rob = pd.read_csv(TAB / "robustness_specs.csv")
    bands = rob[rob.spec.str.startswith("exclusion band")].X_pca
    put("concession_band_min_bp", bands.min(), "−0.167", "robustness_specs.csv exclusion band rows")
    put("concession_band_max_bp", bands.max(), "+0.123", "robustness_specs.csv exclusion band rows")

    # ACM TP10 against five PCs of the same curve
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    dz = z.diff().dropna()
    X = dz - dz.mean()
    u, s, vt = np.linalg.svd(X.values, full_matrices=False)
    pcs = pd.DataFrame(u[:, :5] * s[:5], index=dz.index)
    dtp = (acm.ACMTP10 * 100).diff().reindex(pcs.index)
    ok = dtp.notna()
    r2 = sm.OLS(dtp[ok], sm.add_constant(pcs[ok])).fit().rsquared
    put("acm_dtp_r2_on_5_curve_pcs", r2, "96", "acm.csv + gsw.csv", scale=100)

    # post-release drift: mean day-0 change in TP on release days
    P = L.panel()
    d0 = P.TP10 - P.TP10.shift(1)
    put("tp_change_on_release_days_bp", d0[d0.index.isin(rel)].mean(), "+0.7", "acm.csv + macro_calendar.csv")

    # ------------------------------------------------------ endpoints
    tp = acm.ACMTP10.dropna() * 100; rn = acm.ACMRNY10.dropna() * 100
    at = lambda s, d: s[s.index <= pd.Timestamp(d)].iloc[-1]
    put("dTP_2026_to_sep15_bp", at(tp, "2026-09-15") - at(tp, "2026-01-02"), "−8.6", "acm.csv")
    put("dRN_2026_to_sep15_bp", at(rn, "2026-09-15") - at(rn, "2026-01-02"), "79", "acm.csv")
    starts = ["2025-12-31", "2026-01-02", "2026-01-15", "2026-02-02", "2026-02-27"]
    ends = ["2026-06-30", "2026-07-31", "2026-08-31", "2026-09-11", "2026-09-15"]
    grid = np.array([[at(tp, e) - at(tp, s_) for e in ends] for s_ in starts])
    put("endpoint_grid_min_bp", grid.min(), "−29", "acm.csv, figures_blog.fig9_endpoints grid")
    put("endpoint_grid_max_bp", grid.max(), "+24", "same")
    put("endpoint_grid_n_positive", int((grid > 0).sum()), "12", "same")
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    y10 = fred.DGS10.dropna() * 100
    put("full_sample_d10y_bp", at(y10, SAMPLE_END) - y10[y10.index >= SAMPLE_START].iloc[0], "101", "fred.csv DGS10")
    put("full_sample_dTP_bp", at(tp, SAMPLE_END) - tp[tp.index >= SAMPLE_START].iloc[0], "+90", "acm.csv")

    # -------------------------------------------------------- buybacks
    import buybacks as B
    bs = B.build_surprise()
    lg = bs[bs.is_long & (bs.operation_date >= "2024-01-01")]
    put("long_ops_fill_to_max_share", (lg.fill >= 0.9999).mean(), "75", "buybacks.json", scale=100, nd=0)
    raw = lg.par * lg.dur / B.DUR10 / 1e9
    put("buyback_news_share", lg.ten10_surprise.abs().sum() / raw.sum(), "12", "buybacks.json", scale=100, nd=0)
    bbd = pd.read_csv(PROC / "buybacks_daily.csv", parse_dates=["date"]).set_index("date")
    sur = bbd.bb_long_surprise[bbd.bb_long_surprise != 0]; sur = sur[sur.index.isin(P.index)]
    put("buyback_surprise_days", len(sur), "18", "buybacks_daily.csv in LP panel")
    put("buyback_mean_abs_surprise_bn", sur.abs().mean(), "1", "buybacks_daily.csv", nd=0)
    bv = pd.read_csv(PROC / "buyback_vs_ai_lp.csv")
    put("buyback_raw_h0_b", bv[bv.h == 0].bb_b.iloc[0], "−0.20", "buyback_vs_ai_lp.csv")

    # ---------------------------------------------------- flow tests
    hf = H.panel(); ai = L.shocks(); ai = ai[ai.index.isin(hf.index)]
    hf["be10"] = hf.spot10 - hf.real10
    be = L.project(hf, ai, dep="be10", hmax=0, ctrl=("doil", "dvix", "auc_10y")).iloc[0]
    put("breakeven_h0_b", be.b, "+0.015", "hedgeflow panel (DGS10 - DFII10)")
    put("breakeven_h0_t", be.t, "0.8", "same")
    d10 = hf.spot10.diff()

    def r2_on_10y(col):
        y = hf[col].diff(); m = y.notna() & d10.notna()
        return sm.OLS(y[m], sm.add_constant(d10[m])).fit().rsquared
    put("cmt_f20y10y_r2", r2_on_10y("f20y10y"), "0.62", "hedgeflow panel, CMT forwards")
    put("gsw_f20y10y_r2", r2_on_10y("gsw_f20y10y"), "0.06", "hedgeflow panel, GSW forwards")
    put("corr_gsw_cmt_20y10y", hf.f20y10y.diff().corr(hf.gsw_f20y10y.diff()), "0.38", "hedgeflow panel")

    # --------------------------------------------------- trading
    import variance as VR, strategy as S, strategy2 as S2
    vd = VR.decompose(); vd["pnl"] = -vd.dy10 * VR.MODDUR
    sd5, sd1 = VR.unconditional_vol()
    put("five_day_10y_sd_bp", sd5, "11.4", "gsw.csv 10Y, overlapping 5-day changes")
    put("five_day_price_sd_bp", sd5 * VR.MODDUR, "91", "same x ModDur 8")
    put("trade_pnl_sd_bp", vd.pnl.std(ddof=1), "62", "variance.decompose")
    put("trade_window_dy10_sd_bp", vd.dy10.std(ddof=1), "7.8", "variance.decompose")
    fit = lambda y: sm.OLS(y, sm.add_constant(vd[["size10"]])).fit().rsquared
    put("pnl_r2_on_size", fit(vd.pnl), "1.2", "variance.decompose", scale=100)
    put("spread_r2_on_size", fit(vd.dy10 - vd.dy2), "21.1", "variance.decompose", scale=100)
    sig = 0.123 * vd.size10.mean()
    put("signal_bp", sig, "2.56", "0.123 (10Y spot LP h0 minus h5, hard-coded in variance.py) x mean size")
    put("signal_to_noise", sig / sd5, "0.22", "same")
    put("events_for_t2", np.ceil((2 / (sig / sd5)) ** 2), "80", "same")
    put("v1_sharpe", S.stats(S.pnl_table())["sharpe"], "+0.87", "strategy.pnl_table, 5 days, 3bp cost")
    put("v1_sharpe_2d", S.stats(S.pnl_table(hold=2))["sharpe"], "−0.88", "strategy.pnl_table hold=2")
    put("v1_sharpe_10d", S.stats(S.pnl_table(hold=10))["sharpe"], "−0.69", "strategy.pnl_table hold=10")
    put("v2_sharpe", S2.stats(S2.trades())["sharpe"], "−1.10", "strategy2.trades, size-scaled steepener")

    # -------------------------------------------------------- Japan
    import japan as J
    m = J.build()
    lags = int(np.floor(4 * (len(m) / 100) ** (2 / 9)))
    ok = m.tp10.notna() & m.pickup.notna()
    r = J.nw(m.tp10[ok], m[["pickup"]][ok], lags)
    put("japan_naive_pickup_t", r.tvalues["pickup"], "8.2", "japan.build, levels TP10 ~ pickup")

    TAB.joinpath("paper_numbers.json").write_text(json.dumps(OUT, indent=2))
    bad = {k: v for k, v in OUT.items() if v["matches"] is False}
    for k, v in OUT.items():
        flag = {True: "ok  ", False: "DIFF", None: "    "}[v["matches"]]
        print(f"{flag} {k:36s} {v['value']:12.4f}  paper {v['printed']}")
    print(f"\n{len(OUT)} numbers, {len(bad)} do not match the paper")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
