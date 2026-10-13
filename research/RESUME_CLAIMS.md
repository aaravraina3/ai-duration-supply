# Resume claims (UPGRADE_PLAN section 7)

Each phrase from the current resumes, the artifact that supports it, and a
verdict. Nothing here rewrites a bullet; it is the evidence to rewrite them from.

## QR resume

| Phrase | Verdict | Artifact | Note |
|---|---|---|---|
| Title: Fixed Income, Python | supported | the repo | |
| Title: NLP | **unsupported** | `output/tables/expected_supply.json` | D1: no text rung beat trailing issuance out of sample (MSE 166.6 baseline vs 212.3 embeddings). Per plan D1.10, NLP stays off. |
| Title: Nelson-Siegel | weak | `src/curve.py`; paper, fitted-curve rule | Descriptive figures only. No estimate uses it. |
| Title: PCA | supported | `headline.json` `model_dependence.acm_dtp_r2_on_5_curve_pcs` (0.964); `paper_numbers.json` `three_factor_variance_share` (0.992) | |
| Title: ACM | supported | `headline.json` | |
| "testing preferred-habitat duration absorption in Treasury term premium" | **partly** | `tenorlocal.json` | Duration absorption is what is tested. The preferred-habitat prediction, localization at issued maturities, was tested in C2 and **not supported** (placebo p 0.17). Vayanos-Vila is motivation, not the hypothesis. |
| "DV01-matched 10-year-equivalent AI issuance shocks from SEC EDGAR" | **partly** | `src/eventlist.py`, `deals_all.csv` | The code weights by modified duration (notional × ModDur / ModDur_10Y). That equals DV01 matching only at par prices. "Duration-weighted" is exact. |
| "Jorda local projections on ACM 10Y term premium estimating 0.08bp per billion impact response" | supported | `headline.json` `term_premium.impact_b0_bp_per_bn` (0.0812) | Unit is per $bn of **10-year-equivalent duration**, not per $bn of face. |
| "insignificant from horizon three" | **unsupported as stated** | `headline.json` `persistence` | True under Newey-West only. Under the primary inference (timing-matched placebo) it is marginal on day 0 only and insignificant from day 1 (p 0.22). |
| "permutation inference raising p to 0.08 from 0.0005 under Newey-West" | supported | `headline.json` `placebo_matched_h0`, `h0_inference.newey_west.p` | 0.083 matched; 0.00052 Newey-West. |
| "Tested dealer-hedging channel via on-the-run spread and 0.87 real-nominal TIPS pass-through" | supported | `headline.json` `flow_tests` | A6: 0.87 is the corrected spec (no breakeven control). On-the-run spread is 4% of the move. |
| "replicated Lou Yan Zhang pre-auction concession" | **unsupported** | `headline.json` `auction_lp` | All-tenor t 1.81: consistent with, not a replication (A9). |
| "signal injection showing Svensson refit inverting maturity-local supply signal" | supported | `headline.json` `model_dependence` | 0.777 recovered before the refit, −0.107 after. |
| "hashed holdout" | supported | `src/holdout.py`, hash `7afd3de6e97fcd28` | |

## ML resume

| Phrase | Verdict | Artifact | Note |
|---|---|---|---|
| Title: Python, Feature Engineering, PCA, Permutation Testing | supported | repo; `headline.json` | |
| "parsing SEC EDGAR prospectuses into 16-deal panel" | supported | `deals_all.csv`, `tranches.csv` (103 tranches) | |
| "engineering duration-weighted supply features" | supported | `deals_all.csv` `tenyr_equiv` | |
| "announcement-time alignment eliminating look-ahead leakage" | supported | `headline.json` `announcement_timing` | A8: by pricing date +0.081; by filing date −0.022 (t −0.69). The effect only exists on the true announcement day. |
| "synthetic signal injection recovering 77 percent of planted perturbation pre-smoothing against negative 10 percent post-fit" | supported | `headline.json` `model_dependence` | 77.7% and −10.7%. |
| "PCA spanning exposing 96 percent target redundancy" | supported | `headline.json` `model_dependence.acm_dtp_r2_on_5_curve_pcs` | R² 0.964 on five curve PCs. |
| "permutation testing correcting p to 0.08" | supported | `headline.json` `placebo_matched_h0` | |

## New claims the upgrade supports

| Claim | Artifact |
|---|---|
| Preregistered a 216-specification curve; every estimate positive, none significant after Romano-Wolf or Benjamini-Hochberg (headline Romano-Wolf p 0.69) | `speccurve_summary.json`, `11_UPGRADE_PREREG.md` F1 |
| Sign confirmed on a second term premium model (Kim-Wright +0.038, placebo p 0.048) and on observed yields, rising with maturity (10Y p 0.025, 30Y p 0.007) | `altdv.csv` |
| Diagnosed HAC standard errors below OLS as heteroskedasticity on 16 shock days, not autocorrelation; the variance gap explains 52% | `12_DIAGNOSTICS.md`, `b3_tests.json` T3 |
| EWC and Kiefer-Vogelsang fixed-b inference (Lazarus, Lewis, Stock, Watson 2018) | `diagnostics_hac.csv` |
| Power analysis: 80%-power detectable effect 0.116 at 16 deals; 79% power at the holdout's 32 | `power_summary.json` |
| Preregistered and logged about 50 tests with predictions written first, wrong predictions reported | `TEST_REGISTRY.csv`, `11_UPGRADE_PREREG.md` |
| Purged walk-forward model ladder with Clark-West and Diebold-Mariano tests; supply adds no out-of-sample value | `oos_forecast.json` |
| Hashed data vintages and automated number tracing (136 paper numbers mapped to source tables) | `data/VINTAGES.md`, `paper_numbers.json` |

Not claimable: anything about NLP forecasting skill (D1 null), maturity
localization (C2 null), a stock effect (C3 open), or a persistent effect being
ruled out (D-06).
