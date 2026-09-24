# AI Debt Supply and the Treasury Term Premium

> **Superseded.** This is the original writeup, with a first audit addendum. Several numbers below predate the adversarial review and
> the fixes of 23 September 2026. Current numbers are in
> [`research/03_FINDINGS.md`](../research/03_FINDINGS.md); the long-form writeup is
> [`POST.md`](../POST.md).


Aarav Raina, September 2026

> **Read the addendum in §10 first.** An adversarial audit run after this was
> written materially weakened two claims below. Section 6's "the term premium
> fell, so it cannot be a supply story" is endpoint-dependent and does not hold.
> Section 5's X is driven by a single event. The body is kept as written so the
> revision is visible.

---

## 1. The question

In 2026 the five large AI capex spenders issued $179.5B of USD bonds, up from
$92.8B in 2025 and near nothing before that. Over the same period the 10Y
Treasury went from 4.19% to 5.00%, crossing 5% on 15 September for the first time
since July 2007. Sell-side research attributed roughly 30 bp of the move to
corporate and MBS supply.

That attribution has a testable structure. If supply is the driver, the effect
should appear in the term premium and not in expected short rates, and it should
be concentrated at the tenors issuers actually sell into. This project tests both
claims against primary data.

## 2. Data and event construction

Everything is from free primary sources: FRED for the CMT curve and controls, the
Fed Board's Gürkaynak-Sack-Wright dataset for zero-coupon yields, the New York
Fed's ACM series for the term premium decomposition, SEC EDGAR for issuance, BLS
and the Fed for the macro release calendar, and Treasury Fiscal Data for auctions.

The event list is the part that cannot be regenerated from a formula. Filings
come in three forms and only the combination is usable. The preliminary 424B
carries the announcement with blank amounts. The FWP pricing term sheet carries
the trade date and the priced sizes. The final 424B carries the authoritative
tranche table on its cover page. Sizes are taken from the final, dates from the
FWP trade date, which resolves the look-ahead problem directly rather than by
approximation. All 16 USD deals matched their term sheet on the complete set of
coupons.

The parse validates externally: 2025 USD issuance totals $92.75B against the
~$93B figure in circulation. The 2026 figure, $179.5B, is materially higher than
the ~$132B commonly quoted, because the common figure appears to exclude the
March Amazon deal's full size or the August Alphabet deal.

Duration supply is measured in 10-year equivalents, notional times modified
duration over the duration of a 10Y par bond. Floating rate tranches are assigned
0.25y duration, not their maturity. This matters: Amazon's $37B March deal
contains $2.75B of floaters that supply almost no duration.

**Table 1. USD deals, announcement dated.**

| Issuer | Announced | Size ($B) | Tranches | 10y-equiv ($B) | Target tenors |
|---|---|---|---|---|---|
| Meta | 2024-08-07 | 10.5 | 5 | 15.3 | 5, 7, 10, 30, 40 |
| Oracle | 2024-09-25 | 6.25 | 4 | 8.3 | 5, 10, 30, 40 |
| Oracle | 2025-01-30 | 7.75 | 6 | 8.0 | 3, 7, 10, 30, 40 |
| Alphabet | 2025-04-28 | 5.0 | 4 | 7.6 | 5, 10, 30, 40 |
| Oracle | 2025-09-24 | 18.0 | 6 | 21.2 | 5, 7, 10, 20, 30, 40 |
| Meta | 2025-10-30 | 30.0 | 6 | 38.9 | 5, 7, 10, 20, 30, 40 |
| Alphabet | 2025-11-03 | 17.0 | 7 | 22.3 | 3, 5, 7, 10, 20, 30, 50 |
| Amazon | 2025-11-17 | 15.0 | 6 | 16.5 | 3, 5, 8, 10, 30, 40 |
| Oracle | 2026-02-02 | 25.0 | 8 | 25.7 | 3, 5, 7, 10, 20, 30, 40 |
| Alphabet | 2026-02-09 | 20.0 | 7 | 21.9 | 3, 5, 7, 10, 20, 30, 40 |
| Amazon | 2026-03-10 | 37.0 | 11 | 38.4 | 2, 3, 5, 7, 10, 20, 30, 40, 50 |
| Meta | 2026-04-30 | 25.0 | 6 | 31.9 | 5, 7, 10, 20, 30, 40 |
| Alphabet | 2026-05-05 | 8.5 | 4 | 10.0 | 5, 7, 10, 30 |
| Amazon | 2026-06-08 | 14.0 | 5 | 16.1 | 3, 5, 7, 10, 30 |
| Amazon | 2026-07-07 | 25.0 | 8 | 25.1 | 3, 5, 7, 10, 20, 30, 40 |
| Alphabet | 2026-08-06 | 25.0 | 10 | 25.3 | 2, 3, 5, 7, 10, 20, 30, 40 |

