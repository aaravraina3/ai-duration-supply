# Methods: what I chose, what I rejected, and what it cost

Every non-obvious modelling decision in this project, with the alternative I
turned down and the price I paid for the choice. Written because the results are
only as good as these, and because several of them were wrong the first time.

---

## 1. Measuring supply in 10-year equivalents, not notional

**Chosen.** For each tranche, `notional x modified_duration / duration_of_10Y_par`.

```
D_t  =  sum_j  notional_j  x  ModDur_j  /  ModDur_10Y
```

**Why.** The quantity the market must absorb is interest-rate risk, not cash. A
$5B 30-year tranche is roughly twice the duration shock of a $5B 10-year. Using
notional treats them as identical and throws away the thing being tested.

**Alternatives rejected.**
- *Raw notional.* Simpler, and it is what the press quotes. Discards the maturity
  information that the entire "localized at the tenors they issue into" question
  depends on.
- *DV01 in dollars.* Equivalent up to a scale factor, and arguably more natural
  for a trader. I used 10-year equivalents because they make the AI number
  directly comparable to Treasury coupon supply and buybacks in the same unit,
  which is how the scale comparison in `03_FINDINGS.md` D3 is built.

**Cost.** Modified duration needs a yield assumption. I used the tranche's own
coupon under a par assumption, which is right at issue and drifts afterwards.
Immaterial here because everything is measured on the announcement day.

**A decision that turned out not to matter.** Floating-rate tranches get 0.25y
duration, not their maturity, because they reset quarterly. I first wrote that
this "mattered more than expected." Then I checked: only 7 of 103 tranches are
floaters ($5.75B), and moving their duration anywhere from 0 to 2 years changes
the day-0 coefficient from +0.0813 to +0.0807. Correct in principle, immaterial
in this sample.

---

## 2. Local projections instead of a VAR

**Chosen.** Jordà-style local projections: a separate regression per horizon,

```
TP_{t+h} - TP_{t-1}  =  a_h  +  b_h * shock_t  +  theta_h' Z_t  +  e_{t+h}
```

**Why.** I wanted the *shape* of the response over time, specifically whether the
effect persists. Local projections give that directly, one coefficient per
horizon, with no restriction on the dynamics.

**Alternatives rejected.**
- *VAR with an impulse response.* More efficient if the lag structure is right,
  and catastrophically wrong if it is not, because misspecification at short lags
  propagates into every horizon of the IRF. With 680 daily observations and a
  regressor that is 16 lumpy shocks, I had no basis for choosing a lag order.
- *A single regression on a decayed stock.* I actually did this first and it
  nearly cost me the finding. A decayed stock mean-reverts, so the change in it
  sums to roughly zero over a year, and the regression reported a cumulative
  effect near zero while hiding a real impact effect. Local projections separated
  impact from persistence and showed the effect is +0.080 at h=0 and +0.011 at
  h=5.

**Cost.** Local projections are less efficient than a correctly specified VAR,
and overlapping windows make the residuals autocorrelated by construction. I set
`maxlags = h + 5` in the HAC covariance for that reason.

---

## 3. Randomization tests over Newey-West, when they disagree

**Chosen.** Report both, believe the randomization test.

**Why.** They disagreed badly. On the announcement effect, Newey-West gives
t = 3.47 and p < 0.001 (unified sample to 2026-09-22). A 2000-draw randomization
test, reassigning event dates while holding the shock sizes fixed, gives
**p = 0.078**, with a placebo standard error about 1.9x the Newey-West one.

The tell that something was wrong: **the HAC standard error was smaller than the
OLS standard error** (0.0230 against 0.0442). HAC is a correction for serial
correlation. When it shrinks your error bars, it is exploiting negative
autocorrelation in the score, and with a regressor whose Kish effective n is 9.7,
that is not a correction I trust.

**Alternatives rejected.**
- *Newey-West alone.* Standard, fast, and in this case wrong by a factor of two.
- *Block bootstrap.* Reasonable, but the events are roughly monthly and the
  windows are short, so there is no block structure to preserve. The randomization
  test targets the actual null of interest, which is "these particular dates are
  not special," and that is a sharper question.

**Cost.** Randomization tests are slow. 1000 draws over 16 shocks and a full
local projection is minutes rather than milliseconds.

