# Upgrade preregistration

Each test below is written here and committed before it runs. The commit hash of
the registration and of the result are recorded next to each.

---

## P1. Pooled early response, days 0 to 2 (upgrade A2)

Registered 2026-10-12, before running.

**Why.** Horizon-by-horizon p-values are non-monotonic (Newey-West p 0.0005,
0.049, 0.001 at h = 0, 1, 2; matched placebo 0.083, 0.217, 0.127), which says the
per-horizon tests are noisy at about ten effective observations. One test over the
early window uses the same information with less noise.

**Note on what is already cumulative.** Each local projection coefficient is
already a cumulative change, `b_h` on `TP(t+h) - TP(t-1)`. So `b_2` alone is the
cumulative response through day 2, and its matched-placebo p is 0.127. The new
statistic pools the path instead of reading only its end point.

| | |
|---|---|
| Statistic | `S = (b_0 + b_1 + b_2) / 3`, the average of the h = 0, 1, 2 local projection coefficients from `localproj.project`, same controls (dbe, doil, dvix, auc_10y), all 16 deals |
| Inference | Timing-matched placebo on lag, `placebo_matched.draw_matched`, 2000 draws, seed `RANDOM_SEED`. Each draw recomputes b_0, b_1, b_2 on the same placebo dates and takes their mean |
| p-value | Two-sided, share of draws with abs(S_placebo) >= abs(S_obs), same convention as every other placebo p in the repo. The one-sided p is reported too |
| Secondary | Same statistic under the uniform placebo |
| Observed value, known before running | S = (0.0812 + 0.0777 + 0.1148) / 3 = 0.0912. The point estimates are already known; only the placebo distribution is not |

**Prediction.** S is positive (known). The matched-placebo p is between 0.05 and
0.15: pooling should beat the noisier per-horizon p at h = 1 and 2, but not get
below the day-0 p of 0.083, because about half of the h = 2 response is
post-FOMC drift that the matched placebo reproduces.

**Decision.** Reported in the paper and the log whatever it shows. It does not
replace the day-0 test as the headline, and it is exploratory like everything
else outside `holdout.py`.

Registration commit: `e469395`
Result commit: the commit that adds this block (see `git log -- research/11_UPGRADE_PREREG.md`)

**Result** (`src/cumulative.py`, `output/tables/pooled_early_response.json`):

| Placebo | S_obs | placebo mean | placebo sd | p two-sided | p one-sided |
|---|---|---|---|---|---|
| matched on lag (primary) | +0.0912 | +0.0107 | 0.0512 | **0.081** | 0.065 |
| uniform | +0.0912 | +0.0023 | 0.0544 | 0.098 | 0.057 |

Against the prediction: p is inside the predicted 0.05 to 0.15 band. The second
half of the prediction, that pooling would not get below the day-0 p of 0.083, is
off by a hair: 0.081. Read as the same as day 0. Pooling did not sharpen the
result, which says the day-1 and day-2 moves add little beyond day 0.

---

## Tests of the B3 claims (registered 2026-10-12, before running)

Common pieces:
- **Deal days**: the 16 announcement dates in `localproj.shocks()`.
- **Matched placebo**: `placebo_matched.draw_matched`, 16 dates at the same lag
  after the last FOMC/CPI/NFP release, five-session exclusion around real deals,
  `RANDOM_SEED`, **10,000 draws** (no refit needed, so more draws are cheap).
- All p-values are one-sided in the direction of the claim unless stated.

### T1. Are deal-day residuals quieter than chance?

Claim tested: "deal-day residuals are quieter" (B3).

- **Residuals, primary**: from the controls-only model at h = 0,
  `TP(t) - TP(t-1)` on const, dbe, doil, dvix, auc_10y, **without the shock**.
  Reason: with the shock in the model, OLS fits the 16 deal days and mechanically
  shrinks their residuals, so the full-model residuals would bias the test toward
  "quieter".
- **Residuals, secondary**: the full h = 0 model with the shock (the residuals B3
  actually used).
