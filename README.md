# AI Debt Supply and the Treasury Term Premium

Measures how much of the 2026 long-end selloff is attributable to AI-related
corporate duration supply, and whether the effect is localized at the tenors
hyperscalers actually issue into.

Everything here is built from free primary sources. No paid data, no API keys.

## Headline

Read the audit section below before quoting any of these. An adversarial pass
(`src/audit*.py`) materially weakened two of them.

| | |
|---|---|
| **N** | **7** jumbo USD offerings, threshold $10B, after macro and clustering filters (12 jumbos before the macro filter, 16 USD deals total) |
| **X** | **+0.82 bp** duration-weighted abnormal cheapening at target tenors, NW t = 0.93, placebo p = 0.62. **Driven entirely by one event**, see below |
| **Y** | **+81 bp**, 10Y CMT from 4.19% on 2026-01-02 to 5.00% on 2026-09-15 |
| **explained share** | **7.1%** of Y (5.8 bp), 95% CI −6.4 to +17.9 bp. Not distinguishable from zero |

The term premium leg is the informative one. AI duration supply moves the ACM
10Y term premium on announcement by **+0.080 bp per $bn of 10-year equivalents**,
worth 15.6 bp across 2026 issuance, and the effect is gone by five business days
(b = +0.011). The daily regression reports NW t = 3.42, but that overstates it:

- **Randomization test on the announcement effect: p = 0.069.** The placebo
  standard error is 1.9x the Newey-West one.
- **Plain OLS t = 1.92.** The HAC correction *shrinks* the standard error below
  OLS, which is a warning sign rather than a robustness result.
- **Kish effective n = 9.6**, not T = 673. The regressor is 16 lumpy shocks plus
  deterministic decay; 95% of its variation sits in 16 days.
- It does survive leave-one-out (b from +0.067 to +0.093, min |t| = 2.59) and a
  wild cluster bootstrap (p = 0.017).

So: a marginally significant, clearly transitory announcement effect. Not a
persistent term premium effect, and not a 30 bp one.

## What the audit broke

**The "it's all expectations" framing does not survive endpoints.** Calendar 2026
shows ΔTP = −8.6 bp against ΔExpectations = +79.0 bp. But across 25 start/end
pairs ΔTP ranges **−28.6 to +23.9 bp and is positive in 12 of 25**. Over the full
2024-2026 sample the 10Y rose 105 bp of which **+103.1 bp is term premium** and
−1.7 bp is expectations, the exact opposite. The only endpoint-robust claim is
the narrow one: within calendar-2026 windows, |ΔExp| > |ΔTP| in all 25 pairs.
Over the horizon on which the AI issuance ramp actually happened, term premium is
the whole story, which makes the supply hypothesis *more* plausible, not less.

**X is one observation.** Dropping Meta 2024-08-07 flips X from +0.82 to −0.12 bp.
That event carries an abnormal move of +8.88 bp against a −3.4 to +3.5 range for
the other six, and it sits inside the August 2024 yen-carry unwind (VIX 38.57 on
08-05, 97th percentile of the sample on the event date). Do not defend X.

**The mechanism has an internal inconsistency.** In the same regression, Treasury
coupon duration supply, roughly 10x larger, carries a coefficient of −0.0014
(t = −0.15). If duration absorption raised the term premium, the larger supplier
should dominate. It does not, and the signs differ. Separately, ΔACM TP10 is 96%
explained by five PCs of the same zero curve, so the dependent variable is close
to a fixed linear function of the long-end move it is being asked to explain.

**No reverse causality found, but the test is weak.** Logit of announcement
timing on prior 5d/20d yield changes, 60-day level percentile and VIX gives
LR p = 0.676, nothing near significance, at n = 16.

## What is in the sample

16 USD bond offerings from Amazon, Alphabet, Meta, Microsoft and Oracle between
Jan 2024 and Sep 2026, built from SEC 424B2/424B5 cover pages with announcement
dates recovered from the matching FWP pricing term sheets. Every deal matched its
term sheet on the full set of coupons.

2025 USD issuance totals $92.75B against the ~$93B the brief quoted, which is the
main external validation of the parsing. 2026 year to date is $179.5B, higher than
the ~$132B in the brief.

Excluded and why:
- Non-USD tranches (EUR, GBP, JPY): $34.8B equivalent. They supply duration to
  bund, gilt and JGB curves, not Treasuries.
- Microsoft's May 2024 424B3: an Activision debt exchange offer, not new supply.
  Microsoft issued no new public USD bonds in the window.
- Oracle and Alphabet mandatory convertible preferreds, and Oracle's ATM equity
  program: equity-linked, not duration.

## The three problems worth knowing about

**1. The pre-registered macro filter is infeasible.** The brief specifies dropping
events within 3 business days of FOMC, CPI or payrolls. That retains 1 of 12
jumbos. It is not calendar density: 37% of business days are clean under that
rule, but only 8% of jumbos survive, because treasurers tend to price just after
a macro print (8 of the 11 dropped deals land within 3 business days *after* a
release, only 3 sit purely ahead of one). A symmetric 3-day filter is close to a filter on
issuance itself. The primary rule here is window contamination, meaning a release
inside the t−1 to t+1 return window actually being measured. The full ladder
(±0, ±1, ±2, ±3 giving N = 11, 7, 6, 1) is in `output/tables/robustness_specs.csv`.