---

## 4. Event dating from the FWP trade date, not the filing date

**Chosen.** Parse `Trade Date:` out of the FWP pricing term sheet, match it to
the final 424B by comparing the full set of coupon rates.

**Why.** Final 424Bs are filed one to two days *after* pricing. Using the filing
date puts the event window after the information was already in the market, which
is a look-ahead error in the direction that destroys the result rather than
manufacturing one, but an error either way.

**Alternatives rejected.**
- *Filing date of the final.* Two-day look-ahead.
- *Filing date of the preliminary.* Correct timing, but preliminaries have blank
  amounts, so the size has to come from elsewhere anyway.
- *Settlement date.* T+3. Worse.

**Cost.** The matching has to work. It did: all 16 deals matched their term sheet
on the complete coupon set, which is a strong check because a mismatch would show
up as a partial score rather than silently passing.

---

## 5. GSW zero yields for the curve work, and why that then failed

**Chosen initially.** GSW `SVENY01..SVENY30`, 30 tenor points, zero-coupon.

**Why.** The ±2y exclusion band in the concession design needs a fine tenor grid.
The FRED par grid has 8 usable tenors and a deal targeting six of them leaves
**0.86 control tenors** on average, against four parameters. GSW was the only
free curve that could support the design at all.

**What went wrong.** GSW is itself a six-parameter Svensson fit. Three principal
components span 99.2% of its daily variation, so the residual the design asks for
lives below a basis point by construction. The control-tenor fit had R² = 1.000.

**How I established that rather than assuming it.** Injected a known 5bp Gaussian
bump at each deal's tenors and measured recovery:

| Stage | Recovery |
|---|---|
| 3-factor residualization only | 77.7% |
| after re-fitting Svensson the way GSW does | **−10.7%** |

The estimator is fine. The published smoothing scrambles the sign. This made an
out-of-sample prediction that then came true: the measured concession flips from
−0.167bp to +0.123bp as the exclusion band moves.

**The general lesson, and the one I would keep.** Measure what your instrument
can see *before* trusting a null from it. The injection test took an afternoon
and it is the difference between "no localized concession exists" and "this
method cannot detect one."

---

## 6. Time-series residualization instead of cross-sectional, once §5 failed

**Chosen.** Fit the normal relation per tenor on non-event windows,

```
dy(tau)  =  alpha  +  beta * dy(2Y)  +  gamma * d(breakeven)  +  e
```

then read the event-window residual.

**Why.** A smooth curve cannot answer "is this bump local in tenor," because the
smoothing removed the locality. It *can* answer "did this sector move more than
the front end and inflation compensation imply," because that compares the same
smooth statistic across event and non-event days. Smoothing affects both equally
and differences out.

**Alternative rejected.** More PCA factors as controls. That makes it worse: more
factors span more of the curve and drive the residual further toward zero.

**Cost.** It answers a weaker question. "The long end cheapened" is not "the 10y
point specifically cheapened." I relabelled the output accordingly.

---

## 7. Separating flow from risk premium, and the first attempt that failed

**The problem.** ACM TP10 is 96% explained by five PCs of the same curve and 64%
by the 10Y alone. So dealers selling cash 10Ys to hedge a new deal move the
measured "term premium" with no change in required compensation. I needed a
test the hedge does not touch.

**First attempt, refuted.** Run the event study on forwards built from the GSW
zero curve,

```
f(n1, n2)  =  (n2 * y(n2)  -  n1 * y(n1))  /  (n2 - n1)
```

and lean on the 20y10y forward, which looked nearly orthogonal to the cash 10Y
(R² 0.06) while still carrying the effect. That was an artifact. GSW is a Svensson
fit with few bonds past 20 years, so its far forward is mostly the fit's own
parameter noise. Built from observed CMT points, the same forward has R² 0.623
with the 10Y, and the two versions correlate at 0.384. This is exactly the lesson
of §5 and I did not apply it. Forwards are now built from CMT points, and the GSW
versions are kept only to show the problem (fig12).

**Chosen instead: the on-the-run spread.**

```
otr(10)  =  CMT par yield(10)  -  GSW par yield(10)     [SVENPY10]
```

