# Decisions

Every judgment call the plan did not specify. Entries where I would have stopped
to ask are marked **NEEDS REVIEW** at the top. "Reversible" means how hard it is to
undo.

---

## Retroactive, made before the run-to-the-end instruction (2026-10-12)

**D-01. HC2 and HC3 added in B3.** Plan B3 asked for EWC and Kiefer-Vogelsang
fixed-b. I also computed HC0, HC2 and HC3 because the B3 diagnosis pointed at
leverage on 16 days. Alternatives: leave them out. Why: they test the specific
explanation found (few high-leverage days). This is a technique not in the plan;
logged in SCOPE.md too. Reversible: easy, three table columns.

**D-02. Kiefer-Vogelsang critical values simulated, not from the published
polynomial.** Simulated 5000 draws of the fixed-b null at the sample's T and M.
Alternative: the KV (2005) cubic approximation. Why: gives a p-value, not only a
5% cutoff, and avoids transcribing coefficients from memory. Reversible: easy.

**D-03. Bandwidths for EWC and fixed-b set to the LLSW (2018) rules,
B = 0.4 T^(2/3) and M = 1.3 T^(1/2).** The plan named the methods, not the
bandwidths. Reversible: easy.

**D-04. "Deal days" in diagnostics = the 16 largest values of the regressor.**
For the daily `dD` target, dD is nonzero almost every day, so "nonzero" was wrong
(that was a bug, fixed). Reversible: easy.

**D-05. T1 primary residuals from the controls-only model.** Explained in the
preregistration: the full model mechanically shrinks deal-day residuals.
Reversible: easy.

---

## Run-to-the-end decisions (2026-10-13 onward)

**NEEDS REVIEW. D-06. The "cannot be a persistent 30bp" claim is withdrawn.**
Traced to the local projections (day-5 b × 2026 supply = 2.4bp), not to a
retired level spec. Under the primary inference (timing-matched placebo, sd 0.101
at h = 5) the 95% upper bound on what persists from 2026 supply is about 41bp;
under Newey-West about 28bp. So this sample does not rule out a persistent 30bp
effect. Chosen: remove "rules out" wording from the paper and README; report the
point estimate and both bounds; leave the stock question to C3. Alternatives: keep
the claim on the Newey-West bound (rejected: Newey-West is comparison only), or
keep the point-estimate claim without a bound (rejected: overclaims). This changes
a main conclusion. Reversible: easy (wording).

**D-07. T4 window correction uses Holm.** Decision 1 asked for "the multiple-
window correction". Chosen: Holm across the three windows, Bonferroni reported
alongside. Holm is uniformly at least as powerful as Bonferroni with the same
guarantee. Reversible: easy.

**D-08. Interview guide synced beyond the two requested edits.** Asked: remove the
"quieter days" line and add T1 to T4. Also changed, because the guide would
otherwise contradict the repo: persistence wording (approved A2 phrase), the
withdrawn 30bp claim (D-06), the Newey-West explanation (B3 showed it is not
autocorrelation), "replicates" to "is consistent with" (A9), and 8 of 11 to the
all-16 result. A final sync happens at the end of the run. The guide is a local
file outside the repo. Reversible: easy.

**NEEDS REVIEW. D-09. Spec-curve bands deviate from the registration.** F1 said
bands would use Newey-West with the h + 5 rule. A Newey-West band is not defined
for the pooled-horizon statistic, and Newey-West is comparison-only. Chosen: draw
every band as ±1.96 placebo sd, the same quantity the p-values come from.
Alternative: Newey-West for h = 0 specs and placebo for pooled specs (mixed units
in one figure). This is a deviation from a preregistered display choice; the
estimates and p-values follow the registration exactly. Reversible: easy.

**D-10. One F1 dimension turned out degenerate.** No deal priced on a release day,
so "drop release-day deals" equals "none" for every spec (72 duplicate specs).
Kept, as registered. Effect: Romano-Wolf is unaffected by duplicates; BH counts
m = 216 instead of 144, which makes BH slightly more conservative. Reversible:
easy (drop the level).

**D-11. Headline raw placebo p differs across scripts (0.0705 vs 0.0825).** Both
are the matched-on-lag placebo with 2000 draws and the same seed, but
`placebo_matched.run` draws the uniform placebo first, so its matched draws come
from a different part of the random stream. The gap (0.012) is larger than one
Monte Carlo standard error (about 0.006). Chosen: the headline keeps 0.083 from
the registered `placebo_matched.py`; the spec curve reports its own 0.0705. Not
increasing draws to shrink the gap, since choosing the draw count after seeing
p-values would be tuning. Logged in DEBT.md. Reversible: easy.

