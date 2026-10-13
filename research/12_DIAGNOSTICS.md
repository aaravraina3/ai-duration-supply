# Diagnostics (Phase B)

Assumption tests for the two inference targets, from `src/diagnostics.py`:

- **daily**: `dTP10` on `dD` (the decayed duration stock's daily change) and
  `regression.CTRL`, n = 680 (`regression.py`)
- **lp h**: the local projection `TP(t+h) - TP(t-1)` on the deal shock at
  h = 0..5, controls dbe, doil, dvix, auc_10y, n = 679 at h = 0 (`localproj.py`)

Tables: `output/tables/diagnostics_serial.csv`, `diagnostics_hac.csv`,
`diagnostics_bandwidths.csv`, `diagnostics_b3.csv`. Figure:
`output/figures/diagnostics_acf.png`.

Status: B1 to B8 done, plus T1 to T4 testing the B3 claims (results in
`11_UPGRADE_PREREG.md`). B9 is registered as F1 and not run. B10 not run.

---

## B1. Serial correlation

| target | Ljung-Box p, lags 1 / 5 / 10 | Breusch-Godfrey p, lags 1 / 5 / 10 | residual autocorrelation at lag 1 |
|---|---|---|---|
| daily | 0.0002 / 0.0001 / 0.003 | 0.0002 / 0.0001 / 0.002 | −0.14 |
| lp h=0 | 0.0003 / 0.0001 / 0.004 | 0.0003 / 0.0001 / 0.002 | −0.14 |
| lp h=1 to 5 | all < 0.0001 | all < 0.0001 | +0.30 rising to +0.75 |

Residuals are serially correlated in every target. At h = 0 the correlation is
negative at lag 1 (−0.14): daily term-premium changes partly reverse the next
day. At h > 0 it is strongly positive, and that part is **by construction**: the
dependent variable `TP(t+h) - TP(t-1)` overlaps across consecutive days, so
neighbouring residuals share h of their h + 1 daily changes. The test is reported
anyway.

Correction: Newey-West, already used, plus the B3 alternatives.

## B2. Newey-West bandwidth

Headline t on the deal shock under every bandwidth (`diagnostics_hac.csv`):

| lags | lp h=0 t | daily t |
|---|---|---|
| OLS, no correction | 1.84 | 1.97 |
| 0 (heteroskedasticity only) | 3.25 | 3.56 |
| 2 | 3.35 | 3.62 |
| 5 (repo rule at h = 0) | 3.47 | 3.75 |
| 10 | 3.53 | 3.77 |
| 20 | 3.77 | 3.88 |
| Newey-West (1994) automatic: 11 lags | 3.56 | 3.78 |

The bandwidth barely matters: t moves from 3.25 to 3.77 across 0 to 20 lags, and
the automatic selector picks 11 at h = 0 (8, 4, 2, 2, 4 at h = 1 to 5). **The jump
from OLS to Newey-West happens entirely at lag 0**, before any autocorrelation
correction is applied. That points at B3's answer.

## B3. Why the HAC standard error is smaller than OLS

The audit flagged that the Newey-West SE (0.0234) is about half the OLS SE
(0.0441). The plan's working hypothesis was negative autocorrelation in the score
shrinking the HAC variance. **That is not what happened.**

**Autocorrelation is not the cause.** The score `u = x̃·e`, which is what HAC
corrects, has almost no autocorrelation: lags 1 to 5 at h = 0 are −0.03, −0.04,
−0.01, 0.00, −0.07. The Bartlett long-run variance with 6 lags is 0.88 times the
plain variance, so autocorrelation pulls the SE down by only about 6%. Newey-West
at lag 0, which corrects nothing for autocorrelation, already gives 0.0250.

**Heteroskedasticity is.** The regressor is zero on all but 16 days (100% of its
sum of squares; 97% after partialling out the controls). So the coefficient's
variance depends only on the residuals of those 16 days. In this sample they are
smaller than on other days:

| | residual sd, 16 deal days | residual sd, other days |
|---|---|---|
| lp h=0 | 2.84 bp | 4.00 bp |
| daily | 2.80 bp | 4.00 bp |

OLS assumes every day has the average variance. A heteroskedasticity-robust SE
uses the deal days' own residuals, which are about 30% smaller, so its variance is
about half. **Untested so far:** whether that gap is more than chance with 16 days,
whether deals are timed into calm windows, and whether the gap fully accounts for
the OLS-to-HAC difference. These are T1 to T3 in `11_UPGRADE_PREREG.md`, and nothing
below is interpreted until they run.

**The corrections agree with Newey-West, and that is the problem.**

| lp h=0 | se | t | p |
|---|---|---|---|
| OLS | 0.0441 | 1.84 | 0.066 |
| HC0 / HC2 / HC3 | | 3.26 / 3.15 / 3.03 | |
| Newey-West, 5 lags | 0.0234 | 3.47 | 0.0005 |
| EWC, B = 30, t(30) critical values (LLSW 2018) | 0.0206 | 3.94 | 0.0005 |
| Bartlett, M = 34, Kiefer-Vogelsang fixed-b (simulated, 5% cv 2.06) | 0.0200 | 4.06 | 0.0004 |

The small-sample HAC fixes are built for autocorrelation, and there is little of
it, so they don't change the answer. The leverage corrections HC2 and HC3, which
target exactly this case of a few high-leverage days (deal-day leverage averages
0.068 against 0.007 elsewhere), shave t only to 3.0. Every analytical SE here
estimates the variance from 16 residuals, so the SE is itself estimated from 16
numbers. With 16 numbers, a run of quiet days is enough to make it look precise.

**What randomization does differently.** The placebo asks how large the coefficient
gets on other dates with the same timing after a macro release. Its standard
deviation is 0.0466 (matched on lag), close to the OLS SE of 0.0441 and nearly
double the robust SEs. The two measures of noise disagree by about a factor of two,
and the reason is not established yet (T1 to T3). Randomization is the primary
inference because it does not depend on estimating a variance from 16 residuals;
every HAC number is for comparison only. The paper will say this
explicitly in the Phase E rewrite.

The daily regression on `dD` shows the same pattern (OLS t 1.97, HC0 3.58,
Newey-West 3.75 to 3.88, EWC 3.89, fixed-b 4.10).

---

## B3 follow-ups: T1 to T4

Registered in `f304594` before running. Full results in `11_UPGRADE_PREREG.md`.
In short:
- **T1**: the deal-day residual gap (2.80 vs 4.00bp) is **not distinguishable from
  chance** (matched placebo p 0.13, Brown-Forsythe p 0.31).
- **T2**: trailing 20-day TP volatility before deals is lower than on matched
  placebo dates (p 0.015). Prior-day VIX is not lower; it is slightly higher.
- **T3**: equalising the deal-day spread closes **52%** of the OLS-to-HAC log
  variance gap. It does not explain all of it.
- **T4**: 9 of 16 deals priced 1 to 3 trading days after a release, against a 33%
  base rate (p 0.044); not significant at 1 or 2 days. The "8 of 11" is p 0.10
  against the fair conditional base rate.

So the B3 section above stands as arithmetic: the regressor lives on 16 days and
robust SEs use those 16 residuals. **Why** those residuals are small is not
established.

---

## Inference for B4 to B8: the volatility-matched placebo (V1)

Placebo dates matched on lag after the last release and on the tercile of
trailing 20-day TP10 volatility (t-20 to t-1). Every lag-by-tercile cell had a
free date, so the fallback rate was **0%**. 2000 draws, two-sided.

These estimates need 20 days of trailing volatility, so the sample starts 20 days
later than the headline and the plain OLS estimate is **+0.0809**, not +0.0812.

## B4. Heteroskedasticity and volatility clustering

| target | Breusch-Pagan p | White p | ARCH LM (5) p |
|---|---|---|---|
| daily | 0.0001 | < 0.0001 | < 0.0001 |
| lp h=0 | < 0.0001 | < 0.0001 | < 0.0001 |

Both strongly heteroskedastic, with volatility clustering. Deal-day percentiles
of prior-day VIX and trailing TP volatility are in `b3_tests.json` (T2). The
2024-08-07 deal priced at the **97th** VIX percentile (the yen carry unwind week),
and the 2025-04-28 deal at the 94th VIX percentile and the 100th trailing-TP-vol
percentile (after the April 2025 tariff selloff). Four 2025-26 deals priced below
the 10th trailing-vol percentile.

**Corrected estimates** (`diagnostics_b4b6_estimates.csv`):

| estimator | b | vol-matched placebo p | lag-only placebo p |
|---|---|---|---|
| OLS | +0.0809 | **0.053** | 0.098 |
| OLS, dTP divided by trailing vol | +0.0253 (sd units) | 0.060 | 0.035 |
| WLS, weights 1/vol² | +0.0695 | 0.100 | 0.172 |
| Huber | +0.0804 | 0.039 | 0.066 |
| median regression | +0.0769 | 0.054 | 0.096 |

The sign and size hold under every correction. The vol-matched placebo gives a
**lower** p than the lag-only one for the plain estimate (0.053 vs 0.098). Its
draws are tighter (sd 0.039 vs 0.048) because placebo dates now come from the
same volatility terciles as the deals, and more deals sit in low-volatility
terciles. Against the V1 prediction (p between 0.08 and 0.20, at or above
lag-only): **wrong**.

Note the lag-only p here (0.098) differs from the headline 0.083 because the
sample is 20 days shorter and the draws use a different seed.

## B5. Stationarity

ADF and KPSS (`diagnostics_b5_stationarity.csv`):

| series | ADF p | KPSS p | verdict |
|---|---|---|---|
| TP10 level | 0.42 | 0.01 | nonstationary |
| dTP10 | < 0.001 | 0.10 | stationary |
| D, decayed stock | 0.076 | 0.01 | nonstationary |
| dD | < 0.001 | 0.10 | stationary |
| S, retired text index level | 0.001 | 0.01 | ambiguous |
| dS | < 0.001 | 0.10 | stationary |
| deal shock | < 0.001 | 0.01 | ambiguous |
| dbe, doil, dvix, auc_10y, auc_surprise | < 0.001 | 0.10 | stationary |

The deal shock reads "ambiguous" because KPSS rejects on a series that is zero
except for 16 spikes; ADF rejects a unit root firmly. It is not a level series.

**Specs that break the rule** (stationary dependent on a nonstationary or
ambiguous regressor, `diagnostics_b5_specs.csv`): every `regression.py` spec on
the level of D or S, with or without the regime interaction, for both dTP10 and
dRN10. That is 8 of the 12 specs. None of them is a headline result (the headline
is the local projection, and the daily regression headline uses dD). **Retired
from any headline use**: the D-level and S-level specs, including the "30bp test"
level arithmetic in `regression.py`.

## B6. Fat tails and influential days

h = 0 residuals: Jarque-Bera rejects (p < 1e-79), skew 0.70, kurtosis 6.3. The
ten most influential days by Cook's distance include **no deal days**, for both
targets; the top of the list is 2024-08-05 and 08-06 (the yen carry unwind) and
April 2025 (the tariff selloff) (`diagnostics_b4_b8.json`,
`diagnostics_tails.png`). Huber +0.080 and median regression +0.077 are both
within 5% of OLS (table above).

## B7. Multicollinearity

All VIFs between 1.01 and 1.27 (`diagnostics_b7_vif.csv`). No issue.

## B8. Structural stability

Chow test at 2025-01-01 on the h = 0 local projection: F 4.44, **p 0.0002**. But
the pre-2025 subsample has **2 deals**, so its shock coefficient (+0.50) rests on
two observations, one of them in the yen carry unwind week; the post-2025
coefficient is +0.068 on 14 deals. The test covers all coefficients, so it does
not say which one breaks.

Expanding-window h = 0 coefficient (`diagnostics_b8_expanding.csv`,
`diagnostics_expanding.png`): +0.38 with 4 deals, falling to +0.13 by 7, then
between +0.08 and +0.11 from deal 8 onward, ending at +0.079. The early large
values are the 2024 and April 2025 deals.
