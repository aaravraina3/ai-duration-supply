# Hypotheses

Every hypothesis gets an ID, a falsification criterion written before the test,
the data it needs, and a status. Status values:

- **SUPPORTED** evidence consistent, survives the audit
- **WEAK** point estimate in the right direction, inference marginal
- **REJECTED** evidence against
- **NOT IDENTIFIABLE** the data cannot answer it, and I can show why
- **OPEN** not yet tested

Anything marked OPEN has no result attached to it yet. Do not cite OPEN rows.

---

## Tested

### H1. AI duration supply raises the term premium on announcement

**Test.** Regress ΔACM TP10 on announced 10-year-equivalent duration, daily, with
breakeven, oil, VIX and auction controls. Local projections for h = 0..60.

**Falsified if** the h=0 coefficient is negative, or indistinguishable from zero
under a randomization test.

**Result.** b = +0.080 bp per $bn, NW t = 3.42, but the honest inference is
weaker: OLS t = 1.92, randomization p = 0.069, Kish effective n = 9.6. Survives
leave-one-out (+0.067 to +0.093, min |t| = 2.59) and a wild cluster bootstrap
(p = 0.017).

**Status: WEAK.** Right sign, robust to sample perturbation, marginal on
inference. Do not claim significance at 5%.

---

### H2. The effect is localized at the tenors issuers actually sell into

**Test.** Residualize the event-window curve change on three PCA loading shapes
fit on non-target tenors; read the out-of-sample residual at target tenors.

**Falsified if** the residual is zero, or flips sign with the control definition.

**Result.** +0.077 bp, placebo p = 0.68, and the sign flips with the exclusion
band (−0.167 at 4y, +0.123 at 3y). An injection experiment explains why: a known
5bp bump is recovered at 77.7% by the PCA step alone, and at **−10.7%** once
GSW's Svensson re-fit is applied. The published curve scrambles local
information before it is observable. The FRED par grid leaves 0.86 control
tenors under a ±2y band, so it is not an escape.

**Status: NOT IDENTIFIABLE** from published curves. Needs TRACE or CRSP.

---

### H3. The supply effect persists in the term premium

**Test.** Local projections, h = 0 to 60 business days.

**Falsified if** the coefficient decays to zero within a month.

**Result.** h=0: +0.080 (p = 0.069). h=2: +0.113 (p = 0.116). h=5: **+0.011,
p = 0.918**. Gone within a week.

**Status: REJECTED.** The effect is transitory. This is the strongest single
finding in the project and the one that most directly contradicts a persistent
30bp supply story.

---

### H4. If duration absorption is the mechanism, Treasury coupon supply should show the same sign

**Test.** Include Treasury coupon 10-year-equivalent auction supply in the
identical regression.

**Falsified if** Treasury supply has the same sign and a larger total effect,
given it is roughly 10x the size.

**Result.** Coefficient −0.0014, t = −0.15, against +0.085 for AI supply.
Opposite sign, no significance.

**Status: was REJECTED, now DOWNGRADED TO OPEN.** See
`01_MARKET_CONTEXT_2026.md` §4. Treasury has held coupon auction sizes constant
since May 2026, so the regressor has very little variation left in the back half
of the sample. A null on a near-constant variable is not evidence about the
mechanism. This needs re-testing on the pre-May-2026 subsample where auction
sizes actually moved.

---

### H5. Issuers time deals around rate levels, so causality could run backwards

**Test.** Logit of announcement days on prior 5d and 20d yield changes, 60-day
level percentile, VIX.

**Falsified if** any predictor is significant.

**Result.** Pseudo-R² = 0.0157, LR p = 0.676, nothing near significance. Mean 10Y
on issuance days 4.270% vs 4.310% otherwise (p = 0.52).

**Status: NOT SUPPORTED, but the test is weak.** n = 16 and it does not test
credit spreads, swap spreads, or blackout windows, which are what treasurers
actually watch.

---

## Open, and worth doing next

### H6. Japanese repatriation explains more of the 2026 long end than AI supply

**Motivation.** JGB 10Y near 2.95% and 30Y above 4%, both multi-decade highs.
BOJ at 1.25%. Japanese investors hold ~$1T of Treasuries and sold $29.6B in
Q1 2026. That flow is an order of magnitude larger than AI issuance.

**Mechanism.** A Japanese institution comparing a currency-hedged Treasury
against a domestic JGB looks at

