# AI Debt Supply and the Treasury Term Premium

**Read the paper: [AI debt and the Treasury term premium: flow or stock? (PDF)](PAPER.pdf)**

Measures whether AI-related corporate bond issuance moves the Treasury long end,
and how much of the 2026 selloff it could explain.

Everything here is built from free primary sources. No paid data, no API keys.
Canonical numbers live in [`research/03_FINDINGS.md`](research/03_FINDINGS.md);
this page summarises them. All inference is exploratory, see the last section.

## Headline

On one sample, 2024-01-03 to 2026-09-22, n = 680 trading days. The question is
the one D'Amico and King (2013) frame: is there a **flow** effect (price impact as
new supply arrives) and a **stock** effect (impact of the amount outstanding)?

- **Flow effect, small and marginal.** Announced USD duration from the five AI
  hyperscalers raises the 10Y ACM term premium by **+0.081 bp per $bn of
  10-year equivalents on the announcement day**. Primary inference, the
  timing-matched placebo: **p 0.083**. Newey-West t 3.47 and OLS t 1.84 (p 0.066)
  for comparison. Dated by final-prospectus filing instead of pricing, the effect
  disappears (−0.022).
- **Short-lived**: under the timing-matched placebo it is marginal on day 0 only
  (p 0.08, then 0.22 on day 1); under Newey-West, for comparison, it is
  significant through day 2; the point estimate is near zero by day 5 (+0.013).
- **Stable in sign, not in significance.** All 216 preregistered specifications
  are positive; none survives Romano-Wolf or Benjamini-Hochberg at 0.10
  (headline Romano-Wolf p 0.69). At 16 deals the 80%-power detectable effect is
  0.116, above the estimate.
- **Not an ACM artifact.** Kim-Wright term premium +0.038 (placebo p 0.048);
  observed yields rise with maturity, 10Y +0.097 (p 0.025) to 30Y +0.115
  (p 0.007).
- **Not shown to be localized** at the issued maturities (placebo p 0.17).
- **Stock effect: open.** Monthly changes give −0.067 (permutation p 0.71). A
  levels regression gives t 3.87 but regresses a ramp on a trending series and is
  not read as evidence. The day-5 point estimate implies about 2.4 bp persists
  from 2026 supply, with a 95% upper bound of about 41 bp, so a persistent 30 bp
  effect is not ruled out.
- Treasury buybacks and weak Treasury auctions move the term premium in the
  directions duration absorption predicts. Individually marginal.
- Whether the day-0 move is required compensation or dealer hedging is **not
  fully identified**. The move is not concentrated in on-the-run bonds, and real
  yields move 0.87 times as much as nominals.
- Text from filings does not forecast issuance better than trailing issuance,
  and supply does not improve out-of-sample term premium forecasts.

The upgrade that produced most of this is logged in
[`research/11_UPGRADE_LOG.md`](research/11_UPGRADE_LOG.md), with every test in
[`research/TEST_REGISTRY.csv`](research/TEST_REGISTRY.csv), every prediction in
[`research/11_UPGRADE_PREREG.md`](research/11_UPGRADE_PREREG.md), and every
judgment call in [`research/DECISIONS.md`](research/DECISIONS.md).

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
| M4 | Buyback dates and sizes are pre-announced | Surprise-only shock built. 12.4% of the raw series (|surprise| over accepted 10y-equivalents) was news |
| M5 | No literature | Cited below. The auction result is consistent with Lou, Yan and Zhang (2013) |
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
  advance. The auction result here is consistent with that (t 1.81 on the
  all-tenor local projection, so not a replication).

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
> (timing-matched randomization p≈0.08), marginal on day 0 only, positive in all
> 216 specifications but surviving no multiplicity correction, with the stock
> effect left open, against sell-side estimates of 30bp

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
  upgrade (Phases A to D of research/UPGRADE_PLAN):
    diagnostics.py, diagnostics_b48.py   B1-B8 assumption tests
    b3_tests.py       T1-T4, tests of the B3 claims
    cumulative.py     P1, pooled day 0-2 response
    speccurve.py      B9, 216-spec curve with Romano-Wolf and BH
    power.py          B10, minimum detectable effect
    altdv.py          C1, Kim-Wright and observed yields
    tenorlocal.py     C2, maturity localization
    stockeffect.py    C3, stock effect
    mbs.py            C4, MBS supply bound
    timing.py         C5, does deal timing depend on conditions
    expected_supply.py  D1, anticipated vs surprise supply
    oos_forecast.py   D2, out-of-sample forecasts
    paper_numbers.py, verify_numbers.py, verify_vintage.py   number and data checks
  robustness.py     specification grid
  headline.py       every headline number, single source of truth
  audit1..5_*.py    the adversarial audit
  figures*.py       all figures
  archive/          retired NLP index and HMM, see archive/README.md
research/
  00_PLAN.md ... 10_PREREGISTRATION.md
output/
  figures/  tables/
PAPER.pdf           the research paper
```

## Running it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
cd src && for m in data_pull edgar_list edgar_fetch macro_cal eventlist curve test_curve concession recovery abnormal regression localproj placebo_matched buybacks auctions hedgeflow strategy2 robustness headline diagnostics b3_tests cumulative speccurve power altdv tenorlocal stockeffect mbs timing expected_supply oos_forecast diagnostics_b48 make_pdf paper_numbers verify_numbers test_upgrade verify_vintage; do ../.venv/bin/python $m.py; done
```

Raw downloads are cached. `test_curve.py` must pass before any downstream result
is believed. `placebo_matched.py` runs 36,000 local projections and takes a while.

## Deviations from the brief

- Macro exclusion changed from ±3 business days to window contamination after
  ±3 kept 1 of 12 deals. The original is reported as a robustness row.
- Nelson-Siegel used instead of Svensson for descriptives because Svensson's
  second decay parameter pins to the grid boundary on this sample.
- The NLP index was built with TF-IDF plus SVD rather than a neural encoder and
  then retired. The upgrade's sentence-embedding version (D1) did not beat trailing
  issuance out of sample either.
- MBS issuance is not controlled for. No free daily series exists. A weekly bound
  using the Fed's MBS holdings moves the AI coefficient by 4.9%.
- Upgrade-plan deviations, each logged in `research/DECISIONS.md`: specification
  curve bands drawn from the placebo sd, not Newey-West (D-09); the C3 rule
  selected a levels regression that is reported but not read as a stock effect
  (D-17); the 30 bp claim withdrawn (D-06).
- ACM used as published, not reimplemented.

## Inference status

Every p-value in this repo is exploratory. The sample was searched over for
weeks, several hundred test statistics were computed, and about fifteen had a
prediction written before they ran. The only confirmatory claim this project can
make will come from `src/holdout.py`, frozen at hash `7afd3de6e97fcd28`, which
will not report anything until 32 deals announced after 2026-09-24 exist. At the
2026 issuance pace that is about three years.
