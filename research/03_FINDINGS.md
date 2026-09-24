# Findings

The only place a number is stated as established. Everything else links here.
Each finding carries its inference method, because in this project Newey-West
t-statistics and randomization tests disagree, and the randomization tests win.

Confidence labels:
- **A** survives leave-one-out, a randomization test, and specification variation
- **B** point estimate robust, inference marginal
- **C** suggestive, does not clear conventional significance
- **X** established negative result

Last updated 19 September 2026.

---

## A. The event list

**A1.** 16 USD bond offerings from the five issuers, Jan 2024 to Sep 2026,
reconstructed from SEC 424B cover pages with announcement dates recovered from
matching FWP pricing term sheets. **All 16 matched on the complete set of
coupons.** Confidence **A**.

**A2.** 2025 USD issuance totals **$92.75B** against a widely quoted ~$93B. This
is the external validation of the parser. 2026 year to date is **$179.5B**, well
above the ~$132B commonly quoted. Confidence **A**.

**A3.** Excluded, with reasons: $34.8B equivalent of non-USD tranches (EUR, GBP,
JPY samurai), Microsoft's Activision debt exchange, and the Oracle and Alphabet
mandatory convertible preferreds plus Oracle's ATM equity program. Microsoft
issued **no new public USD bonds** in the window. Confidence **A**.

**A4.** Final event sample **N = 7** at the $10B jumbo threshold with the
window-contamination macro rule. 12 jumbos before the macro filter. Confidence
**A**.

---

## B. The duration channel

This is where the project's weight now sits, and it strengthened materially on
19 September with the buyback test.

**B1. Issuance raises the term premium on announcement.** +0.080 bp per $bn of
10-year equivalents at h=0. NW t = 3.42, **but OLS t = 1.92 and the randomization
p is 0.069**. Kish effective n is 9.6, not 673. Survives leave-one-out (+0.067 to
+0.093, min |t| = 2.59), dropping all three overlapping deal pairs (+0.090), and
a wild cluster bootstrap (p = 0.017). Confidence **B**.

**B2. The effect is transitory.** h=2: +0.113 (p = 0.116). h=5: **+0.011,
p = 0.918**. Gone within a week. Confidence **A**. This is the finding that most
directly contradicts a persistent 30bp supply story.

**B3. Treasury buybacks move the term premium the opposite way.** NEW. Treasury
removed **173.7 $bn of 10-year-equivalent duration** through long-bucket
buybacks since 2024, against 317.4 $bn added by AI issuance. Coefficient
**−0.180 bp per $bn** at h=0 (t = −1.39), negative at every horizon h=0 to h=10,
and stable to the bucket-midpoint assumption (−0.19 to −0.17 for ±2y). Both
channels coexist in one regression with the right signs: issuance **+0.0835**
(t = +3.62), buybacks **−0.168** (t = −1.30). Randomization p = 0.34.
Confidence **C** on its own, but see B4.

**B4. The effect is largest where the curve is least mechanically tied to the
cash 10Y.** NEW, and the strongest mechanism evidence in the project.

Announcement-day response by curve segment, AI issuance:

| Dependent | h=0 coefficient | t | R² with Δ10Y spot |
|---|---|---|---|
| 10Y spot | +0.0950 | 3.21 | 1.000 |
| 5y5y forward | +0.1108 | 3.66 | 0.901 |
| 10y10y forward | +0.1339 | 3.72 | 0.528 |
| 20y10y forward | +0.1111 | 3.18 | **0.103** |

The ratio of the 5y5y response to the 10Y spot response is **+1.17**. The effect
is *larger* in the far forwards than in cash.

Treasury buybacks, same specification, sign reversed as predicted:

| Dependent | h=0 | t | h=2 | t |
|---|---|---|---|---|
| 10Y spot | −0.057 | −0.32 | −0.030 | −0.09 |
| 5y5y | −0.169 | −0.91 | −0.199 | −0.61 |
| 10y10y | −0.278 | −1.53 | −0.150 | −0.44 |
| 20y10y | **−0.668** | **−1.97** | **−1.028** | **−2.81** |

Why this matters: the 20y10y forward has an R² of only **0.103** with the cash
10Y, so it is nearly orthogonal to the point where a dealer would put on a rate
lock. An effect that appears there is not a hedging artifact in the 10Y. And
buybacks bite hardest exactly at 20y10y, which is the sector Treasury is actually
buying (10Y-20Y and 20Y-30Y buckets).

Confidence **B**, downgraded from A for multiplicity: this is 30 tests
(5 dependents x 3 horizons x 2 shocks) with no correction. The defence is the
**coherence** of the pattern rather than any single t-statistic. Every AI
coefficient is positive at h=0 and h=2, every buyback coefficient is negative at
every horizon, and the buyback effect concentrates in the sector Treasury
operates in. That joint pattern is harder to produce by chance than one
significant cell.