```
hedged pickup  =  UST 10Y  −  hedging cost  −  JGB 10Y
hedging cost  ≈  USD short rate  −  JPY short rate     (covered interest parity)
```

When that pickup goes negative, the marginal Japanese buyer of US duration
disappears and the term premium should rise.

**Test.** Build the hedged pickup series. Regress the level and change of ACM
TP10 on it, with the usual controls. Cross-check against TIC data on actual
Japanese holdings.

**Falsified if** the hedged pickup carries no sign or the wrong sign once the
Fed path is controlled for.

**Known constraint before starting.** Free JGB data is **monthly** (FRED
`IRLTLT01JPM156N`, last 2026-08). MOF's daily CSV is not reachable. So this is
roughly 32 monthly observations for 2024-2026. Thin. Plan the inference for that
up front rather than discovering it later.

**Result (19 Sep).** The naive pickup regression gives +65.7 (t = 8.2), the
OPPOSITE of the prediction, and it is mechanical: `pickup` contains UST10 and
TP10 is 64% a function of the 10Y. Decomposed into the non-US half,
`hurdle = JGB10 + (USD3m - JPY3m)`:

| Spec | coef | t | R² |
|---|---|---|---|
| dTP10 ~ d_hurdle | +0.308 | 1.66 | 0.091 |
| + US expectations | +0.300 | 1.34 | 0.091 |
| + US expectations + 2Y | **-0.017** | **-0.10** | 0.691 |
| orthogonalised hurdle | +0.300 | 1.33 | 0.069 |

Adding the US 2Y takes R² from 0.09 to 0.69 and the hurdle coefficient to zero.
The US front end explains the term premium moves; Japan adds nothing.

The hurdle also **fell 31bp** over the sample (557 to 526), because collapsing
hedge cost (517 to 232bp) more than offset rising JGB yields (40 to 294bp). Even
at face value the implied contribution is -9bp against a realised +152bp move.

**Status: NOT SUPPORTED.** The popular repatriation narrative does not survive a
control for the US front end. Caveat: n=39 monthly, cross-currency basis omitted,
and the hedged pickup is negative in 39 of 39 months while Japan kept holding
$1T, so the CIP framework may be the wrong lens rather than the finding being
right.

---

### H7. Treasury's long-end buyback expansion partially offsets AI supply

**Motivation.** Treasury doubled 10Y-30Y buybacks to at least $4B per operation
effective 9 September 2026, six days before the 5% crossing. This removes long
duration on dated, observable days.

**Test.** Build a daily long-end buyback duration series from Fiscal Data
(`buybacks_operations`, 223 operations back to 2000, with maturity buckets and
par accepted). Put it in the term premium regression alongside AI supply. Also
run it as its own event study, since operations are announced and dated exactly
like deals.

**Prediction if the duration channel is real.** Buyback coefficient should be
**negative** (duration removal lowers term premium) and of comparable magnitude
per $bn to the AI coefficient. If AI supply is +0.080 per $bn and buybacks are
0 or positive, the duration story is in trouble regardless of H4.

**This is the cleanest available test of the mechanism**, because it uses the
same asset, the same market, and the same daily frequency, with the sign
reversed. Do this before H6.

**Result (19 Sep).** Treasury removed 173.7 $bn of long-bucket 10-year-equivalent
duration since 2024, against 317.4 $bn added by AI issuance. Buyback coefficient
**−0.180 bp per $bn** at h=0 (t = −1.39), negative at every horizon to h=10,
stable to the bucket-midpoint assumption (−0.19 to −0.17 for ±2y). Both channels
coexist with correct signs: issuance +0.0835 (t = +3.62), buybacks −0.168
(t = −1.30). Randomization p = 0.34.

Against the pre-registered decision rule: the coefficient is negative and its
confidence interval on magnitude, [0, 0.43], contains the AI coefficient of
0.080. **The duration channel survives.**

**Status: SUPPORTED ON SIGN, not on significance.** The buyback coefficient alone
does not clear 5%. Its value is that it is the mirror the mechanism predicts, and
it gets much stronger when split by curve segment (see H10).

---

### H8. The September 2026 oil shock, not supply, drove the 5% crossing

**Motivation.** WTI +13.6% between 8 and 15 September on three simultaneous
Middle East supply disruptions. The 10Y crossed 5% on 15 September.

**Test.** Decompose the 1-15 September move into oil-explained, breakeven-
explained and residual components. Check whether the residual is large enough to
leave room for a supply story.

**Falsified if** the oil and breakeven components explain little of the September
move.