CMT is built from on-the-run securities. GSW is fit only to seasoned bonds and
explicitly excludes on-the-runs. Rate-lock hedges around new corporate deals sell
the most liquid Treasuries, which are the on-the-runs. So a hedging flow should
cheapen on-the-runs against seasoned paper and widen this spread on deal days; a
repricing of duration risk moves both together and leaves it alone. I wrote the
predictions down before running it. The spread moves +0.004 bp per $bn (t 0.77),
4% of the yield move. At 10 years the GSW fit is well constrained, unlike the far
forward, so this is the maturity where the comparison is cleanest.

**Also chosen: real yields, without the breakeven control.** A nominal-only flow
should move nominal yields more than TIPS and widen breakevens. Real yields move
0.87 times the nominal response and breakevens do not move.

**What neither test rules out.** Futures-based hedging. The 10-year note future
delivers the cheapest-to-deliver issue, usually a seasoned note that GSW also
fits, so futures selling would move both legs of the spread together.

**Alternatives rejected.**
- *Swap spreads.* The cleanest separation, since a cash hedge moves Treasuries
  against swaps. Daily history exists at BlueGamma behind an account signup, which
  I did not create.
- *Intraday Treasury prices around pricing time.* Would show whether the move is
  concentrated in the pricing window. Not free.
- *MOVE index.* Would test whether rate volatility repriced. Not free.

**Cost.** Several more tests with no multiplicity correction. Both are reported
as evidence against one alternative, not as proof of the mechanism.

---

## 8. The Japan channel: removing the mechanically shared term

**First attempt, wrong.** Regress TP10 on the FX-hedged pickup

```
pickup  =  UST10  -  (USD3m - JPY3m)  -  JGB10
```

That gave +65.7 with t = 8.2, the opposite sign to the prediction. **It is
mechanical.** `pickup` contains `UST10`, and TP10 is 64% a function of the 10Y.
I was regressing the 10Y on the 10Y. Same trap as §5 and §7, third appearance.

**Fix.** Split it into the US half and the non-US half:

```
pickup  =  UST10  -  hurdle,        hurdle  =  JGB10  +  (USD3m - JPY3m)
```

`hurdle` is the bar a hedged Treasury must clear and contains no US long yield.
Prediction written down before running: coefficient POSITIVE.

**Then handle the global confound in three layers.** Global long rates rose
together, so a naive regression loads on that whatever the true channel is.
(a) control for ACM's US expectations component; (b) add the US 2Y; (c)
orthogonalize the hurdle against US expectations and use the residual.

**Result.** +0.308 (t = 1.66) naive, +0.300 (t = 1.34) with expectations,
**−0.017 (t = −0.10)** once the 2Y is added, at which point R² jumps from 0.09 to
0.69. The US front end explains it and Japan adds nothing.

**Alternatives rejected.**
- *VAR.* 38 monthly observations and 3-4 endogenous variables burns the degrees
  of freedom on a lag structure I cannot estimate, and identification would still
  rest on an ordering I have no basis for.
- *Instrumenting with BOJ policy surprises.* The right answer. Needs intraday JGB
  futures around announcements, which is not free, and there are only a handful
  of BOJ moves in the sample.

**Cost, stated up front.** The cross-currency basis is omitted because no free
series was reachable. JPY basis is persistently negative, roughly −20 to −50bp,
so omitting it biases the pickup **upward**. Any finding that the pickup is
already negative is conservative under that bias.

**A fact the framework cannot explain.** The hedged pickup is negative in
**39 of 39 months**. On a pure CIP view Japan should have sold everything three
years ago. They did not. So either the marginal holder is unhedged and taking FX
risk, or the hedged-pickup framework is the wrong lens for this decision. That
is a limitation of the method, not a result.

---

## 9. Purged walk-forward for anything with a parameter

**Chosen.** Choose the holding period using only events strictly before the trade
being evaluated.

**Why.** The brief names leaky cross-validation as the most common silent error
in finance ML, and it is right. The 5-day holding period came from a local
projection estimated on the same events the strategy trades. Reporting the
in-sample Sharpe of 0.87 without the walk-forward would be exactly that leak.

Out-of-sample it drops to **0.55 with a 50% hit rate**.