**B5. Weak auction demand raises the term premium.** NEW, 23 Sep. Bid-to-cover
surprise carries **-4.49 (t = -1.79)**, randomization p = 0.0705, concentrated at
7-10y auctions (-14.85, t = -2.77) and absent elsewhere. A one-standard-deviation
weak auction is worth **+0.50 bp**, against +1.76 bp for a $25B AI deal, but
Treasury runs roughly 84 coupon auctions a year against 5.9 AI deals. Decays by
half in one business day. Confidence **C** alone, **B** as part of the pattern in
B3/B4. The tail proxy was contaminated (R2 = 0.390 with the same-day move) and
is not used.

**B6. Three flows, three correct signs.** Corporate issuance adds duration and
raises the term premium (+0.080/$bn). Treasury buybacks remove it and lower it
(-0.180/$bn). Weak auction demand makes duration harder to place and raises it
(-4.49 per unit bid-to-cover). All three are marginal individually and all three
are transitory. The coherence across independent flows is the evidence, not any
single t-statistic.

---

## C. What cannot be measured here

**C1. Maturity-localized concession is not identifiable from published curves.**
Confidence **X**, and proven rather than assumed. An injected 5bp bump is
recovered at **77.7%** by the 3-factor residualization alone, and at **−10.7%**
after GSW's Svensson re-fit. The smoothing scrambles sign, not just magnitude.
Confirmed out of sample: the measured concession flips from −0.167 bp (band 4y,
t = −2.20) to +0.123 bp (band 3y, t = +3.16). The FRED par grid leaves 0.86
control tenors under a ±2y band. Needs TRACE or CRSP.

**C2. The event study is underpowered.** Placebo sd 1.70 bp at N = 7 gives a
minimum detectable effect of **3.3 bp at 95%** and 4.7 bp for 80% power. The
expected effect is 1 to 3 bp. Confidence **A** on the power calculation itself.

**C3. X = +0.82 bp is one observation.** Leave-one-out range −0.120 to +1.595.
Dropping Meta 2024-08-07 flips the sign; that event's abnormal move is +8.88 bp
against −3.4 to +3.5 for the other six, and it sits inside the August 2024
yen-carry unwind (VIX 38.57 on 08-05). **Do not cite X.** Confidence **X**.

**C4. MBS is untested.** No free daily or monthly agency MBS issuance series was
reachable. It is a named component of the 30bp claim, so no statement about that
claim is complete. Confidence **X**.

---

## D. Scale, and what the 2026 move actually was

**D1. Y = +81 bp.** 10Y CMT from 4.19% on 2026-01-02 to 5.00% on 2026-09-15.
Confidence **A**.

**D2. The term premium decomposition is endpoint-dependent and my earlier
framing was wrong.** Across 25 start/end pairs ΔTP ranges **−28.6 to +23.9 bp,
positive in 12 of 25**. Over the full 2024-2026 sample the 10Y rose 105 bp of
which **+103.1 bp is term premium** and −1.7 bp is expectations, the reverse of
the calendar-2026 cut. The only endpoint-robust statement is that within
calendar-2026 windows |ΔExp| > |ΔTP| in all 25 pairs. Confidence **A** on the
sensitivity itself.

**D3. AI supply is the smallest flow in contention.** 2026 AI issuance is
**194 $bn** of 10-year equivalents, which is **9.4%** of Treasury coupon duration
supply (2073.5 $bn) and 3.9% in 2025. Japanese investors hold ~$1T of Treasuries
and sold $29.6B in Q1 2026 alone. Confidence **A** on the ratios computed from
Fiscal Data; the Japan figures are sourced, not computed here.

**D4. The 5% crossing was undone by the Fed within two sessions.** 10Y at 5.01 on
16 September (FOMC day), **4.94 on 17 September** after a 25bp hike to
3.75-4.00%. Breakevens fell 5bp, VIX fell 2.3 points. Confidence **A** on the
data; the credibility interpretation is unconfirmed pending H9.

---

## E. Dead ends

**E1. HMM regimes.** No state separates supply-led from inflation-led. Breakevens
co-move with yields at ~0.6 in all three states. BIC cannot distinguish K=2 from
K=3 (−4332.1 vs −4332.5).

**E2. The NLP index.** 716 effectively distinct passages after 0.90 dedup from 68
filings; 82% of the raw corpus has a near-duplicate. Wrong-signed coefficient
(t = −1.20) and **beaten by a plain decayed passage count** (t = +2.86).

**E3. "Treasury supply does nothing, so duration absorption is false."** (now
replaced by a positive result, see B5) I made
this argument from a coefficient of −0.0014 (t = −0.15). It is now withdrawn.
Treasury has held coupon auction sizes constant since May 2026, so the regressor
is close to a constant over much of the sample and a null on it is not evidence.
B3 and B4 are the better test of the same question, and they point the other way.

---

## Current best summary

AI corporate issuance produces a real, transitory increase in long-end
compensation of roughly 0.08 to 0.13 bp per $bn of 10-year equivalents,
concentrated on the announcement day and gone within a week. The effect appears
across the forward curve including segments nearly orthogonal to the cash 10Y,
and Treasury buybacks move the same measures the opposite way, most strongly in
the sector Treasury actually buys. Together that is a coherent duration-absorption
signature.

What it is not: a persistent level effect, an explanation for the 2026 selloff,
or a tested version of the sell-side 30bp claim. AI issuance is the smallest of
at least five flows moving the same market, and the largest of them, Japanese
repatriation, remains untested.
