# Plan

**Status 23 Sep.** Phases 1-3 done. Phase 2's forward-curve test was later
refuted (review F1) and replaced by the on-the-run spread and TIPS tests. Phase 5
items 5.1 and 5.3 done via H11 and the calendar note; 5.2 has no new USD deals to
add. Phase 6 is now enforced by `10_PREREGISTRATION.md` and `src/holdout.py`.
Remaining open: 4.1-4.4 (September oil and Fed decomposition), a free swap or
intraday source, and the broad-IG build.

Updated 19 September 2026, after the Fed hike, the BOJ hike and the oil shock.

The original question was "does AI debt supply explain the 2026 long end." The
answer so far is a weak yes on impact and a clear no on persistence. The problem
is that AI supply turns out to be the **smallest** of at least five candidate
drivers of the same move, and the only one tested properly. The plan below is
about closing that gap in order of what the free data can actually support.

Ordering rule: do the test that can kill the thesis fastest, first.

---

## Phase 1: the buyback mirror (H7)

**Why first.** Treasury buybacks remove long-end duration on dated, announced
days, in the same market, at daily frequency, with the sign reversed from
issuance. If the duration-absorption mechanism is real, buybacks must show a
negative coefficient of comparable magnitude per $bn. If they show zero or
positive, H1 is probably a hedging artifact and the project's headline changes.
It is the cheapest decisive test available.

Data is already verified reachable: Fiscal Data `buybacks_operations`, 223
operations, 2000-03-09 to 2026-09-17, with `maturity_bucket` and
`total_par_amt_accepted`.

- [x] 1.1 Pull and cache the buyback operations table
- [x] 1.2 Map maturity buckets to representative tenors, convert par accepted to
      10-year equivalents using the same `mod_duration` as the issuance side.
      Buckets are strings like "10Y to 20Y"; use the bucket midpoint and record
      the assumption
- [x] 1.3 Build a daily long-end buyback duration series, 2024 onward
- [x] 1.4 Add to the term premium regression next to AI supply. Report both
      coefficients in the same table
- [x] 1.5 Local projections on buyback operations, h = 0..60, same spec as the
      issuance side, so the two impulse responses are directly comparable
- [x] 1.6 Randomization test on the buyback coefficient, same 1000-draw protocol
- [ ] 1.7 Event study on the 9 September size doubling as a regime change:
      pre/post split on per-operation size

**Decision rule, written before running it.** If the buyback coefficient is
negative and its confidence interval overlaps the AI coefficient in magnitude,
the duration channel survives and H1 strengthens. If it is zero or positive,
write that up as evidence for H10 and demote H1 to a hedging-flow finding.

---

## Phase 2: the hedging-flow test (H10)

**Why second.** This decides what H1 means. ΔACM TP10 is 96% explained by five
PCs of the same curve, so the current dependent variable cannot separate "risk
compensation rose" from "dealers sold Treasuries to hedge a deal."

- [x] 2.1 Build the 5y5y forward from the GSW curve. It is further from the
      hedging point than the 10Y and less contaminated
- [x] 2.2 Re-run the announcement local projection with 5y5y as the dependent
      variable
- [ ] 2.3 Pull MOVE or build a rates-vol proxy from the curve if MOVE is not free
- [ ] 2.4 Check whether the effect survives in swap spreads. Needs a free swap
      rate source; if none, record that and move on

**Prediction.** A rate-lock hedge hits the cash 10Y and unwinds. A genuine term
premium repricing shows in the 5y5y too. If the effect is 10Y-only, it is flow.

---

## Phase 3: the Japan channel (H6)

**Why third despite being the biggest flow.** Free JGB data is monthly, so this
is ~32 observations. It is the most important hypothesis and the weakest test,
which is a bad combination to lead with. Do it after the daily-frequency work.

- [x] 3.1 Pull FRED `IRLTLT01JPM156N` (JGB 10Y, monthly) and
      `IR3TIB01JPM156N` (JPY 3m, monthly)
- [x] 3.2 Build the hedged pickup: `UST10Y − (USD 3m − JPY 3m) − JGB10Y`,
      monthly, using DGS10 and DTB3 month-end
- [ ] 3.3 Pull TIC data on Japanese Treasury holdings for the actual flow series
- [x] 3.4 Regress monthly ΔTP10 on the hedged pickup with controls. Report that
      n ≈ 32 and do not over-claim
- [x] 3.5 Compare scale directly: Japanese net selling in $bn of 10-year
      equivalents against AI issuance in the same unit, same period
- [ ] 3.6 Re-check whether daily JGB yields are reachable anywhere free. MOF's
      CSV endpoints 404; try the BOJ statistics portal and Investing-style
      mirrors before giving up

---

## Phase 4: September decomposition (H8, H9)

- [ ] 4.1 Replace the daily oil log return with a specification that can absorb a
      level shift. Cumulative oil return over the event window, or an oil shock
      dummy for 10-15 September
- [ ] 4.2 Decompose the 1-15 September 10Y move into oil, breakeven and residual
- [ ] 4.3 Refresh ACM past 2026-09-15 when the NY Fed publishes, then event-study
      the eight 2026 FOMC dates on the TP and expectations components
- [ ] 4.4 Specifically: was the 17 September ΔTP negative and larger than
      ΔExpectations? That is the credibility test

---

## Phase 5: re-test what September invalidated

- [x] 5.1 **H4 needs redoing.** The Treasury-supply null was run on a period
      where auction sizes were constant from May 2026. Re-run on the pre-May
      subsample where the variable actually moved. My "duration absorption is
      contradicted" claim is currently resting on a near-constant regressor
- [ ] 5.2 Extend the issuance sample. September deals exist (Amazon priced a GBP
      deal 2026-09-09 and there may be USD deals after the sample close). Re-pull
      EDGAR and refresh
- [x] 5.3 Mark the 2025 Q4 macro calendar unreliable. The Oct 1 to Nov 12 2025
      shutdown disrupted BLS releases, which explains the 11-not-12 CPI count and
      the irregular 2026 payroll dates my parser found

---

## Phase 6: write-up discipline

- [x] 6.1 Keep `03_FINDINGS.md` as the only place a number is stated as
      established. Everything else links to it
- [x] 6.2 Any new specification gets logged in `02_HYPOTHESES.md` with its
      falsification criterion **before** it runs, given how much unlogged
      specification search already happened
- [x] 6.3 Every claim in a deliverable carries its inference method. "NW t" alone
      is not acceptable in this project any more, given the randomization tests
      disagreed with it

---

## Standing constraints

These do not change and should stop me re-litigating them:

- **N = 7 events.** Minimum detectable effect 3.3bp at 95%. Any event-study
  result below that is unreportable regardless of point estimate.
- **Maturity-localized concession is not identifiable** on free curves. Proven,
  not assumed. Stop trying.
- **ACM is published with a lag** and is an affine function of the curve. Both
  limit what the term premium leg can say.
- **MBS is untested and untestable** on free data. It is a named component of
  the 30bp claim, so no statement about that claim can be complete.
- **Multiplicity is already bad.** 16 regression specs and 16 event-study rows
  with no correction. Every additional spec makes it worse, so new tests need
  pre-registered predictions, not exploration.