**2. The cross-sectional concession in §4.4 is not identifiable from published
curves.** `src/recovery.py` injects a known 5 bp localized bump and measures what
comes back. The 3-factor residualization alone recovers 77.7% of it, so the
estimator is fine. Re-fitting Svensson the way GSW does before publication drops
recovery to −10.7%: the smoothing does not merely attenuate a local bump, it
scrambles its sign. The FRED par grid is no escape, it leaves 0.9 control tenors
on average under a ±2y band. So the spec's X is reported (+0.077 bp, NW t = 1.72,
placebo p = 0.68) and should not be interpreted. Its sign flips with the
exclusion band, exactly as the recovery experiment predicts. Measuring a genuinely
maturity-localized concession needs security-level data, TRACE or CRSP.

The headline X above is therefore the time-series version in `src/abnormal.py`:
the abnormal move at the deal's tenors relative to what the 2Y and breakevens
imply, with the normal relation fit on 625 non-event windows. Smoothing cannot
destroy that, because the same smooth statistic is compared across event and
non-event days.

**3. N = 7 is underpowered for the effect size in question.** The placebo
distribution has sd 1.70 bp, so the minimum detectable effect is 3.3 bp at 95% and
4.7 bp for 80% power. A true concession of 1 to 3 bp, which is what the brief
anticipates, is below the noise floor. X being insignificant is a statement about
power, not about the world.

## Summary bullet

> **AI Debt Supply and the Treasury Term Premium** | Python, Nelson-Siegel-Svensson, ACM, PCA, local projections
>
> Built a 16-deal hyperscaler issuance panel from SEC 424B/FWP filings
> (announcement-dated, 100% term-sheet coupon match, validated at $92.8B 2025
> issuance against consensus) and estimated the ACM term premium response to
> announced 10-year-equivalent duration; +0.08bp per $bn on announcement
> (randomization p=0.07) decaying to zero within five days, with no persistent
> effect, against sell-side estimates of 30bp

The NLP supply-pressure index in `src/nlp.py` is deliberately not in that list.
It exists and runs, but it is TF-IDF plus truncated SVD rather than a neural
encoder, its corpus is 716 effectively distinct passages after 0.90 dedup (not
the 1,604 raw), its 40 "labels" are rule-selected rather than read individually,
and a plain decayed passage count beats it in the regression (t = +2.86 with the
right sign, versus t = −1.20 with the wrong one). Calling it an NLP index
oversells it.

## Layout

```
data/
  raw/              FRED, GSW, ACM, SEC filings, BLS and FOMC calendars
  events.csv        the 7-event final sample, version controlled
  processed/        parsed intermediates, all regenerable
src/
  config.py         every researcher degree of freedom, set once
  data_pull.py      FRED, GSW zero curve, ACM, Treasury auctions
  edgar_list.py     enumerate 424B/FWP filings per CIK
  edgar_fetch.py    download them
  events.py         cover-page tranche parser
  deals.py          collapse filings to deals, recover announcement dates
  macro_cal.py      FOMC, CPI, payrolls release dates
  eventlist.py      filters, key rate durations, 10y equivalents
  curve.py          NSS with the fixed-lambda trick, PCA, loaders
  test_curve.py     curve layer tests
  concession.py     the spec's cross-sectional concession, plus placebo
  recovery.py       how much of a real bump this estimator can see
  abnormal.py       time-series abnormal-move event study
  nlp.py            supply-pressure index
  regime.py         HMM, filtered and smoothed posteriors
  regression.py     main term premium specification
  localproj.py      persistence of the supply effect
  robustness.py     the full specification grid
  headline.py       every headline number, single source of truth
  figures.py
  audit1_lags.py    effective sample size, NW lag sweep, wild cluster bootstrap
  audit2_loo.py     event independence and leave-one-out
  audit3_endpoints.py  endpoint sensitivity of the 2026 decomposition
  audit4_placebo_reverse.py  randomization test on the LP, reverse causality
  audit5_mbs_scale.py  scale vs Treasury supply, what the MBS gap costs
  audit6_nlp_real.py   whether the text index beats a passage counter
output/
  figures/  tables/  writeup.md
```

## Running it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
cd src && for m in data_pull edgar_list edgar_fetch macro_cal nlp_fetch eventlist curve test_curve concession recovery abnormal nlp regime regression localproj robustness figures headline; do ../.venv/bin/python $m.py; done
```

Raw downloads are cached, so re-runs are cheap. `test_curve.py` must pass before
any result downstream is believed.

## Deviations from the brief

- Macro exclusion changed from ±3 business days to window contamination. Reason
  above. Original reported as a robustness row.
- Nelson-Siegel is used instead of Svensson for descriptives. On the 2024+ sample
  the Svensson lambda2 pins to the grid boundary and beta3 swings from 1.0 to
  10.9, which is the instability the brief flags. Curve choice does not touch the
  concession, which runs on GSW.
- Embeddings are TF-IDF plus truncated SVD rather than a neural encoder, since no
  model API is available here. The scoring maths is unchanged.
- Earnings call transcripts are not SEC filings and are not free. Forward capex
  language is taken from 10-K and 10-Q MD&A instead, 1,604 passages after
  boilerplate stripping.
- MBS issuance is not included as a control. SIFMA publishes monthly only and
  there is no free daily series.
- ACM is used as published. Not reimplemented.
