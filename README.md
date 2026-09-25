# AI Debt Supply and the Treasury Term Premium

**Paper:** [AI Debt and the Treasury Curve (PDF)](paper/AI-Debt-and-the-Treasury-Curve.pdf)

Measures whether AI-related corporate bond issuance moves the Treasury long end,
and how much of the 2026 selloff it could explain.

Everything here is built from free primary sources. No paid data, no API keys.
Canonical numbers live in [`research/03_FINDINGS.md`](research/03_FINDINGS.md);
this page summarises them. All inference is exploratory, see the last section.

## Headline

On one sample, 2024-01-03 to 2026-09-22, n = 680 trading days:

- Announced USD duration from the five AI hyperscalers raises the 10Y term
  premium by **+0.081 bp per $bn of 10-year equivalents on the announcement
  day**. Newey-West t 3.47, plain OLS t 1.97, randomization p 0.078, and
  **p 0.08 to 0.11 against placebo dates matched on timing after macro
  releases**. Survives leave-one-out (min t 2.63) and a wild cluster bootstrap
  (p 0.012).
- **It is gone within a week**: +0.013 at five days (t 0.19). Across 2026
  issuance that is 15.8 bp of one-day impacts and about 2.4 bp that persists.
- So it cannot be a persistent 30 bp supply effect from this slice of issuance.
- Treasury buybacks and weak Treasury auctions move the term premium in the
  directions duration absorption predicts. Individually marginal.
- Whether the day-0 move is a change in required compensation or dealer hedging
  is **not fully identified**. Two free tests cut against the simplest hedging
  story: the move is not concentrated in on-the-run bonds, and real yields move
  0.87 times as much as nominals.

## What the adversarial review broke, and what was done about it

Full review in [`research/09_ADVERSARIAL_REVIEW.md`](research/09_ADVERSARIAL_REVIEW.md),
with an author response section giving the fix and result for each item.

| Item | Problem | Result of the fix |
|---|---|---|
| F1 | The forward-curve test that "ruled out" hedging used a Svensson-fitted 20y10y forward | Refuted. On observed CMT points it has R² 0.623 with the 10Y, not 0.062. Replaced by the on-the-run spread test |
| F2 | No result survives multiplicity correction | Conceded. One frozen held-out test registered, hash `7afd3de6e97fcd28` |
| M1 | Placebos ignored that deals price just after macro releases | Timing-matched placebo run. Day-0 effect survives, p moves 0.078 to 0.08-0.11 |
| M2 | Strategy hedge ratio used future data | Expanding-window β. Real but immaterial, Sharpe unchanged |
| M3 | Main regression silently stopped at 2026-09-11 | One `SAMPLE_END`, every module reads it |
| M4 | Buyback dates and sizes are pre-announced | Surprise-only shock built. 11.5% of the raw series was news |
| M5 | No literature | Cited below. The auction result replicates Lou, Yan and Zhang (2013) |
| M8 | Auction LP used a tenor bucket chosen after the fact | All-tenor LP is primary: t 1.81, not 2.59 |

The same mistake turned up six times: a confident number that came from the
dependent variable containing the thing being regressed on it, or from a fitted
curve standing in for observed prices. Concession estimator, ACM term premium,
Japan hedged pickup, auction tail, 20y10y forward, TIPS with a breakeven control.
Each time the tell was a statistic that looked better than the honest ones next
to it.

## Which number comes from which sample

| Claim | Sample | Script |
|---|---|---|
| Event study X, concession | 7 jumbos after the macro filter | `abnormal.py`, `concession.py` |
| Announcement effect, persistence | 16 USD deals, 680 days | `localproj.py` |
| Daily regression | 16 USD deals, 680 days | `regression.py` |
| Timing-matched placebo | 16 deals, 2000 draws per placebo type | `placebo_matched.py` |
| Buybacks | 68 long-bucket operations, 18 with non-zero surprise | `buybacks.py` |
| Auctions | 220 auction days, all tenors | `auctions.py` |
| On-the-run and TIPS tests | 16 deals, 680 days (GSW to 2026-09-18) | `hedgeflow.py` |
| Strategy | 16 deals, 14 after warm-up for v3 | `strategy2.py` |
| Held-out test | deals from 2026-09-24, none yet | `holdout.py` |

## Related work

The idea that bond supply moves term premia is not new, and this project applies
it to a new supply source rather than discovering it.

- Greenwood and Vayanos (2014), *Review of Financial Studies*: Treasury supply
  and excess bond returns.
- Vayanos and Vila (2021), *Econometrica*: the preferred-habitat model, the
  theory behind maturity-localized supply effects.
- Krishnamurthy and Vissing-Jorgensen (2012), *Journal of Political Economy*:
  the aggregate demand for Treasury debt.