- **Statistic**: sd of the residuals on the 16 deal days.
- **Test 1**: Brown-Forsythe (Levene with median centring), deal days vs all other
  days, two-sided.
- **Test 2**: permutation. p = share of 10,000 matched-placebo draws whose 16-date
  residual sd is <= the deal-day sd. Uniform-placebo version reported too.
- **Prediction**: on the primary residuals the gap shrinks and is **not**
  significant at 5% under the matched placebo. On the secondary residuals it is
  smaller than placebo but marginal (p between 0.02 and 0.20).

### T2. Calm before the deal

Claim tested: "issuers choose calm windows". Uses only data strictly before each
day, so the deal cannot cause the measure.

- **Measures** for each day t: (a) trailing realized volatility, the sd of daily
  ACM TP10 changes over t-20 to t-1; (b) VIX close on t-1.
- **Statistic**: median of each measure across the 16 deal days.
- **Test**: p = share of 10,000 matched-placebo draws with median <= the deal-day
  median. Uniform version reported too. Each deal's percentile of each measure
  against all sample days is reported (the B4 check).
- **Prediction**: both medians below the placebo median, neither significant at 5%.

### T3. Does the deal-day variance gap explain OLS vs HAC?

Claim tested: "the OLS-to-Newey-West gap is the deal-day variance difference".

- From the h = 0 local projection, compute the OLS, HC0 and Newey-West (5 lags)
  standard errors on the shock.
- **Counterfactual**: rescale the full-model residuals on the 16 deal days by
  `sd(other days) / sd(deal days)`, so deal days have the same residual spread as
  every other day, and recompute HC0 and Newey-West from the rescaled residuals.
- **Claim holds if** the counterfactual Newey-West SE is within 10% of the OLS
  SE. Also reported: the share of the log variance gap closed,
  `(log V_cf - log V_nw) / (log V_ols - log V_nw)`.
- **Prediction**: holds (counterfactual within 10% of OLS).

### T4. Are deals priced just after macro releases more often than chance?

Claim tested: "8 of 11 priced within three business days after a release".

- **Lag**: `placebo_matched.lag_table` on the local-projection trading days, so
  lag = trading days since the most recent FOMC/CPI/NFP release on or before the
  day (0 = release day).
- **Primary, all 16 deals**: for k = 1, 2, 3, count deals with 1 <= lag <= k.
  Base rate = share of all sample trading days with 1 <= lag <= k. Exact binomial
  test, one-sided greater. Permutation: 100,000 draws of 16 distinct random
  sample trading days, p = share with count >= observed.
- **Secondary, the 11 deals the ±3 rule dropped**: same test. Those 11 were
  selected *because* they sit within ±3 business days of a release, so a fair base
  rate is the share of days within ±3 of a release that are 1 to 3 days after one.
  Both the unconditional and this conditional base rate are reported.
- **Prediction**: all 16, k = 3: share above base rate, binomial p between 0.02
  and 0.15. Secondary: the 8 of 11 is not significant against the conditional base
  rate.

### V1. Volatility-matched placebo (for B4 to B8)

- Placebo dates matched on **lag after the last release and on the tercile of
  trailing 20-day TP10 realized volatility** (t-20 to t-1; terciles over all
  sample days). If a lag-by-tercile cell has no free date, fall back to lag only;
  the fallback rate is reported.
- Used as the randomization inference for the headline coefficient under each
  B4 to B8 correction, with 2000 draws, two-sided, alongside the existing
  lag-only placebo.
- **Prediction** for the plain h = 0 coefficient: p between 0.08 and 0.20, at or
  above the lag-only 0.083.

---

## F1. The B9 specification family (registered 2026-10-12, not yet run)

Every combination below is one specification. All use the local-projection
design, all 16 deals unless a choice says otherwise, and `SAMPLE_END`.

