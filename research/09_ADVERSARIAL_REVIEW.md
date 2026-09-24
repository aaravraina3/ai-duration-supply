# Adversarial review

23 September 2026. Reviewer posture: every claim is false until the evidence
forces acceptance. Items marked **NEW** were found in this review and were not
previously documented anywhere in the repo. Everything else is already conceded
somewhere, and is listed because conceding a problem does not fix inference.

Checks run for this review, all reproducible from `src/`:
- ACM vintage comparison (17 Sep vs 23 Sep download): no revision detected
- Forward curve rebuilt from FRED CMT points instead of GSW
- Fisher combination of the three randomization p-values
- Inspection of shock construction, estimation windows and sample boundaries

---

## Step 0. Restatement

**Central claim.** Announced AI-hyperscaler USD duration supply raises the 10Y
term premium transitorily through a duration-absorption mechanism, and the effect
is too small and short-lived to explain the 2026 long-end selloff.

**Secondary claims, with what falsifies each and what supports it**

| ID | Claim | Falsified by | Evidence | Strength |
|---|---|---|---|---|
| C1 | Maturity-localized concession is not identifiable from published curves | Recovery of an injected bump on GSW | Injection: 77.7% then −10.7% | Strong |
| C2 | Effect is transitory, gone by ~5 days | Persistent coefficient at h≥5 | LP h5 +0.011, p=0.918 | Moderate |
| C3 | Buybacks move TP the opposite way | Zero or positive buyback coefficient | −0.180, t=−1.39, rand p=0.34 | Weak |
| C4 | Effect sits in forwards orthogonal to cash 10Y, ruling out hedging flow | 20y10y correlated with 10Y on observed data | GSW R²=0.063 | **Refuted in this review** |
| C5 | Weak auction demand raises TP | Wrong-signed btc coefficient | −4.49, rand p=0.0705 | Weak |
| C6 | Three flows, three signs = coherent mechanism | Sign coherence plausible under null | none beyond C3-C5 | **Weak, see F2** |
| C7 | Japanese repatriation not supported | Hurdle coefficient survives US 2Y control | −0.017, t=−0.10 | Moderate, n=39 |
| C8 | Strategy not tradable | Walk-forward t>2 | 0/16 LOO reach t>2 | Strong |
| C9 | 2026 decomposition is endpoint-dependent | Stable sign across windows | 12/25 positive | Strong |

**Implicit assumptions the work depends on**

1. ACM TP10 measures required compensation for duration, not a fixed function of
   curve shape. Undermined: 96% explained by five curve PCs.
2. The FWP trade date is when information reaches the market.
3. 10-year equivalents correctly aggregate risk across tenors.
4. Deal timing is exogenous to yields. Tested only at n=16.
5. Five hyperscalers are the relevant "AI supply."
6. Daily closes capture a same-day effect.
7. Non-event windows are a valid counterfactual.
8. **Placebo dates drawn from all non-event days share the timing structure of
   real deals. Violated: 8 of 11 jumbos price 1-3 days after a macro release.**
   NEW, see M1.
9. A fitted curve's far forwards reflect market pricing. **Violated, see F1.**

---

## Verdict

**Would not survive review at a top venue.** The only mechanism test fails on
observed data, no inferential claim survives any multiplicity correction, the
placebo does not match the timing structure of the events it is testing, and the
closest prior literature is uncited.

---

## FATAL

### F1. The flow-versus-premium separation is a Svensson artifact. NEW

**Location.** `03_FINDINGS.md` B4; `02_HYPOTHESES.md` H10 status "LARGELY
REJECTED"; `POST.md`, section "The satisfying part", the sentence "The 20y10y
forward barely moves with the cash 10-year at all" and the table column
"R² = 0.103"; `src/hedgeflow.py` `forwards()`.

**Problem.** The 20y10y forward was computed from GSW, which is a six-parameter
Svensson fit. Beyond 20 years there are few bonds constraining that fit, so the
far forward is dominated by the λ₂ term and its parameter noise. Rebuilt from
observed FRED CMT points:

| Construction | AI h0 | Buyback h0 | R² with Δ10Y |
|---|---|---|---|
| GSW 20y10y | +0.1115 (t 3.20) | −0.6646 (t −1.96) | **0.063** |
| CMT 20y10y | +0.1326 (t 3.35) | −0.2754 (t −1.79) | **0.623** |
| GSW 10y10y | +0.1340 (t 3.72) | −0.2746 (t −1.51) | 0.539 |
| CMT 10y10y | +0.1142 (t 3.29) | −0.2440 (t −1.35) | 0.697 |

