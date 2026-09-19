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

**One decision that mattered more than expected.** Floating-rate tranches get
0.25y duration, not their maturity, because they reset quarterly. Amazon's $37B
March deal has $2.75B of floaters. Treating them as 2-3 year duration would have
injected phantom duration into the largest event in the sample.

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
  propagates into every horizon of the IRF. With 673 daily observations and a
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
t = 3.42 and p < 0.001. A 1000-draw randomization test, reassigning event dates
while holding the shock sizes fixed, gives **p = 0.069**, with a placebo standard
error 1.9x the Newey-West one.

The tell that something was wrong: **the HAC standard error was smaller than the
OLS standard error** (0.0235 against 0.0443). HAC is a correction for serial
correlation. When it shrinks your error bars, it is exploiting negative
autocorrelation in the score, and with a regressor whose Kish effective n is 9.6,
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

## 7. Decomposing the curve to separate flow from risk premium

**Chosen.** Run the same event study on the 10Y spot, 5y5y, 10y10y and 20y10y
forwards, computed from the zero curve as

```
f(n1, n2)  =  (n2 * y(n2)  -  n1 * y(n1))  /  (n2 - n1)
```

**Why.** ACM TP10 is 96% explained by five PCs of the same curve and 64% by the
10Y alone. So a dealer selling cash 10Ys to hedge a deal moves the measured "term
premium" mechanically, with no change in required compensation. I needed a
dependent variable the hedge does not touch.

The 20y10y forward has an **R² of 0.103** with the cash 10Y. It is nearly
orthogonal to where a rate lock would be placed.

**Result.** The effect is *larger* in the far forwards than in cash (5y5y/spot
ratio 1.17) and present at 20y10y with t = 3.18. Buybacks reverse the sign
everywhere and bite hardest at 20y10y, the sector Treasury actually buys.

**Alternatives rejected.**
- *Swap spreads.* The cleanest separation, since a cash hedge moves Treasuries
  against swaps. No free daily swap curve found.
- *MOVE index.* Would test whether rate vol repriced. Not free.

**Cost.** 30 tests (5 dependents x 3 horizons x 2 shocks) with no multiplicity
correction. The defence is the coherence of the sign pattern, not any single
t-statistic, and I say so wherever it is cited.

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
T = 673 but 95% of the regressor's variation sits in 16 days, giving an effective
n of **9.6**. Quoting n = 673 anywhere would be misleading.

```
n_eff  =  (sum x_i^2)^2  /  sum x_i^4
```

**Wild cluster bootstrap with the null imposed** when clustering on few groups.
17 episode clusters is well inside the range where cluster-robust standard errors
are unreliable. Gives p = 0.017 against a cluster-robust t of 3.48.

**Leave-one-out on everything.** It has caught two results that were single
observations: X = +0.82bp flips sign without Meta 2024-08-07, and the strategy
never reaches t > 2 in any of 16 LOO variants. The local projection coefficient
passed (+0.067 to +0.093, min |t| = 2.59), which is why it is the one result I
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
