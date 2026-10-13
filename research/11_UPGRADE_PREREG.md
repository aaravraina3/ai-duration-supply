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
