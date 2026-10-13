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

Registration commit: (filled in after commit)
Result commit: (filled in after run)