- Lou, Yan and Zhang (2013), *Review of Financial Studies* 26(8): Treasury prices
  fall before auctions and recover after, even though auctions are announced in
  advance. The auction result here is a replication of that.

## What is in the sample

16 USD bond offerings from Amazon, Alphabet, Meta, Microsoft and Oracle between
Jan 2024 and Sep 2026, built from SEC 424B2/424B5 cover pages with announcement
dates recovered from the matching FWP pricing term sheets. Every deal matched its
term sheet on the full set of coupons. 2025 USD issuance totals $92.75B against a
quoted ~$93B; 2026 year to date is $179.5B.

Excluded and why:
- Non-USD tranches (EUR, GBP, JPY): $34.8B equivalent, which supplies duration to
  other curves.
- Microsoft's May 2024 424B3: an Activision debt exchange, not new supply.
- Oracle and Alphabet mandatory convertible preferreds and Oracle's ATM program.

## Summary bullet

> **AI Debt Supply and the Treasury Term Premium** | Python, local projections, randomization inference, ACM, PCA
>
> Built a 16-deal hyperscaler issuance panel from SEC 424B/FWP filings
> (announcement-dated, 100% term-sheet coupon match, validated at $92.8B 2025
> issuance against consensus) and estimated the Treasury term premium response to
> announced 10-year-equivalent duration: +0.08bp per $bn on the announcement day
> (timing-matched randomization p≈0.08), gone within five days, with no
> persistent effect, against sell-side estimates of 30bp

## Layout

```
data/
  raw/              FRED, GSW, ACM, SEC filings, BLS and FOMC calendars
  events.csv        the 7-event final sample, version controlled
  processed/        parsed intermediates, all regenerable
src/
  config.py         every researcher degree of freedom, including SAMPLE_END
  data_pull.py      FRED, GSW zero and par curves, ACM, Treasury auctions
  edgar_list.py     enumerate 424B/FWP filings per CIK
  edgar_fetch.py    download them
  events.py         cover-page tranche parser
  deals.py          collapse filings to deals, recover announcement dates
  macro_cal.py      FOMC, CPI, payrolls release dates
  eventlist.py      filters, durations, 10y equivalents
  curve.py          NSS with the fixed-lambda trick, PCA, loaders
  test_curve.py     curve layer tests
  concession.py     the brief's cross-sectional concession, plus placebo
  recovery.py       how much of a real bump that estimator can see
  abnormal.py       time-series abnormal-move event study
  regression.py     daily term premium regression
  localproj.py      impulse responses
  placebo_matched.py  timing-matched randomization inference
  hedgeflow.py      flow vs premium: CMT forwards, on-the-run spread, TIPS
  buybacks.py       Treasury buybacks, raw and surprise-only
  auctions.py       Treasury auction demand
  japan.py, japan2.py   the hedged-pickup channel, rejected
  strategy.py, strategy2.py, variance.py   tradability, rejected
  signal_live.py    EDGAR scanner that prints the v3 rule's position
  holdout.py        the pre-registered held-out test
  robustness.py     specification grid
  headline.py       every headline number, single source of truth
  audit1..5_*.py    the adversarial audit
  figures*.py       all figures
  archive/          retired NLP index and HMM, see archive/README.md
research/
  00_PLAN.md ... 10_PREREGISTRATION.md
output/
  figures/  tables/
paper/              the research paper (PDF)
```

## Running it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
cd src && for m in data_pull edgar_list edgar_fetch macro_cal eventlist curve test_curve concession recovery abnormal regression localproj placebo_matched buybacks auctions hedgeflow strategy2 robustness headline; do ../.venv/bin/python $m.py; done
```

Raw downloads are cached. `test_curve.py` must pass before any downstream result
is believed. `placebo_matched.py` runs 18,000 local projections and takes a while.

## Deviations from the brief

- Macro exclusion changed from ±3 business days to window contamination after
  ±3 kept 1 of 12 deals. The original is reported as a robustness row.
- Nelson-Siegel used instead of Svensson for descriptives because Svensson's
  second decay parameter pins to the grid boundary on this sample.
- The NLP index was built with TF-IDF plus SVD rather than a neural encoder and
  then retired.
- MBS issuance is not controlled for. No free series exists.
- ACM used as published, not reimplemented.

## Inference status

Every p-value in this repo is exploratory. The sample was searched over for
weeks, several hundred test statistics were computed, and about fifteen had a
prediction written before they ran. The only confirmatory claim this project can
make will come from `src/holdout.py`, frozen at hash `7afd3de6e97fcd28`, which
will not report anything until 32 deals announced after 2026-09-24 exist. At the
2026 issuance pace that is about three years.