## 3. The exclusion rule had to change, and why that is itself a result

The design called for dropping any deal within three business days of FOMC, CPI
or payrolls. Applied literally, that leaves one event out of twelve jumbos.

The reason is not calendar density. Under a ±3 day rule, 37% of business days in
the sample are clean, so random timing would retain around four or five of twelve
deals. Only one survives. Issuers are not timing randomly: of the eleven dropped
deals, eight price within three business days *after* a macro release, in the
window treasurers regard as clean air, and only three sit exclusively in front of
one. The exclusion rule and the issuance decision are not independent, so a
symmetric ±3 day filter is close to a filter on issuance itself.

The primary rule is therefore contamination of the window actually being
measured: drop a deal if a top-tier release falls inside t−1 to t+1. That is the
narrower and more defensible version of the same concern, since a curve-wide
macro shock is in any case removed by the residualization. The ladder:

| Rule | N |
|---|---|
| ±0 bdays | 11 |
| **±1 bdays (primary)** | **7** |
| ±2 bdays | 6 |
| ±3 bdays (as specified) | 1 |

No clustering merges were triggered at the primary rule. The closest pair,
2026-02-02 and 2026-02-09, is five business days apart.

## 4. Why the cross-sectional concession cannot be measured here

The design measures concession as the out-of-sample residual at target tenors
after projecting the event-window curve change onto three PCA loading shapes fit
on non-target tenors. Run as specified on GSW, the answer is +0.077 bp with
NW t = 1.72 and a placebo p-value of 0.68.

That number should not be interpreted, and the reason is worth stating precisely
because it decides what the rest of the project can claim.

The control-tenor fit has R² = 1.000. GSW is a six-parameter Svensson curve, and
three principal components span 99.2% of its daily variation, so residuals live
at the sub-basis-point scale by construction.

`recovery.py` quantifies this by injecting a known 5 bp Gaussian bump at each
deal's tenors and measuring what the estimator returns:

| Step | Recovery |
|---|---|
| 3-factor residualization only | 77.7% |
| Svensson re-fit, then 3-factor residualization | −10.7% |

The estimator is sound. The published curve is the problem. Re-fitting Svensson,
which is what the Fed does before publishing GSW, does not merely shrink a local
bump, it redistributes it across the curve and flips the sign of the residual at
the target tenors for five of seven events.

This prediction is confirmed out of sample by the robustness grid: the spec's X
swings from −0.167 bp (band 4y, t = −2.20) to +0.123 bp (band 3y, t = +3.16) as
the exclusion band moves. A real effect does not flip sign with the control
definition. Noise does.

The FRED par grid is not a way out. With eight usable tenors and deals targeting
six of them, a ±2y band leaves 0.86 control tenors on average, and a ±0.5y band
leaves 2.7, against four parameters to fit. The design is infeasible on any free
curve. Measuring genuine maturity-localized cheapening requires security-level
data such as TRACE or CRSP.

## 5. What can be measured: the abnormal long-end move

Smooth curves can still answer whether the sector the deal issues into cheapened
by more than the front end and inflation compensation imply, provided the
residualization happens in the time series rather than across the curve.

For each tenor, the normal relation is fit on 625 non-event three-day windows:

  Δy(τ) = α + β Δy(2Y) + γ Δbreakeven + ε

At the 10Y point, β = 0.664, γ = 0.650, R² = 0.685, residual sd 4.29 bp. The
event-window residual at the deal's tenors, duration weighted, is the abnormal
move.

**X = +0.82 bp**, duration weighted across seven events, unweighted +1.14 bp,
NW t = 0.93 with L = 2, p = 0.35.

The placebo, 2,000 draws of randomized event dates holding each deal's target
tenors and duration weights fixed, centres at −0.02 bp with sd 1.70 bp, so the
estimator is unbiased. The two-sided placebo p-value for X is 0.62.

The sign is right and the magnitude is plausible. The significance is not there,
and the reason is power. With placebo sd of 1.70 bp and N = 7, the minimum
detectable effect is 3.3 bp at 95% confidence and 4.7 bp at 80% power. The effect
size the brief anticipates, single-digit and probably 1 to 3 bp, sits below the
noise floor. X being insignificant is a statement about sample size.

X is positive in twelve of fifteen specifications. It is largest in wide windows
(+4.32 bp at ±5 days) and turns negative only for the window (0, +1), at −0.73
bp with t = −2.03. That pattern is informative: the cheapening arrives on the
announcement day itself and partially retraces the following day, which is what a
concession absorbed by the market looks like.

