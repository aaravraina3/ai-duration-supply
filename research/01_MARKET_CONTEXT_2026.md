# Market context, September 2026

What happened after the original sample closed, and why each item matters for
this project. Compiled 19 September 2026. Hard numbers are from FRED, Treasury
Fiscal Data and the Fed; narrative items are sourced inline.

---

## 1. The Fed hiked on 16 September

The FOMC raised the target range by 25bp to **3.75-4.00%**, unanimous **12-0**,
no dissents. The statement says inflation "remains elevated" and frames the hike
as supporting "a timelier return to the Committee's 2 percent goal." It also
describes "robust capital investment," and cites uncertainty from geopolitical
developments.

Confirmed in the data: effective fed funds (`DFF`) moves **3.63% to 3.88% on
2026-09-17**, the day after the decision.

**The market reaction is the interesting part.**

| Date | 2Y | 10Y | 30Y | 10Y breakeven | VIX |
|---|---|---|---|---|---|
| 2026-09-15 | 4.67 | **5.00** | 5.36 | 2.38 | 17.20 |
| 2026-09-16 (FOMC) | 4.74 | **5.01** | 5.35 | 2.33 | 17.71 |
| 2026-09-17 | 4.67 | **4.94** | 5.29 | 2.33 | 15.44 |

Yields **fell** after the hike, the curve bull-flattened, breakevens dropped 5bp
and VIX fell 2.3 points. That is a credibility response: the market read the hike
as inflation-fighting and took compensation out of the long end.

**Why it matters here.** The 10Y's 5% crossing on 15 September, the headline
event motivating this whole project, was reversed within two sessions by a
monetary policy action. Any story that attributes the long end to corporate
supply has to explain why one 25bp hike undid the last 6bp of it in a day.

Source: [FOMC statement, 16 Sep 2026](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm)

---

## 2. The BOJ hiked on 18 September, and the yen is being defended jointly

The Bank of Japan raised its policy rate 25bp to **1.25%, the highest since
1995**, on a split **7-2** vote (Asada and Sato dissenting). The BOJ cited risk
of inflation overshooting 2%. The hike came three months after the previous one,
against six months before that, so the normalization cycle is accelerating.

Yen traded **156.64** after the decision, weaker by 0.45%. JGB 10Y **fell 4.9bp
to 2.947%**.

Context that matters more than the hike itself:

- **Tokyo and Washington have been intervening jointly** to support the yen.
  Coordinated intervention is rare and signals the level is a policy concern for
  both sides.
- JGB 10Y at ~2.95% is the highest since 1997. The 30Y JGB **breached 4% for the
  first time since the maturity was introduced in 1999**.
- Japanese investors hold roughly **$1 trillion** of Treasuries, the largest
  foreign position, and sold **$29.6B in Q1 2026 alone**.

**Why it matters here.** This is the single largest competing explanation for the
2026 long end and it dwarfs the AI story in size. My entire AI universe supplies
194 $bn of 10-year-equivalent duration in 2026. One quarter of Japanese net
selling is $29.6B of actual Treasuries, and the at-risk stock is $1T. If domestic
JGB yields now clear what a currency-hedged Treasury pays, the marginal foreign
buyer of US duration disappears, and that is a level effect rather than a
three-day announcement effect.

