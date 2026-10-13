# Diagnostics (Phase B)

Assumption tests for the two inference targets, from `src/diagnostics.py`:

- **daily**: `dTP10` on `dD` (the decayed duration stock's daily change) and
  `regression.CTRL`, n = 680 (`regression.py`)
- **lp h**: the local projection `TP(t+h) - TP(t-1)` on the deal shock at
  h = 0..5, controls dbe, doil, dvix, auc_10y, n = 679 at h = 0 (`localproj.py`)

Tables: `output/tables/diagnostics_serial.csv`, `diagnostics_hac.csv`,
`diagnostics_bandwidths.csv`, `diagnostics_b3.csv`. Figure:
`output/figures/diagnostics_acf.png`.

Status so far: B1 to B3 done. B4 to B10 not run yet.

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
variance depends only on the residuals of those 16 days. They are unusually
quiet:

| | residual sd, 16 deal days | residual sd, other days |
|---|---|---|
| lp h=0 | 2.84 bp | 4.00 bp |
| daily | 2.80 bp | 4.00 bp |

OLS assumes every day has the average variance. A heteroskedasticity-robust SE
uses the deal days' own residuals, which are about 30% smaller, so its variance is
about half. This fits a pattern found earlier: deals price in the calm days after
macro releases, and the 16 trade windows were quieter than usual (7.8bp against
11.4bp of five-day 10Y noise, `paper_numbers.json`).

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
double the robust SEs. So comparably timed days are not as quiet as the 16 deal
days happened to be. The spread of the coefficient across real alternative dates is
the honest measure of its noise. That is why randomization is the primary
inference and every HAC number is for comparison only. The paper will say this
explicitly in the Phase E rewrite.

The daily regression on `dD` shows the same pattern (OLS t 1.97, HC0 3.58,
Newey-West 3.75 to 3.88, EWC 3.89, fixed-b 4.10).