## 6. The term premium, which is where the 30 bp claim lives

Decomposing the 2026 move with the published ACM series:

| | 2026-01-02 to 2026-09-15 |
|---|---|
| 10Y CMT (Y) | **+81.0 bp** |
| ACM 10Y zero yield | +70.5 bp |
| of which expected short rates | **+79.0 bp** |
| of which term premium | **−8.6 bp** |
| 10Y breakeven | +8.0 bp |

The term premium fell. The entire 2026 long-end selloff, and slightly more than
all of it, is in expected short rates. Whatever repriced the long end in 2026, it
repriced the path of policy, not the compensation for holding duration.

That alone makes a persistent 30 bp supply-driven term premium effect impossible
to sustain as an account of 2026. There is no term premium increase to
decompose.

Supply does move the term premium, though, and on impact it moves it a lot.
Regressing the daily change in ACM TP10 on the change in decayed AI duration
supply, with breakevens, oil, VIX and auction controls, and Newey-West at six
lags:

  γ = +0.085 bp per $bn of 10-year equivalents, t = 3.69, n = 673

Local projections settle whether that persists. Regressing the h-day cumulative
change in TP10 on the announcement-day duration shock:

| h (bdays) | b (bp per $bn) | t |
|---|---|---|
| 0 | +0.080 | 3.42 |
| 1 | +0.076 | 1.93 |
| 2 | +0.113 | 3.20 |
| 3 | +0.061 | 1.13 |
| 5 | +0.011 | 0.17 |
| 20 | −0.054 | −0.40 |
| 60 | +0.074 | 0.32 |

The effect is sharp, significant for two to three days, and gone within a week.
Robust to restricting to jumbos only.

Scaling the impact coefficient by 2026 supply of 194 $bn of 10-year equivalents
gives +15.6 bp of announcement-day term premium impact across the year, 19.3% of
Y. Scaling the h = 5 coefficient gives +2.2 bp, 2.7% of Y, with t = 0.17.

The natural reading is dealer inventory. A jumbo deal forces intermediaries to
absorb duration, they demand compensation, and the compensation decays as the
paper is distributed. That is a real and economically sensible supply effect. It
is not a mechanism that moves the level of long rates over a year.

## 7. Regimes

An HMM on the three curve factors, Gaussian emissions, best of 20 EM restarts,
states relabelled by mean level loading, does not recover the regime structure
the design anticipated. With K = 3 the states are a rally state (17% of days), a
calm baseline (74%) and a short high-volatility selloff state (9%, mean dwell 2.1
days). Breakevens co-move with yields at a correlation near 0.6 in all three
states, so the states do not separate inflation-led from supply-led episodes. No
state shows long-end-led steepening with flat breakevens; the selloff state
actually flattens 30s10s by 0.50 bp per day and has breakevens rising with
yields, which is the inflation signature.

BIC barely distinguishes K = 2 from K = 3 (−4332.1 versus −4332.5). Mean dwell
times of two to twelve days say these are volatility regimes at a daily
frequency, not macro regimes.

The regime interaction on the NLP index does produce a significant coefficient,
−1.35 with t = −3.55 in the high-volatility state, but it has the wrong sign and
the regressor is a trending level against a stationary dependent variable. In the
change specification the same coefficient is −0.36 with t = −1.25. I read the
level result as spurious and would not defend it.

## 8. What I would say about this in an interview

The honest summary is three sentences. AI duration supply produces a real,
statistically strong, and short-lived term premium impact of about 0.08 bp per
$bn of 10-year equivalents, worth roughly 16 bp across 2026 issuance on
announcement days but indistinguishable from zero after a week. The 2026 long-end
selloff cannot be a supply story through the term premium channel, because the
ACM term premium fell 8.6 bp while expected short rates rose 79 bp. The
maturity-localized concession the design set out to measure is not identifiable
from published curves at all, and I can show exactly how much signal the
published smoothing destroys.

The main things I would not claim: that X = +0.82 bp is distinguishable from
zero, that the regime interaction means anything, or that N = 7 supports
inference about effect sizes below 3 bp.

## 9. Limitations

- N = 7. Minimum detectable effect 3.3 bp at 95%. Underpowered for the question.
- The maturity-localized concession needs TRACE or CRSP. Free curves are
  pre-smoothed and cannot support it.
- Non-USD issuance is excluded. Cross-currency swapped reverse yankees do
  transmit some USD rate exposure, so the USD-only duration measure is a lower
  bound on total hedging flow.
- MBS issuance is not controlled for. No free daily series exists, and it is a
  named component of the 30 bp claim being tested.