| Dimension | Choices |
|---|---|
| Dependent variable | ACM TP10; observed 10Y yield (DGS10) |
| Horizon | h = 0; pooled mean of h = 0, 1, 2 (P1's statistic) |
| Controls | dbe, doil, dvix, auc_10y (headline); none; headline without auc_10y |
| Shock | 10y-equivalent duration ($bn); face value ($bn); 10y-equivalent, jumbo deals (>= $10B) only |
| Sample start | 2024-01-03; 2025-01-02 |
| Macro filter | none; drop deals priced on a release day (lag 0); drop deals with a release inside the t-1 to t+1 window |

2 x 2 x 3 x 3 x 2 x 3 = **216 specifications**. The Newey-West lag rule is not a
dimension: it changes bands, not estimates, and inference here is by placebo.
Bands are drawn with the repo rule (h + 5).

- **Per-spec p**: matched-on-lag placebo, 2000 draws, two-sided. The same 2000
  placebo date sets are used for every spec, so the joint null distribution across
  specs is preserved.
- **Romano-Wolf**: stepdown adjusted p-values from that joint placebo
  distribution, using the studentised statistic `|b| / sd_placebo`.
- **Benjamini-Hochberg**: FDR-adjusted p across the 216.
- **Reported**: the specification curve (estimates sorted, bands, choice panel),
  share with a positive sign, share with raw p < 0.10 and < 0.05, and the adjusted
  p of the headline spec (ACM TP10, h = 0, headline controls, 10y-equivalent, full
  sample, no filter).
- **Prediction**: more than 90% of specs positive; under 30% with raw p < 0.05;
  headline Romano-Wolf p above 0.10.

Specs that cannot be estimated (for example, a filter leaving fewer than 5 deals)
are reported as missing, not dropped silently.

---

## Results for T1 to T4 (`src/b3_tests.py`, `output/tables/b3_tests.json`)

**T1. Not established.** Controls-only residual sd 2.80 on deal days against 4.00
on others. Brown-Forsythe p 0.31. Matched placebo one-sided p 0.129 (uniform
0.119). Full-model residuals: 2.84 against 4.00, Brown-Forsythe p 0.21, matched p
0.136. Prediction: primary not significant, held; secondary marginal (0.02 to
0.20), held. **The deal-day variance gap is not distinguishable from chance.**

**T2. Mixed, and the prediction was wrong.** Trailing 20-day TP10 volatility
before deal days: median 3.54 against a matched-placebo median of 4.27, one-sided p
**0.015** (uniform 0.020). Prediction said not significant; it is. VIX on the
prior close: median 17.6 against 16.2, p 0.93 for "calmer", so deal days came
after *higher* VIX, if anything. The two pre-deal measures disagree. Two measures
were tested, so 0.015 is one of two.

**T3. Fails.** Equalising deal-day residual spread raises the Newey-West SE from
0.0233 to 0.0325, against OLS 0.0441: ratio 0.74, outside the 10% band. It closes
52% of the log variance gap. **The deal-day variance difference explains about
half of the OLS-to-HAC gap, not all of it.** The rest has not been examined.

**T4. Marginal for k = 3, not for 1 or 2.** All 16 deals, priced 1 to k trading
days after a release:

| k | count | base rate | binomial p | permutation p |
|---|---|---|---|---|
| 1 | 4 of 16 | 0.125 | 0.130 | 0.128 |
| 2 | 6 of 16 | 0.237 | 0.156 | 0.153 |
| 3 | 9 of 16 | 0.326 | **0.044** | **0.041** |

Three windows were tested, so the k = 3 result is one of three. Secondary, the
11 deals the ±3 rule dropped: 8 of 11, p 0.008 against the unconditional base
rate, but **p 0.099 against the conditional base rate (0.489)**, which is the fair
one because those 11 were selected for being within ±3 days of a release.
Prediction held on both.

## Result for V1 (`src/diagnostics_b48.py`, `output/tables/diagnostics_b4b6_estimates.csv`)

Plain h = 0 OLS on the 20-day-shorter sample (+0.0809): vol-matched placebo p
**0.053**, lag-only 0.098. Fallback rate 0%. Prediction (0.08 to 0.20, at or
above lag-only): **wrong**. Matching on volatility tightened the placebo (sd 0.039
vs 0.048) and lowered p.

## Result for F1 (`src/speccurve.py`, `output/tables/speccurve.csv`, `speccurve_summary.json`, `output/figures/speccurve.png`)

216 specs, all estimable (none missing). **100% positive.** Raw placebo p below
0.10 in 38% of specs, below 0.05 in 9%. After correction across the family,
**no spec has Romano-Wolf p or BH p below 0.10.** Headline spec: b +0.0812 (equals
`headline.json`), raw p 0.0705, Romano-Wolf p **0.69**, BH p 0.24.

Predictions: more than 90% positive, held (100%); under 30% with raw p < 0.05,
held (9%); headline Romano-Wolf p above 0.10, held (0.69). Deviations: bands drawn
from the placebo sd, not Newey-West (DECISIONS D-09); one dimension degenerate
(D-10).

---

# Phase C and D registrations (2026-10-13, before any of them ran)

Shared across C1 to C5 unless stated: sample `SAMPLE_START` to `SAMPLE_END`
(every series cut there, including the new FRED pulls, which run past the holdout
start); headline controls (dbe, doil, dvix, auc_10y); primary inference the
matched-on-lag placebo, 2000 draws, two-sided, one placebo date per deal per draw
(as in F1); Newey-West (h + 5) for comparison.

## C1. Alternative dependent variables (`src/altdv.py`)

- Dependents: Kim-Wright 10Y term premium (FRED `THREEFYTP10`, the Fed Board's
  three-factor model); CMT 2, 5, 7, 10, 20, 30Y (FRED `DGS*`); slopes 10s2s
  (DGS10 - DGS2) and 30s10s (DGS30 - DGS10). All in bp.
- Local projections h = 0 to 5. Placebo p at h = 0 and for the pooled h = 0 to 2
  statistic; Newey-West at every h.
- Already known before running: DGS10 at h = 0 is +0.097 (t 3.48, `flow_tests`).
- **Predictions**: Kim-Wright h = 0 positive with placebo p <= 0.15; 10, 20 and 30Y
  h = 0 all positive; the 2Y response smaller than the 10Y; 10s2s positive. If
  Kim-Wright disagrees with ACM in sign, the ACM result is model-dependent.

## C2. Maturity localization on observed yields (`src/tenorlocal.py`)

- Exposure: each tranche's 10y-equivalent duration is split between the two
  neighbouring CMT tenors in {2, 5, 7, 10, 20, 30} by linear weights in years to
  maturity (all to 2Y below 2 years, all to 30Y above 30). Exposure at tenor k on
  day t is the sum over deals announced on t.
- Test: panel of the six tenors by day, `dy(k,t) = day FE + tenor FE + beta x
  exposure(k,t) + e`, h = 0. With day fixed effects, beta is identified only from
  how the move differs across tenors on deal days, so a curve-wide move cannot
  produce it. Placebo: each deal moves to its matched date carrying its exposure
  profile.
- Fitted curves are not used.
- **Prediction**: beta positive but not significant (placebo p > 0.10), i.e. the
  response looks curve-wide rather than localized. Reported whichever way it goes.

## C3. Stock effect (`src/stockeffect.py`)

- Monthly (month-end), 2024-01 to the month of `SAMPLE_END`. Stock = cumulative
  outstanding AI 10y-equivalent duration announced since 2024-01-01, no decay.
  Dependent = ACM TP10 month-end level.
- Steps: ADF and KPSS on both levels; Engle-Granger and Johansen (trace, one lag)
  cointegration. If neither finds cointegration at 5%, the estimate is changes on
  changes: monthly dTP on monthly new issuance, with monthly controls (change in
  breakeven, oil log change, change in VIX, monthly coupon 10y-equivalent supply).
- Inference: permutation of monthly issuance across months, 10,000 draws,
  two-sided (primary); Newey-West, 2 lags, for comparison. MDE at 80% from the
  permutation sd.
- **Prediction**: no cointegration; the changes coefficient positive with
  permutation p > 0.10; MDE larger than the coefficient. Low power is expected and
  will be stated with the B10 numbers.

## C4. MBS supply bound (`src/mbs.py`)

- Weekly, Wednesday to Wednesday. dTP10 weekly on the week's AI shock (deals
  announced Thursday to Wednesday), weekly controls (change in breakeven, oil log
  change, change in VIX, weekly coupon 10y-equivalent supply), with and without
  the weekly change in Fed MBS holdings (FRED `WSHOMCB`, $bn). Series ID verified
  by the downloaded file's header.