The two constructions of "20y10y" have a daily-change correlation of **0.384**.
They are barely the same series.

**Why it matters.** The entire argument that the effect is not dealer hedging
rested on the 20y10y forward being nearly orthogonal to the cash 10Y. On observed
data it is not orthogonal. So:
- H10 reverts from LARGELY REJECTED to **OPEN**. There is now no test in the
  project that separates term premium from cash-market flow.
- The "buybacks bite hardest at 20y10y" claim was inflated **2.4x** by the
  artifact (−0.665 GSW vs −0.275 CMT).
- The AI coefficient itself survives on CMT (+0.1326, t=3.35). What dies is the
  interpretation.

This is the fifth instance of the smoothing/contamination problem, and it is in
the evidence the project leans on hardest. It was also avoidable: the injection
experiment had already shown Svensson distorts local structure, and GSW was then
used for the mechanism test anyway.

Note also the GSW R² itself moved from 0.103 to 0.063 when the sample extended by
one week, which is its own sign the far-forward construction is unstable.

**Resolve.** Rerun every H10 and B4 result on CMT-built forwards. Separate flow
from premium with an instrument the hedge does not touch: swap spreads, or
intraday Treasury data in the window between deal pricing and the close.
**Cost.** CMT rerun: minutes (done here). Swap spreads: depends on finding a free
daily swap curve; possibly unavailable.

### F2. No inferential claim survives multiplicity correction, and "three for three" is weak evidence. NEW framing