Sources: [CNBC on the BOJ hike](https://www.cnbc.com/2026/09/18/japan-raises-rates-30-year-high-yen-jgb.html),
[CNBC on intervention](https://www.cnbc.com/2026/09/03/yen-japan-intervention-boj.html),
[OMFIF on coordinated intervention](https://www.omfif.org/2026/08/japans-yen-intervention-and-the-us-unusual-support/),
[Fortune on repatriation](https://fortune.com/2026/05/17/us-debt-japan-investors-treasury-bonds-top-foreign-holders-repatriation-jgb-treasury-yields/),
[CNBC on the JGB market](https://www.cnbc.com/2026/07/14/japan-bond-jgb-yields-.html)

---

## 3. Oil went from $94 to $107 in a week

WTI (`DCOILWTICO`): **$94.21 on 8 Sep, $103.57 on 10 Sep, $107.02 on 15 Sep**.
That is +13.6% into the exact window where the 10Y crossed 5%.

Reported cause is three simultaneous supply shocks: damage to Saudi Arabia's
East-West pipeline, threats to the Strait of Hormuz, and Red Sea disruption.
Commentary frames it as a structural delivery problem rather than a flare-up,
because the two routes that normally absorb transit risk are compromised at once.

**Why it matters here.** The oil control in the main regression is a daily log
return, which is right for a daily specification and useless for a level shift of
this size. A 13.6% move in the week the 10Y peaked is a first-order confound for
the September segment of the sample. It is also the most likely reason breakevens
were where they were before the Fed hike knocked them down.

Sources: [Gulf News on the WTI jump](https://gulfnews.com/business/energy/wti-oil-price-jumps-8-as-middle-east-tensions-rattle-global-markets-1.500471588),
[Octagon on the pipeline repricing](https://www.octagonai.co/news/wti-oil-price-forecast-september-2026-prediction-market)

---

## 4. Treasury doubled long-end buybacks, effective 9 September

Treasury increased liquidity-support buybacks for nominal coupons in the
**10Y-20Y and 20Y-30Y** sectors from a $2B maximum per operation to **at least
$4B**, effective **9 September 2026**, running through 4 November.

Visible in the operations data:

| Operation date | Bucket | Par accepted |
|---|---|---|
| 2026-09-10 | 10Y to 20Y | $5.19B |
| 2026-09-17 | 7Y to 10Y | $2.39B |

Separately, **coupon auction sizes have been held steady since May 2026**, with
dealers not expecting changes until early 2027.

**Why it matters here, twice over.**

First, this is a dated, measurable, long-end duration *removal* running in the
opposite direction to AI issuance, and it started six days before the 5%
crossing. It belongs in the model as a control at minimum, and arguably as its
own channel.

Second, it explains a result I could not account for. My `auc_10y` regressor had
a coefficient of −0.0014 with t = −0.15, which I read as evidence against
duration absorption. Part of that is now mechanical: if auction sizes have been
constant for four months, the variable has almost no variation left to identify
anything from. That weakens my own counterargument against the mechanism, and I
should say so.

Sources: [Treasury buyback size increase](https://home.treasury.gov/news/press-releases/sb0607),
[Reuters/Yahoo on steady auction sizes](https://finance.yahoo.com/economy/policy/articles/us-treasury-keeps-auction-sizes-145911745.html)

---

## 5. Fiscal background

- A shutdown was averted on **2 September** via H.R. 6500, funding the government
  through **11 December 2026**.
- Total public debt passed **$40 trillion in August**, against a **$41.1T** limit
  set by the July 2025 reconciliation act.
- FY2026 opened with the longest shutdown in modern history, **1 October 2025 to
  12 November 2025**.

**Why the shutdown matters here.** It is a data-integrity point I had already
half-observed. My BLS calendar parse found only 11 CPI releases in 2025 instead
of 12, and irregular payroll dates in early 2026 (11 February on a Wednesday,
28 April on a Tuesday). I had written that off as parser noise being
conservative. It was the shutdown disrupting the release schedule. The macro
exclusion windows in the event study are therefore correct for the wrong reason,
and the 2025 Q4 macro calendar should be treated as unreliable.

Sources: [CRFB fiscal deadlines](https://www.crfb.org/blogs/upcoming-congressional-fiscal-policy-deadlines),
[Treasury Fiscal Data on the debt](https://fiscaldata.treasury.gov/americas-finance-guide/national-debt/)

---

## 6. What this does to the project

The original question was whether AI corporate duration supply explains the 2026
long end. As of 19 September there are at least five candidate drivers for the
same move, ordered by the size of the flow involved:

| Driver | Scale | Frequency | Tested? |
|---|---|---|---|
| Japanese repatriation | ~$1T stock, $29.6B sold in Q1 | Monthly (free data) | **No** |
| Fed policy | 25bp hike, 10Y −7bp next day | Daily | Partially (controls only) |
| Oil supply shock | +13.6% in a week | Daily | Weakly (log returns only) |
| Treasury buybacks | $4B/op, 10-30Y, from 9 Sep | Daily | **No** |
| AI corporate supply | 194 $bn 10y-equiv in 2026 | Event | Yes |

AI supply is the **smallest** flow on that list and the only one I have tested
properly. That is a scope problem, and it is the honest framing for what comes
next.