- ACM's expectations component is model-based. A critic who thinks ACM loads
  genuine term premium variation into the risk-neutral rate would read Section 6
  differently, and I have no independent decomposition to rebut that.
- Embeddings are TF-IDF plus SVD, not a neural encoder. That attenuates the NLP
  index without biasing its sign.
- Forward capex language comes from 10-K and 10-Q MD&A, not earnings calls.
- The macro exclusion rule was changed after seeing how many events it dropped,
  though before looking at any yield outcome. The full ladder is reported.

---

## 10. Addendum: adversarial audit

Run after the body was written, to try to break it. Scripts: `src/audit1_lags.py`
through `src/audit6_nlp_real.py`. Three findings change what is defensible.

**§6 does not survive endpoint variation.** The body reports ΔTP = −8.6 bp for
calendar 2026 and concludes the selloff cannot be a supply story. Across 25
start/end pairs ΔTP ranges **−28.6 to +23.9 bp and is positive in 12 of 25**.
Over the full 2024-2026 sample the 10Y rose 105 bp of which **+103.1 bp is term
premium** and −1.7 bp is expectations, the reverse of the calendar-2026 cut. The
surviving claim is only that within calendar-2026 windows |ΔExp| > |ΔTP| in all
25 pairs. Over the horizon on which the issuance ramp happened, the term premium
is the whole move, which makes the supply hypothesis more plausible rather than
less. The §8 summary is wrong on this point.

**§5's X is one observation.** Leave-one-out over the seven events gives X from
−0.120 to +1.595 bp. Dropping Meta 2024-08-07 alone flips the sign. That event's
own abnormal move is +8.88 bp against −3.4 to +3.5 for the other six, and it
falls inside the August 2024 yen-carry unwind (VIX 38.57 on 08-05; the event date
sits at the 97th percentile of the sample). X should not be defended.

**§6's t-statistic overstates the announcement effect.** Reported NW t = 3.42.
Plain OLS gives **t = 1.92**, and the HAC correction shrinks the standard error
below OLS. A 1000-draw randomization test on the local projection gives a placebo
sd 1.9x the Newey-West one and **p = 0.069** at h = 0 (h = 2: p = 0.116;
h = 5: p = 0.918). Kish effective n of the daily regressor is **9.6**, not 673.
The effect does survive leave-one-out (b from +0.067 to +0.093, min |t| = 2.59),
dropping all three overlapping deal pairs (b = +0.090), and a wild cluster
bootstrap with the null imposed (p = 0.017).

**Two further problems for the mechanism.** Treasury coupon duration supply,
roughly 10x larger, carries −0.0014 (t = −0.15) in the identical regression where
AI supply carries +0.085. Duration absorption does not predict that. And ΔACM
TP10 is 96% explained by five PCs of the same zero curve (64% by Δ10y alone), so
the dependent variable is close to a fixed linear function of the long-end move
it is asked to explain. A hedging flow in the cash market would produce this
pattern without any change in required risk compensation.

**Reverse causality: no evidence, weak test.** Logit of announcement timing on
prior 5d and 20d yield changes, 60-day level percentile and VIX gives pseudo-R²
= 0.0157, LR p = 0.676. Mean 10Y level on issuance days 4.270% vs 4.310%
otherwise. At n = 16 this rules out very little, and it does not test the things
treasurers actually watch: credit spreads, swap spreads, blackout windows.

**Scope of the 30 bp claim actually tested.** AI 10-year-equivalent duration is
3.9% of Treasury coupon duration supply in 2025 and 9.4% in 2026. Agency MBS is
**not tested at all**; no free daily or monthly series was reachable. Nor is the
non-AI majority of IG corporate, nor private-credit and ABS data-centre
financing. If MBS supply correlates with corporate supply, the reported
coefficient absorbs it and is biased up.

**The 15.6 bp figure, precisely.** 0.0802841415 bp/$bn x 194.30120 $bn =
15.5993 bp. The coefficient is estimated on all 16 USD deals and applied to all 8
2026 USD deals, so there is no jumbo/all mismatch. It is a **sum of 8 separate
one-day impacts**, each decaying to zero within a week, not a level effect. The
eight never coexist: peak simultaneous decayed stock is 60.8 $bn, so the largest
instantaneous level effect available in 2026 is 4.9 bp.

**Specification search.** The estimator that produced X did not exist until the
specified one returned a null with control-fit R² = 1.000. Also chosen after
seeing data: USD-only filtering, GSW over the par grid, the >30y tenor cap, the
`is_prose` and per-issuer boilerplate filters, local projections, and the
recovery experiment itself. `regression.py` runs 16 specifications and the body
highlights the significant one. No multiplicity correction is applied anywhere.