- Reported: AI coefficient both ways and the percentage change; MBS coefficient.
  Newey-West (4 lags) only, since this is a sensitivity bound, not a test of the
  AI effect.
- **Prediction**: the AI coefficient changes by less than 20%; the MBS coefficient
  is not significant at 5%.

## C5. Reverse causality: does deal timing depend on market conditions? (`src/timing.py`)

- Daily, all sample trading days. Outcome: 1 if a deal is announced that day.
  Regressors, all known before the day: a coupon auction scheduled that day
  (auc_10y > 0), 5-day change in DGS10 ending t-1, 10s2s slope at t-1, Baa minus
  10Y spread (FRED `BAA10Y`) at t-1.
- Logit. Joint test by permutation of the 16 deal days across all trading days,
  10,000 draws, likelihood-ratio statistic (primary); per-coefficient Wald p
  reported.
- Power: simulated, 1000 samples of 16 events from a logit with odds ratio 2 per
  sd on one regressor; share rejecting at 5% with the same permutation test (200
  permutations per sample).
- **Prediction**: joint permutation p > 0.10; power below 50%.

## D1. Anticipated versus surprise supply (`src/expected_supply.py`)

- Corpus: `nlp_corpus.csv` (archived MD&A, liquidity and capex passages, 10-K and
  10-Q), dated by filing date. Deduplicate first: sentence embeddings, greedy,
  cosine > 0.90, keeping the earliest-filed copy. Counts before and after reported.