**Note.** The current oil control is a daily log return, which cannot absorb a
level shift of this size. That is a specification weakness, not just a missing
control.

**Status: OPEN.**

---

### H9. The Fed's 16 September hike compressed the term premium

**Motivation.** 10Y fell 5.01 to 4.94 and breakevens fell 5bp the day after a
25bp hike. That is a credibility response, and it is a term premium event rather
than an expectations event.

**Test.** Event study on the eight 2026 FOMC dates using the ACM decomposition.
Compare the TP and expectations components on hike days.

**Prediction.** If credible tightening compresses the term premium, the 17
September ΔTP should be negative and larger in magnitude than the ΔExpectations.

**Status: OPEN.** Requires ACM refresh past 2026-09-15.

---

### H10. The AI announcement effect is dealer hedging flow, not risk compensation

**Motivation.** This is the strongest counterargument to H1. ΔACM TP10 is 96%
explained by five PCs of the same zero curve and 64% by Δ10y alone, so the
dependent variable is close to a fixed function of the long-end move it is being
asked to explain. Underwriters hedging a jumbo with Treasuries produce exactly
the observed pattern, including the decay.

**Test that would separate them.** A genuine risk-compensation change should show
up in instruments the hedging flow does not touch: swap spreads, the 5y5y
forward, or MOVE. A pure rate-lock hedge shows up in cash Treasuries and unwinds.
Check whether the announcement effect appears in the 5y5y forward, which is less
contaminated by the hedge.

**Pre-registered predictions.** Flow story: effect in the 10Y spot, little at
5y5y. Premium story: effect present at 5y5y, same sign.

**Result (19 Sep).** The effect is *larger* in the far forwards than in cash.
Ratio of the 5y5y response to the 10Y spot response is **+1.17**.

| Dependent | AI h=0 | t | R² with Δ10Y |
|---|---|---|---|
| 10Y spot | +0.0950 | 3.21 | 1.000 |
| 5y5y | +0.1108 | 3.66 | 0.901 |
| 10y10y | +0.1339 | 3.72 | 0.528 |
| 20y10y | +0.1111 | 3.18 | **0.103** |

The 20y10y forward is nearly orthogonal to the cash 10Y (R² = 0.103), which is
where a rate lock would be placed, and the effect is present there at t = 3.18.
Buybacks reverse the sign across every segment and are strongest at 20y10y
(−0.668, t = −1.97 at h=0; −1.028, t = −2.81 at h=2), which is the sector
Treasury actually buys.

**Status: LARGELY REJECTED.** The pure hedging-flow explanation does not fit a
response that is bigger in far forwards than in cash and that reverses under
duration removal in the matching sector. Caveat: this is 30 tests with no
multiplicity correction, so the defence is the coherence of the pattern rather
than any single cell. A residual flow component is not excluded, only the claim
that flow explains all of it.

---

## Dead

### D1. HMM regimes separate supply-driven from inflation-driven episodes

Three states on 673 days of curve factors give a rally state, a calm state and a
two-day volatility state. Breakevens co-move with yields at ~0.6 in **all three**,
so no state is distinguishable as supply-led. BIC cannot separate K=2 from K=3
(−4332.1 vs −4332.5). Mean dwell 2 to 12 days, which is a volatility clock, not a
macro regime.

### D2. An NLP index of capex language leads issuance

TF-IDF into truncated SVD, scored against a labelled direction, decayed into a
daily series. Corpus is 716 effectively distinct passages after 0.90 dedup, from
68 filings; 82% of the raw corpus has a near-duplicate. Produced a wrong-signed
coefficient (t = −1.20) and was **beaten by a plain decayed passage count**
(t = +2.86). Retired.


---

## Strategy

### S1. The announcement effect is monetisable

**Trade.** Buy duration at the close of announcement day, exit at t+5, modelled
as a 10Y note with 3bp round-trip cost.

**Falsified if** the walk-forward Sharpe is indistinguishable from zero, or the
result depends on a small number of trades.

**Result.** In-sample Sharpe 0.87, t = 1.24, bootstrap 95% CI [-0.50, +2.55].
Walk-forward Sharpe 0.55, hit rate 50%. **0 of 16 leave-one-out variants reach
t > 2.** Top 3 trades are 102% of total P&L. Holding-period Sharpe oscillates
from -0.88 (2d) to +0.87 (5d) with no monotonic structure, which is selection
rather than decay. At zero cost it is still not significant.

**Status: REJECTED.** Full writeup in `06_STRATEGY.md`.
