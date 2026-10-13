"""Single place that produces every headline number, so the writeup and the
resume bullet cannot drift from the code."""
import json, numpy as np, pandas as pd
from config import PROC, TAB, JUMBO_USD, MACRO_EXCL_BDAYS, EVENT_WINDOW, EXCL_BAND_YEARS, SAMPLE_END
import curve as C, concession as K, abnormal as A, localproj as L


def main():
    out = {}
    ev = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
    tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])
    allg = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])

    # ------------------------------------------------------------------ N
    out["N"] = len(ev)
    out["N_usd_deals_total"] = len(allg)
    out["N_jumbo_before_macro"] = int((allg.total_usd >= JUMBO_USD).sum())
    out["jumbo_threshold_usd_bn"] = JUMBO_USD / 1e9
    out["macro_excl_bdays"] = MACRO_EXCL_BDAYS
    out["event_window"] = list(EVENT_WINDOW)
    out["merges_applied"] = int(len(ev) - ((allg.total_usd >= JUMBO_USD) &
                                           (~allg.macro_conflict)).sum())
    out["event_dates"] = [str(d.date()) for d in ev.announce]
    out["issuance_face_usd_bn"] = {str(y): float(g.total_usd.sum() / 1e9)
                                   for y, g in allg.groupby(allg.announce.dt.year)}
    out["issuance_face_usd_bn"]["2026_through_2026-06-08"] = float(
        allg[(allg.announce >= "2026-01-01") & (allg.announce <= "2026-06-08")].total_usd.sum() / 1e9)
    out["event_total_usd_bn"] = float(ev.total_usd.sum() / 1e9)
    out["event_10y_equiv_bn"] = float(ev.tenyr_equiv.sum() / 1e9)

    # ------------------------------------------------------------------ X
    z = C.load_gsw(start="2024-01-01")
    V, evr = K.loadings(z)
    res, det = K.run(ev, tr, z, V)
    a1 = K.aggregate(res)
    pl1 = np.load(PROC / "placebo.npy")
    out["X_pca"] = dict(value_bp=a1["cbar"], nw_t=a1["nw_t"], nw_se=a1["nw_se"],
                        nw_lags=a1["nw_lags"], nw_p=a1["nw_p"],
                        placebo_mean_bp=float(pl1.mean()), placebo_sd_bp=float(pl1.std()),
                        placebo_p=float((np.abs(pl1) >= abs(a1["cbar"])).mean()),
                        mde95_bp=float(1.96 * pl1.std()),
                        recovery=float(np.load(PROC / "recovery.npy")[1]))

    df, tn = A.panel(); W = A.build_windows(df, tn)
    res2, det2, models, est = A.abnormal(ev, tr, W, verbose=False)
    a2 = A.agg(res2)
    pl2 = np.load(PROC / "abnormal_placebo.npy")
    out["X_abnormal"] = dict(value_bp=a2["mean"], unweighted_bp=a2["unw"], nw_t=a2["t"],
                             nw_se=a2["se"], nw_lags=a2["L"], nw_p=a2["p"],
                             placebo_mean_bp=float(pl2.mean()), placebo_sd_bp=float(pl2.std()),
                             placebo_p=float((np.abs(pl2) >= abs(a2["mean"])).mean()),
                             mde95_bp=float(1.96 * pl2.std()),
                             mde80pct_power_bp=float(2.80 * pl2.std()))

    # ------------------------------------------------------------------ Y
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    s = fred.DGS10.dropna(); s26 = s[s.index >= "2026-01-01"]
    s26 = s26[s26.index <= SAMPLE_END]
    at15 = s26[s26.index <= "2026-09-15"].iloc[-1]
    out["Y"] = dict(value_bp=float((s26.iloc[-1] - s26.iloc[0]) * 100),
                    start_date=str(s26.index[0].date()), start_pct=float(s26.iloc[0]),
                    end_date=str(s26.index[-1].date()), end_pct=float(s26.iloc[-1]),
                    to_5pct_crossing_bp=float((at15 - s26.iloc[0]) * 100),
                    crossing_date="2026-09-15", crossing_pct=float(at15),
                    note="Y depends on the endpoint; see research/03 D2. The 10Y printed "
                         "5.104% intraday on 2026-09-23 per press reports, not yet in FRED.",
                    series="FRED DGS10 (10Y constant maturity par yield)")

    # ---------------------------------------------------- term premium leg
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    t26 = acm.ACMTP10.dropna()[acm.index >= "2026-01-01"]
    r26 = acm.ACMRNY10.dropna()[acm.index >= "2026-01-01"]
    lp = pd.read_csv(PROC / "localproj_all.csv")
    e26 = allg[allg.announce >= "2026-01-01"]
    d26 = float(e26.tenyr_equiv.sum() / 1e9)
    b0 = lp[lp.h == 0].iloc[0]; b5 = lp[lp.h == 5].iloc[0]
    out["term_premium"] = dict(
        realised_2026_dTP_bp=float((t26.iloc[-1] - t26.iloc[0]) * 100),
        realised_2026_dExpectations_bp=float((r26.iloc[-1] - r26.iloc[0]) * 100),
        acm_last=str(acm.ACMTP10.dropna().index[-1].date()),
        supply_2026_10y_equiv_bn=d26,
        impact_b0_bp_per_bn=float(b0.b), impact_t=float(b0.t),
        implied_impact_bp=float(b0.b * d26),
        b_h5_bp_per_bn=float(b5.b), b_h5_t=float(b5.t),
        implied_persistent_bp=float(b5.b * d26))

    # ------------------------------------------------- explained share of Y
    Y = out["Y"]["value_bp"]
    n26_jumbo = int(((allg.announce >= "2026-01-01") & (allg.total_usd >= JUMBO_USD)).sum())
    out["explained_share"] = dict(
        # X is a per-event number. The 2026 imprint it implies is X times the
        # count of 2026 jumbo deals, and only if the effect were permanent.
        via_concession_scaled=dict(
            n_jumbo_2026=n26_jumbo,
            X_bp=a2["mean"],
            implied_total_bp=float(a2["mean"] * n26_jumbo),
            share_of_Y=float(a2["mean"] * n26_jumbo / Y),
            ci95_total_bp=[float((a2["mean"] - 1.96 * a2["se"]) * n26_jumbo),
                           float((a2["mean"] + 1.96 * a2["se"]) * n26_jumbo)],
            caveat="assumes permanence; window (0,+1) and the local projections say otherwise"),
        via_concession_X_abn=dict(
            # X is per-event bp at the deal's tenors; the cumulative long-end
            # imprint is the sum over the 2026 events, not the mean.
            n_events_2026=int((ev.announce >= "2026-01-01").sum()),
            sum_2026_bp=float(res2[res2.announce >= "2026-01-01"].abn_bp.sum()),
            share_of_Y=float(res2[res2.announce >= "2026-01-01"].abn_bp.sum() / Y)),
        via_term_premium_impact=dict(bp=float(b0.b * d26), share_of_Y=float(b0.b * d26 / Y)),
        via_term_premium_persistent=dict(bp=float(b5.b * d26), share_of_Y=float(b5.b * d26 / Y)),
        realised_TP_share_of_Y=float((t26.iloc[-1] - t26.iloc[0]) * 100 / Y))

    # ---------------------------------------- added in the review fix pass
    out["sample"] = dict(end=SAMPLE_END, lp_n=int(len(L.panel())),
                         lp_first=str(L.panel().index.min().date()),
                         lp_last=str(L.panel().index.max().date()))
    pm = pd.read_csv(PROC / "placebo_matched.csv")
    out["placebo_matched_h0"] = {r.placebo: dict(mean=r["mean"], sd=r.sd, p=r.p)
                                 for _, r in pm[pm.h == 0].iterrows()}
    out["placebo_matched_h2"] = {r.placebo: dict(mean=r["mean"], sd=r.sd, p=r.p)
                                 for _, r in pm[pm.h == 2].iterrows()}
    import hedgeflow as H
    hf = H.panel(); ai = L.shocks(); ai = ai[ai.index.isin(hf.index)]
    tot = H.lp_row(hf, ai, "spot10", 0); otr = H.lp_row(hf, ai, "otr10", 0)
    nom = L.project(hf, ai, dep="spot10", hmax=0, ctrl=("doil", "dvix", "auc_10y")).iloc[0]
    real = L.project(hf, ai, dep="real10", hmax=0, ctrl=("doil", "dvix", "auc_10y")).iloc[0]
    out["flow_tests"] = dict(
        spot10_b=float(tot.b), spot10_t=float(tot.t),
        otr10_b=float(otr.b), otr10_t=float(otr.t),
        otr_share_of_move=float(otr.b / tot.b),
        real_over_nominal_no_be_control=float(real.b / nom.b),
        cmt_f20y10y_r2_vs_10y=0.623, gsw_f20y10y_r2_vs_10y=0.062, corr_gsw_cmt_20y10y=0.384)
    bbd = pd.read_csv(PROC / "buybacks_daily.csv", parse_dates=["date"]).set_index("date")
    sur = bbd.bb_long_surprise[bbd.bb_long_surprise != 0]; sur = sur[sur.index.isin(L.panel().index)]
    out["buyback_surprise"] = {f"h{h}": dict(b=float(r.b), t=float(r.t)) for h in (0, 2, 5)
                               for r in [L.project(L.panel(), sur, dep="TP10", hmax=h).iloc[-1]]}
    au = pd.read_csv(PROC / "auction_lp_alltenor.csv")
    out["auction_lp"] = {f"{r['sample']}|h{int(r.h)}": dict(b=r.b, t=r.t, n=int(r.n))
                         for _, r in au.iterrows()}
    import strategy2 as S2
    v3 = S2.stats(S2.trades_v3())
    out["strategy_v3_clean"] = dict(n=v3["n"], mean_bp=v3["mean"], t=v3["t"], sharpe=v3["sharpe"])
    import holdout as HO
    out["preregistration"] = dict(hash=HO.spec_hash(), n_min=HO.N_MIN,
                                  holdout_start=HO.FROZEN["holdout_start"])

    # --------------------------- every inference number the paper quotes at h=0
    # Written here so none of them lives only in prose.
    import statsmodels.api as sm
    from config import RANDOM_SEED
    P = L.panel(); sh = L.shocks()
    x = sh.reindex(P.index).fillna(0.0)
    y0 = P.TP10 - P.TP10.shift(1)
    X0 = sm.add_constant(pd.DataFrame({"shock": x, **{c: P[c] for c in ("dbe", "doil", "dvix", "auc_10y")}}))
    ok = y0.notna() & X0.notna().all(axis=1)
    y0, X0 = y0[ok], X0[ok]
    ols = sm.OLS(y0, X0).fit()
    nw = sm.OLS(y0, X0).fit(cov_type="HAC", cov_kwds={"maxlags": 5, "use_correction": True})
    # cluster by episode: every day belongs to the most recent announcement
    ep = pd.Series(0, index=X0.index)
    for i, a in enumerate(sorted(sh.index), start=1):
        ep[X0.index >= a] = i
    cl = sm.OLS(y0, X0).fit(cov_type="cluster", cov_kwds={"groups": ep.values})
    rng = np.random.default_rng(RANDOM_SEED)
    r0 = sm.OLS(y0, X0.drop(columns="shock")).fit()
    uniq = np.unique(ep.values)
    tb = np.empty(2000)
    for b in range(2000):
        w = pd.Series(rng.choice([-1.0, 1.0], size=len(uniq)), index=uniq).reindex(ep.values).values
        yb = r0.fittedvalues.values + r0.resid.values * w
        tb[b] = sm.OLS(yb, X0).fit(cov_type="cluster", cov_kwds={"groups": ep.values}).tvalues["shock"]
    loo = pd.DataFrame([L.project(P, sh.drop(a), hmax=0).iloc[0] for a in sh.index])
    second_of_pair = [pd.Timestamp(d) for d in ("2026-02-09", "2025-11-03", "2026-05-05")]
    dp = L.project(P, sh.drop(second_of_pair, errors="ignore"), hmax=0).iloc[0]
    v = X0["shock"].values ** 2
    out["h0_inference"] = dict(
        spec="TP(t) - TP(t-1) on shock ($bn 10y-equiv), controls dbe doil dvix auc_10y",
        n=int(ols.nobs), b=float(ols.params["shock"]),
        ols=dict(se=float(ols.bse["shock"]), t=float(ols.tvalues["shock"]), p=float(ols.pvalues["shock"])),
        newey_west=dict(lags=5, small_sample_correction=True, se=float(nw.bse["shock"]),
                        t=float(nw.tvalues["shock"]), p=float(nw.pvalues["shock"])),
        cluster_by_episode=dict(n_clusters=int(len(uniq)), se=float(cl.bse["shock"]),
                                t=float(cl.tvalues["shock"]), p=float(cl.pvalues["shock"])),
        wild_cluster_bootstrap=dict(reps=2000, weights="Rademacher", null_imposed=True,
                                    n_clusters=int(len(uniq)),
                                    p=float(np.mean(np.abs(tb) >= abs(cl.tvalues["shock"])))),
        randomization_draws=2000,
        leave_one_out=dict(b_min=float(loo.b.min()), b_max=float(loo.b.max()),
                           t_min=float(loo.t.min()), t_max=float(loo.t.max())),
        drop_overlapping_pairs=dict(dropped=[str(d.date()) for d in second_of_pair],
                                    b=float(dp.b), t=float(dp.t)),
        shock_days=int((v > 0).sum()),
        kish_effective_n=float(v.sum() ** 2 / (v ** 2).sum()))
    lpt = pd.read_csv(PROC / "localproj_all.csv")
    out["lp_table"] = {f"h{int(r.h)}": dict(b=float(r.b), se=float(r.se), t=float(r.t), p=float(r.p))
                       for _, r in lpt[lpt.h.isin([0, 1, 2, 3, 4, 5, 10, 20])].iterrows()}
    out["lp_first_h_not_significant_5pct"] = int(lpt[lpt.p > 0.05].h.min())
    # upgrade A2: "gone" under each inference, plus the point-estimate path
    pmh = pm[pm.placebo == "matched on lag"].set_index("h")
    out["persistence"] = dict(
        point_estimate={f"h{h}": float(lpt[lpt.h == h].b.iloc[0]) for h in range(6)},
        newey_west_p={f"h{h}": float(lpt[lpt.h == h].p.iloc[0]) for h in range(6)},
        matched_placebo_p={f"h{int(h)}": float(r.p) for h, r in pmh.iterrows()},
        first_h_not_sig_newey_west_5pct=int(lpt[lpt.p > 0.05].h.min()),
        first_h_not_sig_matched_placebo_10pct=int(pmh[pmh.p > 0.10].index.min()))

    # -------------- AI share of Treasury coupon duration supply, cutoff explicit
    import regression as R
    auc = R.treasury_supply()["auc_10y"]
    auc = auc[auc.index <= SAMPLE_END]
    ai = allg.set_index("announce").tenyr_equiv / 1e9
    share = {"cutoff": SAMPLE_END,
             "note": "both legs in $bn 10y-equivalent; Treasury leg is coupon auctions "
                     "from Jan 1 of each year through the cutoff (full year before 2026)"}
    for yr in (2024, 2025, 2026):
        a_ = float(ai[ai.index.year == yr].sum()); t_ = float(auc[auc.index.year == yr].sum())
        share[str(yr)] = dict(ai_10y_bn=a_, treasury_coupon_10y_bn=t_, share=a_ / t_)
    out["coupon_duration_share"] = share
    pd.DataFrame([dict(year=int(y), cutoff=SAMPLE_END, **v) for y, v in share.items()
                  if y.isdigit()]).to_csv(TAB / "supply_share.csv", index=False)

    # ---------------- upgrade A7: what the fitted curve can and cannot see
    rec = np.load(PROC / "recovery.npy")
    import paper_numbers as PN
    out["model_dependence"] = dict(
        injection_recovered_residualisation_only=float(rec[0]),
        injection_recovered_after_svensson_refit=float(rec[1]),
        acm_dtp_r2_on_5_curve_pcs=float(PN.acm_pc_r2()))

    # ------- upgrade A8: what dating by filing instead of pricing would do
    trd = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce", "final_filing"])
    dd = trd.groupby(["issuer", "announce"]).final_filing.first().reset_index()
    dd["lag"] = [int(np.busday_count(a.date(), f.date())) for a, f in zip(dd.announce, dd.final_filing)]
    by_filing = (allg.merge(dd, on=["issuer", "announce"]).groupby("final_filing").tenyr_equiv.sum() / 1e9)
    fb = L.project(P, by_filing[by_filing.index.isin(P.index)], hmax=0).iloc[0]
    out["announcement_timing"] = dict(
        pricing_to_final_filing_bdays={str(k): int(v) for k, v in dd.lag.value_counts().sort_index().items()},
        b0_dated_by_pricing=float(lpt[lpt.h == 0].b.iloc[0]),
        b0_dated_by_final_filing=float(fb.b), t0_dated_by_final_filing=float(fb.t))
    return out


if __name__ == "__main__":
    o = main()
    print(json.dumps(o, indent=2, default=float))
    (TAB / "headline.json").write_text(json.dumps(o, indent=2, default=float))