**D-12. The test registry counts the B9 family as one row.** 216 rows would make
the registry unreadable; the per-spec results are in
`output/tables/speccurve.csv`, which the row points to. Reversible: easy.

**D-13. B10 uses one-sided 5%, anchored on the matched-placebo sd at 16 deals,
scaled by sqrt(16/n).** Same convention as the holdout power table, so the two
agree (power 0.79 at 32). Alternative: two-sided, which would raise every MDE by
about 12%. Not a hypothesis test, so no registry row. Reversible: easy.

**D-14. New FRED series go to `fred_extra.csv`, not `fred.csv`.** Keeps the
committed vintage of `fred.csv` unchanged. The new files run past `SAMPLE_END`
and the holdout start (2026-09-24); every use cuts at `SAMPLE_END`. The holdout
does not read these series. Reversible: easy.

**D-15. Choices inside the C and D specs the plan left open** (all registered
before running): C2 key-rate allocation by linear weights between neighbouring
CMT tenors; C3 monthly frequency and Johansen with one lag; C4 Wednesday weeks
and a 4-lag Newey-West; C5 logit with Baa minus 10Y as the credit spread (the
plan said "credit spreads", no series named; BAA10Y has the longest free daily
history); D1 deduplication on the sentence embeddings, keeping the earliest copy
so information is dated when it first appeared; D1 capex feature by regex; D2
feature set and 250-day warm-up. Reversible: easy for each, but each change after
seeing results would be tuning.

**D-16. sentence-transformers added as a dependency** for D1, as the plan named.
Model download about 420MB. Reversible: easy.

**NEEDS REVIEW. D-17. C3 stock effect: the registered rule selected the levels
regression, and that result looks like a trend artifact.** Engle-Granger p 0.043
says cointegrated; Johansen trace (5.10 against a 95% cutoff of 15.49) says not.
The registration said "levels if either finds cointegration", so levels ran: +0.21
bp per $bn of outstanding stock, Newey-West t 3.87, R² 0.41 on 33 months. But the
stock is a near-deterministic ramp, the TP10 level is not clearly I(1) (ADF
p 0.013, KPSS p 0.01), and the term premium rose over the sample, so a levels fit
mostly measures two series both trending up. I added the Newey-West t (not in the
registration) so the estimate is not reported bare. Chosen for the paper: report
both, present the changes estimate (−0.067, permutation p 0.71, MDE 0.50) as the
conservative reading, and state that the levels result is not evidence of a stock
effect. Alternatives: report levels as the stock answer (rejected: this is the
"number that looks too good" pattern the paper's six artifacts are about), or
report only changes (rejected: hides a registered result). Prediction "no
cointegration" was wrong under the either-test rule. Reversible: easy (wording).

**D-18. D1 warm-up fallback.** For a deal whose latest filing has no
out-of-sample forecast (filing inside the 12-filing warm-up), expected supply was
set to the naive rate, trailing 365-day issuance × 90/365. In the run it was never
triggered (every deal's filing had a forecast). Reversible: easy.

**D-19. D1 filings whose 90-day target window runs past `SAMPLE_END` (10 of 97)
are excluded from training and scoring but still produce forecasts.** Otherwise
their targets would be truncated, which biases them toward zero. Reversible: easy.

**D-20. D2 ladder stopped at rung 2.** Rule 5.0 says climb to rung 4 only if
residuals show a pattern against an input or regime. Two checks were run:
volatility on the squared rung-2 error (t 2.14 at h = 1, 1.77 at h = 3) and
volatility on the error itself (t −0.90, −0.61). The first is a pattern in the
error variance, which a better mean model cannot fix; the second, the one that
bears on the forecast, is flat. Rung 3 needs correlated inputs or many features;
VIFs are about 1 and there are 7 features. So neither condition is met. The
mean-error check was added after seeing the first check; it is a diagnosis step
the plan requires, not a model choice. Reversible: easy.

**D-21. C5 power simulation details** (not specified by the plan): effect placed
on the 10s2s slope, odds ratio 2 per sd, event probabilities rescaled to average
16 events, 200 permutations per simulated sample. Reversible: easy.
