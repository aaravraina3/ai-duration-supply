# Is this tradable?

Short answer: **no, and I would not put money on it.** The numbers are below so
you can see why rather than take my word.

I am not licensed to give investment advice and I will not place trades. This is
a backtest of a hypothesis, written up the way I would write up any other
negative result.

---

## The trade

The local projections say a jumbo announcement pushes long-end yields up on the
day and the effect decays to zero within about five business days. From h=0 to
h=5 on the 10Y spot, the cumulative coefficient goes from +0.095 to −0.028 bp per
$bn of 10-year equivalents.

So: **buy duration at the close of announcement day, exit five business days
later.** Economically you are being paid to warehouse the duration the dealers
could not place, which is the same role the concession compensates.

Modelled as a 10Y note position, P&L converted from yield by modified duration
(8.0), costs 3bp of price round trip (about two ZN ticks).

Entry at the close of day t, never earlier. The FWP hits EDGAR that afternoon and
the deal is on screens in the morning, so the close is the earliest timestamp I
can defend without intraday data.

---

## What it returns

| | |
|---|---|
| Trades | 16 over 2024-2026 (7.9/yr) |
| Hit rate | 56% |
| Mean per trade | **+19.2 bp of price** |
| Standard deviation | 62.1 bp |
| Total | +308 bp |
| Max drawdown | 102 bp |
| **t-stat on the mean** | **+1.24** |
| In-sample Sharpe | +0.87 |
| **Bootstrap Sharpe 95% CI** | **[−0.50, +2.55]** |
| P(Sharpe > 0) | 0.90 |
| **Walk-forward Sharpe** | **+0.55**, hit rate 50%, n=10 |

Positive point estimate. Cannot reject zero on any measure.

---

## Four reasons it fails

### 1. The t-stat never clears 2 under any sample perturbation

Leave-one-out across all 16 trades:

| Dropped | That trade's P&L | Sharpe without it | t without it |
|---|---|---|---|
| Alphabet 2026-02-09 | +124.7 bp | 0.58 | 0.82 |
| Meta 2024-08-07 | +112.4 bp | 0.62 | 0.86 |
| ... | | | |
| Alphabet 2025-04-28 | −102.0 bp | 1.36 | **1.93** |

**0 of 16 leave-one-out variants reach t > 2.** The best case, dropping the worst
trade, still only gets to 1.93.

### 2. The P&L is three trades

Top 3 winners contribute **315 bp against a 308 bp total, which is 102%**. The
other 13 trades net to slightly negative. Median trade is +10.1 bp against a mean
of +19.2.

And the second-largest winner is **Meta 2024-08-07 at +112 bp**, the same event
that single-handedly drives the X result and sits inside the August 2024
yen-carry unwind, with VIX at 38.57 three days earlier. That is not an issuance
effect, that is a volatility event that happened to have a bond deal in it.

### 3. The holding period has no structure

| Hold | 1d | 2d | 3d | **5d** | 8d | 10d | 20d |
|---|---|---|---|---|---|---|---|
| Sharpe | +0.07 | **−0.88** | +0.39 | **+0.87** | −0.56 | −0.69 | −0.22 |

A real decaying effect produces a smooth profile. This oscillates between −0.88
and +0.87 with no monotonic structure, and 5 days happens to be the best of seven
choices. That is the signature of noise being selected over, not of an edge.

The walk-forward exists precisely to price that in, and it takes the Sharpe from
0.87 to 0.55 with a coin-flip hit rate.

### 4. Costs are not the problem, which is its own problem

| Round-trip cost | Mean per trade | Sharpe |
|---|---|---|
| 0.0 bp | +22.2 | +1.01 |
| 1.5 bp | +20.7 | +0.94 |
| 3.0 bp | +19.2 | +0.87 |
| 6.0 bp | +16.2 | +0.74 |

At **zero cost** it is still not significant. There is no cost assumption that
rescues it, and none that kills it either. The edge is simply inside the noise.

---

## What it would take

At the estimated Sharpe, reaching t = 2 needs roughly **five more years** of
events at 7.9 per year. The 5-day position has a price standard deviation of
62 bp, so the per-trade edge of 19 bp is under a third of one standard deviation.

For scale on a single ZN contract ($100k face): expected gross is about $1,530 a
year, per-trade standard deviation about $620, and the realised drawdown was
$1,020. You would be risking a known amount for an edge you cannot distinguish
from zero.

---

## If you wanted to keep pulling this thread

The honest version of this research is not a strategy, it is a **risk factor**.
"Jumbo duration supply is announced today" is a real, dated, observable state
variable that correlates with a few basis points of long-end cheapening. That is
useful as a tilt on execution timing if you already have a reason to be
transacting in duration, and it is not useful as a standalone position.

Things that would actually raise the power:

1. **Widen the universe.** Sixteen deals is the binding constraint. All jumbo IG
   issuance, not just five AI names, gets you to hundreds of events. The AI angle
   is what makes the project interesting and also what makes it underpowered.
2. **Trade the buyback side too.** Treasury ran 67 long-bucket operations against
   16 deals, and the coefficient there was −0.180 with the sign the mechanism
   predicts. More events, same hypothesis, opposite direction.
3. **Get intraday.** The effect is a same-day phenomenon measured on daily
   closes. Most of what you would capture is happening inside the announcement
   day and I cannot see it.

---

## The bottom line

The research finding is real enough to publish with caveats: duration supply
moves long-end compensation transiently, in the direction the mechanism predicts,
confirmed by the buyback mirror and by showing up in forwards nearly orthogonal
to the cash 10Y.

The trading finding is that it is too small, too rare and too noisy to monetise
at N=16. Those are different statements and the second one does not undo the
first.
