# AI Debt Supply and the Treasury Term Premium

Measures how much of the 2026 long-end selloff is attributable to AI-related
corporate duration supply, and whether the effect is localized at the tenors
hyperscalers actually issue into.

Everything here is built from free primary sources. No paid data, no API keys.

## Headline

| | |
|---|---|
| **N** | **7** jumbo USD offerings, threshold $10B, after macro and clustering filters (12 jumbos before the macro filter, 16 USD deals total) |
| **X** | **+0.82 bp** duration-weighted abnormal cheapening at target tenors, NW t = 0.93, placebo mean −0.02 bp (p = 0.62) |
| **Y** | **+81 bp**, 10Y CMT from 4.19% on 2026-01-02 to 5.00% on 2026-09-15 |
| **explained share** | **7.1%** of Y (5.8 bp), 95% CI −6.4 to +17.9 bp. Not distinguishable from zero |

The term premium leg is the informative one:

- 2026 change in the ACM 10Y term premium: **−8.6 bp**. It fell.
- 2026 change in expected short rates: **+79.0 bp**. That is the whole move.
- AI duration supply does move the term premium on announcement, **+0.080 bp per
  $bn of 10-year equivalents (t = 3.42)**, worth 15.6 bp across 2026 issuance.
  The effect is gone by five business days (b = +0.011, t = 0.17).

So the supply effect is real and transitory. BofA's ~30 bp claim does not survive
as a persistent term premium effect, because the 2026 term premium did not rise.

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

## Resume bullet

Using the null-result variant from the brief, since that is what the data
supports:

> **AI Debt Supply and the Treasury Term Premium** | Python, Nelson-Siegel-Svensson, ACM, PCA, HMM, NLP
>
> Measured AI debt supply impact on the Treasury long end, hand-building a
> 16-deal hyperscaler issuance panel from SEC 424B/FWP filings and regressing ACM
> term premium on announced 10-year-equivalent duration; found a +0.08bp per $bn
> announcement effect (t=3.4) that decays to zero within five days, and no
> persistent term premium effect against the +81bp 2026 10Y move, contradicting
> sell-side estimates of 30bp

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
