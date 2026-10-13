# Upgrade log

Running record for `UPGRADE_PLAN.md`: what was run, what came out, what changed.
Every changed number lists the old value, the new value, and why.

## 0. What I found before starting (2026-10-12)

Read in order: README, `03_FINDINGS`, `09_ADVERSARIAL_REVIEW` with the author
response, `10_PREREGISTRATION`, `config.py`, `headline.py` and `headline.json`,
`localproj.py`, `regression.py`, `placebo_matched.py`, `hedgeflow.py`,
`recovery.py`, `archive/README.md`.

- **Paper source.** `PAPER.pdf` is built by `src/make_pdf.py` from `POST.md` in
  the repo root. `POST.md` is deliberately gitignored: the published paper is the
  PDF, and the markdown stays local. So the source exists on disk but is not in
  version control. Number checks therefore read `PAPER.pdf` itself.
- **Already done before this plan**, in commits `14b8c8a` and `79bcc27`:
  - A1: OLS t 1.84, p 0.066 in `headline.json` (`h0_inference.ols`). The 1.97 /
    0.049 pair was the Newey-West h=1 row.
  - A3, partly: coupon shares in `headline.json` (`coupon_duration_share`) with the
    cutoff stored. `supply_share.csv` was not built yet.
  - A4: wild cluster bootstrap on the h=0 local projection is p 0.015 (2000 reps,
    Rademacher, 17 episode clusters). The old 0.012 could not be reproduced on
    this coefficient; it was the same test on the daily regression in
    `audit1_lags.py`, a different coefficient.
  - A5: `acm.csv` and the raw ACM file are committed, with SHA-256 in
    `data/VINTAGES.md` and `src/verify_vintage.py`.
  - A precursor to A12: `src/paper_numbers.py` checks 45 paper numbers.
- **Holdout.** `holdout.py` and hash `7afd3de6e97fcd28` are not touched by anything
  in this log.

## Phase A

(entries appended below as each item is done)

**A1. OLS t.** Done before this plan. `grep 1.97` now only hits an unrelated
buyback t (−1.97, `02_HYPOTHESES.md`) and the h=1 Newey-West row. README value
equals `headline.json` (`h0_inference.ols`: t 1.84, se 0.0441, p 0.066).

**A2. Persistence.** `placebo_matched.py` now runs every horizon 0 to 5 (was 0, 2,
5). h=0 rows reproduce exactly. New `headline.json` block `persistence`:

| h | point | NW p | matched placebo p |
|---|---|---|---|
| 0 | +0.081 | 0.0005 | 0.083 |
| 1 | +0.078 | 0.049 | 0.217 |
| 2 | +0.115 | 0.001 | 0.127 |
| 3 | +0.064 | 0.237 | 0.445 |
| 4 | +0.038 | 0.596 | 0.686 |
| 5 | +0.012 | 0.853 | 0.910 |

First horizon not significant: h=3 under Newey-West at 5%; h=1 under the
timing-matched placebo at 10% (h=0 itself is only significant at 10%). The
current wording "gone within three days" is the Newey-West definition. **Not
reworded yet:** switching the headline to the placebo definition changes how the
headline reads, so it waits for Aarav (plan 0.3).

**A3. Coupon shares.** `output/tables/supply_share.csv` written by `headline.py`,
cutoff read from `SAMPLE_END`: 2024 0.83%, 2025 3.94%, 2026 9.21%. Every mention
matches.

**A4. Wild cluster bootstrap.** Done before this plan; see section 0.

**A5. ACM vintage.** Done before this plan; see section 0.

**A6. The 0.87.** Confirmed it is the corrected specification:
`flow_tests.real_over_nominal_no_be_control`, real and nominal 10Y on the AI shock
with the breakeven control dropped (controls oil, VIX, coupon supply). The flawed
version, with the breakeven control, gave real = nominal exactly (+0.0971, t 3.48
in both), and that is the sixth artifact. No number changes.

**A7. Injection and PCA spanning.** Both were already in the paper (Figure 2 table
and the ACM caveat paragraph). Now also in `headline.json` under
`model_dependence`: 0.777 recovered through residualisation only, −0.107 after the
Svensson refit, R² 0.964 of daily ACM TP10 changes on five curve PCs.

**A8. Announcement timing.** New `headline.json` block `announcement_timing`.
Pricing to final-prospectus filing: 1 business day for 8 deals, 2 for 8. Dating
shocks by filing date instead of pricing date: day-0 b goes from +0.081 to −0.022
(t −0.69). The effect disappears entirely. One sentence added to the paper.