- Embeddings: `sentence-transformers/all-mpnet-base-v2`, version recorded.
- Unit: one filing. Target: the issuer's realized 10y-equivalent USD issuance in
  the 90 days after the filing date.
- Ladder: rung 0 trailing 365-day issuance; rung 1 adds the filing's
  decayed passage count (30-day half-life, `NLP_HALFLIFE_DAYS`); rung 2 adds the
  largest capital-expenditure dollar figure stated in the filing's passages
  (regex); rung 3 ridge on the mean filing embedding plus rung 2 inputs, penalty
  chosen inside an inner walk-forward on training filings only.
- Validation: expanding walk-forward by filing date; a training filing is used
  only if its 90-day target window ends before the test filing date (purge plus
  embargo). The first 12 filings are warm-up. Score: out-of-sample MSE; one
  standard error rule against the rung below.
- Decomposition: for each deal, expected = the chosen rung's forecast from the
  issuer's latest filing before the deal, minus that issuer's issuance between
  that filing and the deal, floored at 0. Surprise = deal size minus expected.
- Test: h = 0 local projection with expected and surprise as two regressors,
  headline controls, placebo moving both together.
- **Predictions**: the plan's: surprise coefficient positive and larger than the
  expected coefficient. Mine: the text rungs do not beat rung 1 out of sample, and
  neither coefficient is significant.

## D2. Out-of-sample value (`src/oos_forecast.py`)

- Targets: TP10(t+h) - TP10(t), h = 1 and 3 trading days.
- Features at the close of t: dTP10, dbe, doil, dvix, auc_10y (rung 1); plus the
  day's deal shock and the decayed stock change dD (rung 2).
- Rungs: 0 historical mean and zero; 1 OLS macro; 2 OLS macro plus supply. Climb
  to 3 or higher only if the 5.0 rules are met, with the diagnosis written first.
- Validation: expanding window, first 250 days training, refit daily, the last h
  training labels purged, embargo h.
- Metrics: out-of-sample R² against the historical mean; Clark-West for rung 2 vs
  1; Diebold-Mariano for rung 1 vs zero.
- **Prediction**: rung 2 does not beat rung 1 (Clark-West p > 0.10); every rung's
  out-of-sample R² is at or below zero; the ladder stops at rung 2.