**Location.** `03_FINDINGS.md` B6 ("The coherence across independent flows is
the evidence"); `08_LOG_2026-09-23.md` "three-for-three on sign"; `POST.md`
"Two flows, opposite directions, both strongest where the mechanism says they
should be."

**Problem.** Under the null of no effect, each coefficient's sign is a coin flip.

```
P(3 of 3 correct signs | null, independent)  =  0.5^3  =  0.125
```

Sign coherence alone would happen one time in eight by chance. The magnitudes
add information, so combine the three randomization p-values with Fisher's
method:

```
chi2  =  -2 * [ln(0.069) + ln(0.34) + ln(0.0705)]  =  12.81,   df = 6,   p = 0.046
```

That is p = 0.046 **before** any correction, assuming the three tests were
pre-registered and independent, and neither assumption holds cleanly: the
auction and AI tests share the dependent variable on overlapping samples, and
7-10y was selected after seeing the cross-section.

Project-wide the specification count exceeds 100 (16 regression specs, 30
hedgeflow cells, ~16 robustness rows, ~30 strategy configurations, ~10 auction
specs, ~8 Japan specs, 60 LP horizons x 2 universes x 2 dependents). Bonferroni
over even 10 tests requires p < 0.005. The best single result in the project is
p = 0.069.

**Why it matters.** Every "significant" or "supported" status in
`02_HYPOTHESES.md` is an uncorrected exploratory result. The coherence argument
was offered as the defence against exactly this problem, and it does not hold up.

**Resolve.** Reclassify all inferential claims as exploratory. Pre-register one
primary specification and test it on data the project has never touched: either
the post-23-September period as it arrives, or a pre-2024 period with other IG
issuers. **Cost.** Pre-registration is free; the held-out data is the constraint.

---

## MAJOR

### M1. The placebo does not match the timing structure of real deals. NEW

**Location.** `src/audit4_placebo_reverse.py` placebo pool; `src/concession.py`
`placebo()`; `src/abnormal.py` `placebo()`. All draw from every non-event day.

**Problem.** The project's own finding is that 8 of 11 jumbos price 1-3 business
days *after* a macro release. Post-announcement drift after macro releases is a
well-documented pattern. So real deal days are systematically "day after news"
days, while placebo days are drawn uniformly. If there is drift in the days after
CPI or FOMC, the deal days inherit it and the placebo does not.

**Why it matters.** The randomization p = 0.069, which the project treats as its
most honest inference, may be measuring post-macro drift rather than supply. The
direction of the bias is unknown without running it.

**Resolve.** Redraw placebo dates only from days 1-3 after FOMC, CPI and NFP
releases, matching the real deals' lag distribution, then recompute the
randomization p. **Cost.** Minutes. Highest information per unit of compute of
anything on this list.

### M2. The strategy's hedge ratio uses future data. NEW

**Location.** `src/strategy2.py` docstring: "the hedge ratio is 0.664 because
that is the coefficient estimated there, on NON-EVENT windows, so it never saw a
trade." Same claim in `src/signal_live.py`. Source: `src/abnormal.py`, where the
estimation sample is every non-event window across the full 2024-2026 sample.

**Problem.** A trade on 2024-08-07 uses a β estimated on windows running through
September 2026. "Never saw a trade" is true; "never saw the future" is false. The
walk-forward in `strategy2.py` re-selects the holding period from prior events
only, but never re-estimates β.

**Why it matters.** v2 and v3 backtests carry look-ahead in the hedge, and
`signal_live.py` is presented as a live tool.

**Resolve.** Re-estimate β on an expanding window at each trade date. **Cost.**
Minutes.

### M3. The main regression stops at 11 September and nobody noticed. NEW

**Location.** `src/regression.py` `dataset()`, which joins
`data/processed/regime_posteriors.csv`.

**Problem.** The regression index runs 2024-01-03 to **2026-09-11**, n=673, even
though ACM now runs to 2026-09-22 and FRED to 2026-09-23. The binding input is
the stale regime-posterior file from the original GSW run. Meanwhile
`localproj.panel()` does not join that file and runs to n=675. So the headline
regression and the headline local projection are on different samples, and the
Fed hike, the 5% crossing and the 23 September move are absent from the main
regression.

`08_LOG_2026-09-23.md` correctly says the 23 September move "is not in any
regression." It does not say that the entire 12-22 September window is also
missing.

**Resolve.** Regenerate the regime posteriors, rerun `regression.py`,
`auctions.py` and `buybacks.py` on the extended sample, and make every module
read its end date from one config value. **Cost.** Minutes.

### M4. Buyback event dates are probably not surprises. NEW, partly MISSING

**Location.** `src/buybacks.py`, which uses `operation_date` as the shock date.

**Problem.** Treasury publishes a tentative buyback schedule at each quarterly
refunding, so operation dates and maximum sizes are known in advance. The
9 September size doubling was also announced before it took effect. Only the
accepted amount is news. Corporate deals are surprises. Comparing the two as
"announcement effects" compares a scheduled event to an unscheduled one.

**MISSING.** The Fiscal Data table has `preliminary_ann_pdf` and
`final_ann_pdf` filenames but no announcement date field, and the filename
timestamp on the one inspected (`BBPA_20260917174000`) is later than the
operation start time, so it cannot be the pre-announcement. The actual lead time
per operation could not be recovered from the data.

**Resolve.** Pull the tentative schedules from the quarterly refunding statements
and rebuild the buyback shock as the *surprise* component: accepted minus
maximum announced. **Cost.** A few hours of parsing.

### M5. Closest prior work is uncited, and H11 is probably a known result.

**Location.** None of `README.md`, `POST.md`, `output/writeup.md` or
`research/` cites any literature.

**Problem.** Papers I am confident exist and that a reviewer from the rates
literature would expect:
- Greenwood and Vayanos (2014, *Review of Financial Studies*), bond supply and
  excess bond returns. The direct precedent for supply moving the term premium.
- Vayanos and Vila (2021, *Econometrica*), the preferred-habitat model. The
  theoretical basis for maturity-localized supply effects, which is exactly what
  H2 set out to measure.
- Krishnamurthy and Vissing-Jorgensen (2012, *Journal of Political Economy*), the
  aggregate demand for Treasury debt.

A paper I believe exists but would verify before citing: Lou, Yan and Zhang
(2013, *Review of Financial Studies*) on price pressure around Treasury auctions.
If it says what I recall, H11 replicates a known result rather than finding one.

**Why it matters.** Without these, novelty is unestablished and the framing
reinvents a standard mechanism.

**Resolve.** A literature section, and position the AI-issuance angle as an
application of preferred-habitat supply effects to a new supply source. **Cost.**
A day of reading.

### M6. The dependent variable cannot distinguish the hypothesis from its main alternative.

**Location.** Every regression using ACM TP10.

**Problem.** ΔACM TP10 is 96% explained by five PCs of the same zero curve and
64% by Δ10Y alone. With F1, there is no longer any test in the project that
separates a change in required compensation from a cash-market price move.

**Resolve.** Same as F1. **Cost.** As F1.

### M7. One regime, no held-out data.

**Problem.** Every specification choice, threshold, window and hedge ratio was
made on 2024-2026, and every result is reported on 2024-2026. There is no
out-of-sample period. The sample covers one hiking-cutting-hiking sequence.

**Resolve.** Freeze the primary spec and evaluate it on data arriving after
23 September, or on pre-2024 IG issuance. **Cost.** Time, or a day of EDGAR work.

### M8. The 7-10y auction result conditions on its own selection.

**Location.** `08_LOG_2026-09-23.md` "Decay" section, LP on 7-10y auctions,
t=2.59.

**Problem.** 7-10y was chosen because the cross-sectional result was strongest
there, and then a local projection was run on that subsample. The log flags this
as "descriptive." It should not appear in `03_FINDINGS.md` B5 as a finding.

**Resolve.** Report the all-tenor LP as the primary. **Cost.** Minutes.

### M9. Pre-registration was violated at the first decision.

**Location.** `src/config.py`, `MACRO_EXCL_BDAYS`.

**Problem.** Changed from ±3 to ±1 after seeing N=1. Documented honestly, but
documentation does not restore the property that a pre-registered test has.

**Resolve.** Report the ±3 result as primary where it can be computed, which it
cannot at N=1. This is a design dead end rather than something a rerun fixes.

### M10. Different claims use different samples without saying so clearly.

**Problem.** Event study N=7 jumbos after macro filter. Local projection N=16 all
USD deals. Regression N=673 days ending 11 September. Local projection panel
N=675 ending 22 September. Buyback N=67 long operations. Auction N=66 (7-10y) or
279 (all). The headline +0.080 comes from the 16-deal LP, the event study from 7
deals, and `POST.md` presents them in sequence without stating the switch.

**Resolve.** One table in the README mapping each claim to its sample.
**Cost.** An hour.

---

## MINOR

| ID | Location | Problem | Resolve |
|---|---|---|---|
| m1 | `concession.loadings()` | PCA loadings estimated on the full sample including event days | Estimate on non-event days only |
| m2 | `buybacks.BUCKET_MID` | Midpoint assumption | Already tested ±2y, stable; keep |
| m3 | `eventlist.mod_duration` | Floater duration fixed at 0.25y, sensitivity unreported | Report 0 / 0.25 / 0.5 |
| m4 | `03_FINDINGS.md` B1 | "Kish n_eff 9.6" and "16 shocks" used interchangeably | State one |
| m5 | ACM vintage | Checked one week only, no revision found; weak test of a re-estimated model | Archive each download with a date |
| m6 | `fig8_recovery.png` | Legend overlaps a bar | Move legend |
| m7 | `POST.md` opening | "closed at 5.00%" is stale, 5.104% printed 23 Sep | Update |
| m8 | `src/nlp.py` | Retired leg still in the pipeline and README layout | Move to `archive/` |
| m9 | Regime HMM | BIC cannot separate K=2 and K=3; states are volatility clocks | Already dead; remove from pipeline |

---

## Step 13. Alternative explanations, ranked by likelihood

1. **Cash-market hedging flow.** Underwriters and investors rate-lock with
   Treasuries on pricing day, and the flow unwinds as paper distributes. Fits
   the magnitude, the timing, and the five-day decay. **Now unrefuted** after F1.
   *Rule out:* swap spreads, or intraday Treasury moves in the pricing window
   versus the rest of the day.
2. **Post-macro-release drift.** Deal days are systematically 1-3 days after a
   macro print. *Rule out:* the matched placebo in M1.
3. **Small-sample noise plus specification search.** Best p ≈ 0.07 with over 100
   tests is what the garden of forking paths produces. *Rule out:* one frozen
   spec on held-out data.
4. **Curve-fitting artifacts.** Confirmed for the concession and for the 20y10y
   forward. *Rule out:* rerun everything on CMT points.
5. **A risk-on common factor.** Issuers come to market in windows where rates are
   drifting for other reasons. The reverse-causality logit is too weak at n=16 to
   exclude this. *Rule out:* condition on credit spreads and equity returns in the
   days before pricing.
6. **Single-event leverage.** Confirmed for X (Meta 2024-08-07, August 2024 carry
   unwind). The LP coefficient survived leave-one-out, so this is not the
   explanation for B1. *Rule out:* already done.

---

## Top five next experiments, by information per unit of compute

| # | Experiment | Resolves | Cost |
|---|---|---|---|
| 1 | Matched placebo: dates drawn from days 1-3 after FOMC/CPI/NFP | M1, alternative 2 | minutes |
| 2 | Refresh the regression sample to 22 September and rerun | M3 | minutes |
| 3 | Expanding-window β in the strategy | M2 | minutes |
| 4 | Buyback surprise from refunding tentative schedules | M4 | hours |
| 5 | Swap spreads or intraday data around pricing | F1, M6, alternative 1 | unknown; data-limited |

Experiment 5 is the one that decides what the project means, and it is the one
the free data may not support. Experiments 1-3 should run before anything else
gets written.

---

## Steelman

Announced USD duration supply from five AI hyperscalers is associated with a
transitory rise in long-end Treasury yields of roughly 0.08 to 0.13 bp per $bn of
10-year equivalents, present on the announcement day and gone within a week. The
coefficient survives leave-one-out, a wild cluster bootstrap and construction of
the forward curve from observed CMT points, with randomization p ≈ 0.07. Treasury
buybacks and weak auction demand show consistent signs. The effect is too small
and too short-lived to account for the 2026 long-end selloff, which is evidence
against a persistent 30 bp supply attribution for this slice of issuance. Whether
the response is a change in required compensation or cash-market hedging flow is
not identified.

---

## Kill shot

> Your only evidence that this is a term premium effect rather than dealer
> hedging was the 20y10y forward being nearly orthogonal to the cash 10Y. That
> orthogonality is a Svensson extrapolation artifact: built from observed CMT
> points the same forward has R² = 0.623 with the 10Y, and your two versions of
> "20y10y" correlate at 0.384. So what you have is a marginally significant
> cash-market price response to jumbo issuance, no mechanism, a placebo that
> ignores the fact that issuers deliberately price after macro news, and no
> result that survives multiplicity correction.

**How to answer it.** Concede the mechanism. Retitle the result as a price-
pressure finding rather than a term premium finding. Run the matched placebo; if
the coefficient survives it, the post-macro-drift explanation is gone and the
price-pressure claim is defensible. Then either find swap-spread data to test
flow against premium, or state plainly that the question is not identified with
free data.

---

## Questions that must be answered before this can be trusted

1. What is the total number of specifications run across the project, and which
   were written down before their results were seen?
2. Why was GSW used to build forwards for the mechanism test after the injection
   experiment had already shown Svensson smoothing distorts local structure?
3. Does the AI coefficient survive a placebo drawn from days 1-3 after macro
   releases?
4. What is the announcement lead time for each buyback operation, and how much of
   each operation's size was a surprise?
5. Has β been re-estimated out of sample for any backtest?
6. Why does the main regression end on 11 September, and what do the headline
   numbers become on the extended sample?
7. Which sample does each number in `POST.md` come from?
8. How does H11 relate to existing work on Treasury auction price pressure?
9. Is there any free source of daily USD swap rates or intraday Treasury prices?
   If not, is the flow-versus-premium question answerable at all with this data?

---

# Author response, 23 September 2026

Every item below was worked in `src/` on one unified sample, 2024-01-03 to
2026-09-22 (n = 680), and the canonical numbers are in `03_FINDINGS.md`.

| Item | Status | What was done | Result |
|---|---|---|---|
| F1 | **Conceded** | CMT-built forwards made primary in `hedgeflow.py`; two new free flow tests added | 20y10y is not orthogonal on observed data (R² 0.623). New on-the-run spread test: AI effect +0.004 bp/$bn (t 0.77), 4% of the yield move, so the move is not concentrated in on-the-run bonds. Real yields move 0.87x nominals and breakevens do not move. Evidence against cash on-the-run hedging; futures hedging not excluded |
| F2 | **Conceded** | Held-out test frozen in `holdout.py`, registered in `10_PREREGISTRATION.md` | Hash `7afd3de6e97fcd28`, one-sided, timing-matched inference, gate at 32 deals for 80% power. First draft used a 14-deal gate; changed to 32 before any held-out data existed after a power check showed 49% at 14 |
| M1 | **Fixed** | `placebo_matched.py`: placebo dates drawn at the same business-day lag after the last FOMC/CPI/NFP release, and separately at the same lag and release type | Post-release drift exists (+0.72 bp on release days). It does not produce the day-0 coefficient: matched placebo mean +0.0001. p goes 0.078 (uniform) to 0.0825 (lag) to 0.1095 (lag and type). About half the h = 2 response is reproduced by the lag-and-type placebo |
| M2 | **Fixed** | `strategy2.beta_asof()` re-estimates the hedge at each trade on prior windows; v3 promoted from an ad-hoc script to `trades_v3()`, which also removed a second look-ahead in its position scaling; `signal_live.py` computes β at run time | β runs 0.574 to 0.682. v2 Sharpe −1.10 either way. v3 +0.27 after costs (previously reported +0.31) |
| M3 | **Fixed** | One `SAMPLE_END` in `config.py`; hard-coded end dates removed from five modules; retired inputs left-joined so they can never truncate the core | Regression and local projections both run 2024-01-03 to 2026-09-22, n = 680. Regression coefficient +0.0872 (t 3.80) |
| M4 | **Fixed, with a caveat** | `buybacks.build_surprise()`: expected fill from prior operations in the same bucket, shock = accepted minus expected | 75% of long-bucket operations fill to the announced maximum; 11.5% of the raw series was news. Surprise shock: h = 2 −1.45 (t −2.46), 18 events. Caveat: Lou, Yan and Zhang (2013) show anticipated Treasury flows still move prices, so the raw series is not simply wrong, it measures the whole flow |
| M5 | **Fixed** | Related work added to README and `POST.md` | Lou, Yan and Zhang (2013, RFS 26(8)) verified; the auction result replicates it |
| M6 | **Partly addressed** | Same as F1 | On-the-run and TIPS evidence narrow the alternatives. Not closed without swap or intraday data |
| M7 | **Addressed by F2** | Held-out test | Nothing to report until 32 new deals |
| M8 | **Fixed** | All-tenor auction LP made primary | +4.50 (t 1.81), against +14.76 (t 2.59) for the selected 7-10y bucket |
| M9 | **Cannot be fixed** | Documented | The ±3 day rule keeps one event; there is no pre-registered estimate to fall back to |
| M10 | **Fixed** | Sample map added to README | |
| m1 | **Checked, immaterial** | PCA loadings re-estimated without event days | Loadings correlate at 0.99996; concession +0.0754 vs +0.0808 |
| m3 | **Checked, immaterial** | Floater duration 0, 0.25, 0.5, 2 years | b0 +0.0813 to +0.0807. Only 7 of 103 tranches are floaters; the post overstated how much this mattered and is corrected |
| m6 | **Fixed** | fig8 legend moved | |
| m7 | **Fixed** | `POST.md` opening updated for the 5.104% print | |
| m8, m9 | **Fixed** | NLP index and HMM moved to `src/archive/` with a README; nothing in `src/` depends on them | |
| m2, m4, m5 | Unchanged | Bucket midpoints already stable; Kish n now stated once as 9.7; ACM vintage checked once, no revision | |

## New problem found while fixing

**A sixth instance of the mechanical-contamination pattern.** The first TIPS test
returned a real-yield coefficient exactly equal to the nominal one, +0.0971 with
t 3.48 in both. That is an identity, not a result: every regression controls for
Δbreakeven, and the breakeven is nominal minus real, so at h = 0 the two
regressions are the same regression. The informative version drops the breakeven
control. Checking whether the breakeven control biases the headline: the AI shock
does not move breakevens (+0.015, t 0.82), so it is not a bad control in the
sense that matters, and removing it raises the day-0 TP10 coefficient from +0.081
to +0.095 (t 4.93). The headline keeps the pre-specified control.

## Answers to the review questions

1. **Specification count.** Several hundred reported test statistics, about
   fifteen pre-registered. Breakdown in `10_PREREGISTRATION.md`.
2. **Why GSW for the forward test.** No good reason. The injection experiment had
   already shown Svensson distorts local structure and the lesson was not applied
   to the far forward. Fixed.
3. **Timing-matched placebo.** The day-0 coefficient survives: p 0.08 to 0.11.
4. **Buyback surprise.** 11.5% of the raw series; 25% of long-bucket operations
   filled below the announced maximum.
5. **β out of sample.** Now yes, at every trade.
6. **Why 11 September.** A stale HMM posterior file; fixed.
7. **Which sample.** Table in the README.
8. **Relation to auction literature.** H11 replicates Lou, Yan and Zhang (2013).
9. **Free swap or intraday data.** Daily swap rates exist at BlueGamma behind an
   account signup, which this project did not create. No free intraday Treasury
   source was found. So flow versus premium remains partly open.

## Revised verdict

Still would not pass a top venue: the effect is marginal under the best available
inference, the sample is one regime, and the mechanism is only partly identified.
What changed is that the two most damaging alternatives now have direct tests.
Post-macro drift does not explain the day-0 effect, and the move is not an
on-the-run hedging artifact. The claim that survives is a transitory,
marginally significant price response to jumbo AI issuance that is too small and
too short-lived to be a 30 bp story.
