# Why the numbers jump around

Four layers, smallest to largest. The fourth is the real answer.

---

## 1. The position is an unhedged rates bet

v1 buys a 10Y and holds it five days. That position's risk has almost nothing to
do with the bond deal.

| | |
|---|---|
| 10Y daily yield sd, 2024-2026 | 5.32 bp |
| 5-day yield sd | 11.36 bp |
| times modified duration 8.0 | **91 bp of price** |
| observed strategy P&L sd | **62 bp** |

The strategy's volatility is the 10Y's volatility. For five days you own whatever
CPI, the Fed, oil and Tokyo do. The deal is incidental.

---

## 2. The signal is a quarter the size of the noise

| | |
|---|---|
| Expected effect, mean-size deal | **2.56 bp** of yield |
| 5-day noise in the 10Y | **11.36 bp** of yield |
| Signal-to-noise | **0.22** |
| Trades needed for t = 2 | **~80** |
| Trades available | **16** |

That single ratio explains the whole thing. You are trying to read a 2.5bp effect
through 11bp of static. With 16 samples you cannot.

---

## 3. Deal size explains 1.2% of the P&L, until you hedge

Regressing each trade's outcome on how big the deal was:

| Dependent | coef on size | t | R² |
|---|---|---|---|
| Δy10 (what v1 trades) | +0.084 | 0.41 | **0.012** |
| Δy10 − Δy2 | +0.238 | 1.94 | **0.211** |
| Δy10 − Δy5 | +0.096 | 1.54 | 0.145 |
| Δy30 − Δy10 | +0.059 | 0.92 | 0.057 |

Hedging the 2Y raises the explained share **seventeen-fold**. The issuance shock
is a steepening shock, not a level shock, so the spread keeps the signal and
drops the level risk.

This is a genuine bug in v1 that I should have caught: the hypothesis was
**tested** with a control for the 2Y (`abnormal.py`, β = 0.664 estimated on 625
non-event windows) and then **traded** without it.

### But hedging does not fix it, because of the intercept

Fitting the hedged spread change on size:

```
spread_change  =  -5.77  +  0.1864 * size        (t on slope = 1.45, R2 = 0.130)
```

Break-even deal size is **31 $bn of 10-year equivalents**. Only **3 of 16** deals
clear it. So a one-way steepener on every announcement loses money: the slope is
real and the constant is against you.

The correct construction harvests the slope alone, sizing the position by
`size − E[size]` on an expanding-window mean so it never sees future deals. Long
steepener on big deals, flattener on small ones. That gives Sharpe **+0.90 gross
and +0.31 after 6bp of two-leg cost**, with 0 of 15 leave-one-out variants
reaching t > 2.

---

## 4. The real answer: the result moves more between my specifications than it does between trades

Same 16 events, same hypothesis, three constructions:

| Version | Construction | Sharpe | t |
|---|---|---|---|
| v1 | outright 10Y, 5 days | **+0.87** | +1.24 |
| v2 | size-scaled 2s10s steepener | **−1.10** | −1.57 |
| v3 | size-demeaned spread, expanding window | **+0.31** | +0.42 |

A Sharpe swing of two full points from construction choices alone. Holding period
does the same thing inside v1: −0.88 at 2 days, +0.87 at 5 days, −0.69 at 10
days, with no monotonic structure.

Count of distinct configurations run against these same 16 events:

| Source | Configurations |
|---|---|
| v1 holding periods | 7 |
| v1 cost assumptions | 4 |
| v1 jumbo filter | 2 |
| hedge ratios | 5 |
| spread definitions | 4 |
| v2 size scaling on/off | 2 |
| v2 holding periods | 4 |
| v3 demeaned variants | 2 |
| **Total** | **30** |

At N = 16 with a signal-to-noise of 0.22, thirty configurations will produce a
Sharpe above 1 by chance. Whichever one looks best is the one that got luckiest,
and that is true no matter how principled the story I tell about it afterwards.

---

## What this means

The volatility you are seeing is not a bug to engineer out. It is the honest
width of the uncertainty around a 2.5bp effect measured 16 times. Every
construction that "fixes" it is choosing a different draw from the same
distribution.

Two things would actually change the answer, and neither is a modelling choice:

**More events.** Drop the AI framing and run all jumbo investment-grade
issuance. Hundreds of events instead of sixteen. The AI angle is what makes the
project interesting and also what makes it unanswerable.

**Intraday data.** The effect is a same-day phenomenon measured on daily closes.
Most of what there is to capture happens inside the announcement day, and daily
closes cannot see it.

Until one of those changes, the correct position size implied by this research
is zero.