**Cost.** Ten evaluable trades instead of sixteen, and the first six are burned
as the training minimum.

---

## 10. Inference under a tiny N, generally

Three things I now do by default in this project:

**Kish effective sample size** for lumpy regressors. The daily regression has
T = 680 but 95% of the regressor's variation sits in 16 days, giving an effective
n of **9.7**. Quoting n = 680 anywhere would be misleading.

```
n_eff  =  (sum x_i^2)^2  /  sum x_i^4
```

**Wild cluster bootstrap with the null imposed** when clustering on few groups.
17 episode clusters is well inside the range where cluster-robust standard errors
are unreliable. Gives p = 0.012 against a cluster-robust t of 3.72.

**Leave-one-out on everything.** It has caught two results that were single
observations: X = +0.86bp flips sign without Meta 2024-08-07, and the strategy
never reaches t > 2 in any of 16 LOO variants. The local projection coefficient
passed (+0.068 to +0.094, min |t| = 2.63), which is why it is the one result I
still stand behind.

---

## 11. Costs in the backtest

**Chosen.** 3.0bp of price round trip, sensitivity at 0 / 1.5 / 6.0.

**Why.** One ZN tick is 1/64 of a point, which is 1.56bp of price. Two ticks
covers bid-ask plus slippage on a liquid contract at modest size. Commission at
institutional size sits inside the tick.

**What it does not include.** Financing, which is inside the futures basis;
market impact, which is negligible at retail size and not negligible at the
capacity where this would be worth running; and the cost of being wrong about the
announcement timestamp.

**Honest note.** Costs are not what kills this strategy. At zero cost the Sharpe
is 1.01 and it is still statistically indistinguishable from zero.

---

## 12. Placebo dates matched on timing, not drawn uniformly

**Chosen.** For each real deal, compute its lag in business days since the last
FOMC decision, CPI print or payrolls release. Each placebo draw replaces every
real deal with a date at the same lag, drawn from days at least five sessions
from any real deal, and gives it the real deal's size. A stricter version also
matches the type of the last release.

**Why.** Deals are not uniform in time. Treasurers price in the quiet after a
macro print: 9 of 16 deals sit 1-3 days after a release. The term premium drifts
up after releases in this sample (+0.72 bp on release days, +0.72 bp at lag 2).
A uniform placebo cannot see that; a matched one inherits it, so any effect that
survives matching is not post-release drift.

**Result.** Matched placebo mean +0.0001 at day 0. p moves from 0.078 to 0.0825
(lag) and 0.1095 (lag and type). About half the day-2 response is reproduced by
the stricter placebo, so that part of the peak was drift.

**Cost.** Matching on lag and type leaves few candidate dates in some cells; where
a cell is empty the draw falls back to lag-only matching.

---

## 13. Checking controls for being functions of the outcome

**Chosen.** For every control, ask whether it is built from the dependent
variable, and test whether the shock moves it.

**Why.** The breakeven is nominal minus real by construction. Controlling for it
while regressing real yields makes the real and nominal coefficients identical at
day 0, which is what the first TIPS test returned (+0.0971, t 3.48 in both). That
was an identity, not a finding.

**Result.** The AI shock does not move breakevens (+0.015, t 0.82), so the
control is not absorbing the effect. Dropping it raises the day-0 TP10
coefficient to +0.095 (t 4.93). The headline keeps the control because it was
specified in advance.

---

## 14. A frozen held-out test instead of more corrections

**Chosen.** Freeze one specification in `src/holdout.py`, hash it, record the hash
in `10_PREREGISTRATION.md`, and test it only on deals announced after 2026-09-24.

**Why.** Several hundred test statistics were computed on the in-sample data. No
correction applied after the fact recovers what a search destroys, and choosing
which correction to apply is itself another degree of freedom. An untouched
sample is the only repair.

**Alternatives rejected.**
- *Bonferroni or Holm on the existing results.* Honest, but it just says nothing
  is significant, which is already known.
- *A held-out split of the existing sample.* Every choice in the project was made
  looking at all of it, so no part of it is held out in the sense that matters.

**Cost.** The test needs 32 deals for 80% power. At the 2026 pace that is about
three years. I first set the gate at 14, which has 49% power, and changed it
before any held-out data existed.