**A9. Lou, Yan and Zhang.** "Replicates" changed to "is consistent with" in the
README (twice), `02_HYPOTHESES`, `09_ADVERSARIAL_REVIEW` (twice) and the paper.
Reason: the primary all-tenor LP is t 1.81. Phase B has not run yet, so this may
be revisited.

**A10. Preferred habitat.** Paper already cites Vayanos and Vila as motivation
and never says it tests the model. No change.

**A11. Nelson-Siegel.** Added to the paper after the injection section: fitted
curves, including the repo's Nelson-Siegel fits, are descriptive only, and no
estimate of the supply effect runs on one. Stated caveat in the same paragraph:
the ACM term premium is itself built from the Fed's fitted curve, which is why the
main result is also run on the observed 10Y. Not claimed: that fitted curves
appear nowhere. The trading section's P&L uses GSW 10Y yields.

**A12. Number traceability.** `src/verify_numbers.py` reads `PAPER.pdf` and
`README.md`, finds 185 distinct numbers, and traces each to `paper_numbers.json`,
`headline.json` or a committed table. **0 untraced.** Matches go to
`output/tables/number_trace.csv`. Caveat: a value can match by coincidence (small
integers especially), so the trace table is for review, and an empty untraced
list is necessary, not sufficient. Documented constants (dates, explainer
examples, the quoted external $93B and $132B, the 5.10% press print) are listed
in `CONSTANTS` with the reason. To get to zero, yearly face issuance was added to
`headline.json` (`issuance_face_usd_bn`), and the README run-time note was
updated to 36,000 local projections.

**Numbers changed in Phase A:** none of the existing `headline.json` values
changed (verified by diff). New values only.

## Phase A follow-ups (approved 2026-10-12)

**A2, wording.** Approved and applied. One phrase everywhere, timing-matched
placebo first: marginal on day 0 only (p 0.08, then 0.22 on day 1); significant
through day 2 under Newey-West, for comparison; point estimate near zero by day 5.
Changed in the paper (Figure 3 caption, table now carries the placebo p, the
paragraph below it), README headline bullet, `03_FINDINGS` B2, `02_HYPOTHESES`,
`06_STRATEGY`, `strategy.py` docstring, `09_ADVERSARIAL_REVIEW` C2 and summary.
Old wording: "gone within three days" (Newey-West definition). **Not changed:**
the README "Summary bullet", which is a resume claim and waits for Section 7.

**A2, pooled test.** Registered as P1 in `11_UPGRADE_PREREG.md` (commit
`e469395`) before running. Average of b_0, b_1, b_2 is +0.091, matched-placebo p
0.081 (one-sided 0.065), uniform p 0.098. Same as day 0 alone. One sentence in the
paper. Note recorded there: each b_h is already cumulative, so b_2 alone is the
cumulative response to day 2 (placebo p 0.127); P1 pools the path.

**A8, expanded.** Paper paragraph now gives the lag distribution (8 deals at one
business day, 8 at two) and both estimates (+0.081, t 3.47 by pricing date;
−0.022, t −0.69 by filing date).

Checks after these edits: `paper_numbers.py` 45 of 45 match; `verify_numbers.py`
190 numbers, 0 untraced (now also reads every `output/tables/*.json`).

## Phase B

**B1 to B3 done** (`src/diagnostics.py`, write-up in `12_DIAGNOSTICS.md`). No
existing number changed.

- B1: residuals serially correlated in every target. At h = 0, lag-1
  autocorrelation is −0.14 (Ljung-Box p 0.0003). At h > 0 it is +0.30 to +0.75,
  by construction from overlapping windows.
- B2: bandwidth barely matters. h = 0 t is 3.25 at 0 lags and 3.77 at 20. The
  NW (1994) automatic selector picks 11 lags, t 3.56. Repo rule (5) gives 3.47.
- B3: **the plan's hypothesis was wrong.** HAC < OLS is not from negative
  autocorrelation. The score's autocorrelation is about zero, and Newey-West at
  lag 0 (heteroskedasticity only) already gives se 0.0250 against OLS 0.0441. The
  cause is heteroskedasticity: residual sd on the 16 deal days is 2.84bp against
  4.00bp elsewhere, and every analytical SE estimates the variance from those 16
  residuals. EWC (t 3.94) and Kiefer-Vogelsang fixed-b (t 4.06) agree with
  Newey-West; HC3 gives 3.03. The matched placebo's sd (0.0466) sits next to the
  OLS SE, which is the argument for randomization as primary.
- Still to do from B3: the paper statement that randomization is primary and HAC
  is comparison only, in the Phase E rewrite.
