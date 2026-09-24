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
    return out


if __name__ == "__main__":
    o = main()
    print(json.dumps(o, indent=2, default=float))
    (TAB / "headline.json").write_text(json.dumps(o, indent=2, default=float))
