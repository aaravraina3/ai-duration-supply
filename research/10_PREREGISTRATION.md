# Pre-registration

Registered 23 September 2026, before any held-out data exists. Responds to review
items F2 and M7.

## Why this exists

Every inferential result in this project came from searching over
specifications on the same 2024-2026 data. Counting below, that is several
hundred reported test statistics, of which about fifteen had a prediction written
down before they ran. The best p-value in the project is 0.069, and it does not
survive any multiplicity correction. More documentation of the search does not
repair that. A test on data the project has never seen, with the specification
fixed before the data exists, does.

## The registered test

Implemented in `src/holdout.py`. The frozen parameters are hashed; if they change,
the hash changes and it is no longer this test.

**Spec hash: `7afd3de6e97fcd28`**

| | |
|---|---|
| Hypothesis | Announced USD duration supply from the five issuers raises the 10Y term premium on the announcement day |
| Held-out window | Deals announced on or after **2026-09-24** |
| Universe | USD bond deals from Amazon, Alphabet, Meta, Microsoft, Oracle, all sizes |
| Shock | 10-year-equivalent duration announced, $bn, dated by FWP trade date |
| Dependent | ACM TP10, change from t−1 to t, bp |
| Controls | Δbreakeven, oil return, ΔVIX, Treasury coupon 10y-equivalent supply |
| Sample | Trading days on or after 2026-09-24 only, so the controls are out of sample too |
| Inference | Timing-matched randomization: placebo dates at the same lag after the last FOMC/CPI/NFP release, 2000 draws |
| Test | One-sided, H1: b > 0 |
| Alpha | 0.05 |
| Minimum N | **32 deals**, for 80% power at the in-sample estimate |
| Decision | Reject if p < 0.05. Report the estimate and p either way. A failure to reject at N = 32 is reported as a failure and the sample is not extended to rescue it |

Below 32 deals the script prints the count and stops. There is nothing to look at
early, which is deliberate.

## Why 32 and not a smaller number

Using the timing-matched placebo standard deviation at n = 16 (0.0466) as the
anchor, one-sided power against the in-sample estimate of +0.081 bp per $bn:

| Held-out deals | Standard error | Power |
|---|---|---|
| 6 | 0.0761 | 0.28 |
| 14 | 0.0498 | 0.49 |
| 20 | 0.0417 | 0.62 |
| **32** | **0.0330** | **0.79** |
| 50 | 0.0264 | 0.92 |

I first set the gate at 14 and changed it after running this table. That change
was made before any held-out data existed and before the hash was recorded here,
so the registered test is the 32-deal version. At 14 the test is a coin flip and
a null would mean nothing.

This test has a known weakness it cannot fix: if the true effect is smaller than
the in-sample estimate, which is common after a specification search, power at 32
is lower than 0.79.

## How long it takes

| Year | USD deals | Pace |
|---|---|---|
| 2024 | 2 | 2.0 / yr |
| 2025 | 6 | 6.0 / yr |
| 2026 | 8 in 9 months | 10.7 / yr |

At the 2026 pace, 32 held-out deals is roughly **three years**. If issuance slows
it is longer. That is itself the strongest argument for the broad investment-grade
version below.

## Registered next: broad IG

Not built yet. Registering the shape now so it cannot be tuned later:

- Universe: every USD investment-grade deal of at least $5B, any issuer, found
  through the same EDGAR 424B/FWP pipeline
- Everything else identical to the test above, including the dependent variable,
  controls, inference and one-sided alpha
- Held-out window identical: announced on or after 2026-09-24
- The AI-hyperscaler subset is reported as a secondary split, not the primary

If this version is built, its hash gets added here before it is run on any data
after 2026-09-24.

---

## Answer to review question 1: how many specifications

Counted by module, as reported test statistics. Approximate, because some
scripts print intermediate coefficients.

| Module | Reported tests | Prediction written first? |
|---|---|---|
| `regression.py` | 12 specs, ~70 coefficients | No |
| `robustness.py` | 16 rows x 2 estimators, plus 6 | Brief's thresholds only |
| `concession.py`, `abnormal.py`, `recovery.py` | ~10 | Brief's design only |
| `localproj.py` | 61 horizons x 2 dependents x 2 universes | No |
| `audit1` to `audit5` | ~80 | No |
| `archive/audit6_nlp_real.py`, `archive/nlp.py`, `archive/regime.py` | ~20 | No |
| `buybacks.py` | ~20 | Sign, yes |
| `hedgeflow.py` v1 and v2 | ~80 | v1 5y5y, v2 on-the-run: yes |
| `japan.py`, `japan2.py` | ~13 | Sign, yes |
| `strategy.py`, `variance.py`, `strategy2.py` | ~40 | S1 criterion only |
| `auctions.py` | ~20 | Three signs, yes |
| `placebo_matched.py` | 9 | Yes |
| Checks run for the review and this fix pass | ~30 | No |

**Total: several hundred reported test statistics, of which roughly fifteen had a
written prediction before they ran.** That is the honest denominator for every
p-value in `03_FINDINGS.md`, and it is why the only confirmatory claim this
project can ever make will come from `holdout.py`.
