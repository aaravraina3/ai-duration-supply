"""H11: does WEAK Treasury auction demand move the term premium?

WHY THIS EXISTS
In `03_FINDINGS.md` E3 I withdrew an argument. I had claimed that Treasury
coupon supply having a coefficient of -0.0014 (t = -0.15) was evidence against
duration absorption. It is not, because Treasury has held coupon auction SIZES
constant since May 2026, so the regressor is close to a constant over half the
sample and a null on a constant is not evidence about anything.

The fix is to stop using size and start using DEMAND. Every auction produces
metrics that vary a lot even when the size does not:

  bid-to-cover      total bids / amount sold. Low means thin demand.
  dealer share      primary dealers are the buyer of last resort. They take
                    whatever real money does not. A high share means the auction
                    was poorly bid.
  tail (proxy)      the yield the auction cleared at, versus where the bond was
                    trading. A positive tail means Treasury had to pay up.

23 September 2026 is exactly the event that motivated this. The 5-year came at a
bid-to-cover of 2.21 against 2.57-2.72 for every other September coupon auction,
and the 10-year moved +13bp on the day, its biggest one-day move in 18 months.

PRE-REGISTERED PREDICTIONS, written before running
  weak auction (low bid-to-cover, high dealer share, positive tail)
    -> term premium RISES
  So: coefficient on bid-to-cover NEGATIVE, on dealer share POSITIVE, on tail
  POSITIVE. If duration absorption is real, this is where it should show up
  most cleanly, because it is the same market and the buyer of last resort is
  directly observable.

MEASUREMENT CHOICES

Bid-to-cover and dealer share are pure demand ratios and are unaffected by the
level of yields, so they are the primary measures.

The tail is a proxy and I flag it as one. The real tail is the stop-out yield
versus the when-issued quote at the 1pm bidding deadline, and when-issued quotes
are not free. I use the auction's high yield minus the PREVIOUS close at the
matched tenor. That contains the day's move up to 1pm as well as the auction
concession, so it is contaminated in the direction of overstating. It is
reported alongside, never alone.

Sizes are converted to 10-year equivalents with the same `mod_duration` used on
the corporate side, so the coefficients are directly comparable to the AI
issuance number.
"""
import json, numpy as np, pandas as pd, requests, statsmodels.api as sm
from config import RAW, PROC, SEC_UA
from eventlist import mod_duration, DUR10
import curve as C

URL = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/"
       "accounting/od/auctions_query?filter=auction_date:gte:2023-06-01"
       "&page%5Bsize%5D=10000&format=json")

TERM_YEARS = {"2-Year": 2, "3-Year": 3, "5-Year": 5, "7-Year": 7,
              "10-Year": 10, "20-Year": 20, "30-Year": 30}


def fetch(refresh=False):
    p = RAW / "auctions_full.json"
    if refresh or not p.exists():
        r = requests.get(URL, headers={"User-Agent": SEC_UA}, timeout=240)
        r.raise_for_status(); p.write_bytes(r.content)
    return pd.DataFrame(json.loads(p.read_text())["data"])


def build():
    d = fetch()
    d = d[d.security_type.isin(["Note", "Bond"])].copy()
    # nominal coupons only: TIPS quote a real yield, floaters have no fixed coupon
    if "inflation_index_security" in d:
        d = d[d.inflation_index_security != "Yes"]
    if "floating_rate" in d:
        d = d[d.floating_rate != "Yes"]
    d["date"] = pd.to_datetime(d.auction_date)
    d["tenor"] = d.original_security_term.map(TERM_YEARS)
    d = d.dropna(subset=["tenor"])
    for c in ["offering_amt", "bid_to_cover_ratio", "high_yield",
              "primary_dealer_accepted", "total_accepted", "indirect_bidder_accepted"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["bid_to_cover_ratio", "total_accepted"])
    d["dealer_share"] = d.primary_dealer_accepted / d.total_accepted
    d["indirect_share"] = d.indirect_bidder_accepted / d.total_accepted
    d["ten10"] = d.offering_amt * d.tenor.map(lambda t: mod_duration(t, 4.5)) / DUR10 / 1e9

    # demand surprises: relative to the trailing 6 auctions of the SAME tenor,
    # so a 30-year is never compared against a 2-year
    d = d.sort_values("date")
    g = d.groupby("tenor")
    d["btc_norm"] = d.bid_to_cover_ratio - g.bid_to_cover_ratio.transform(
        lambda s: s.shift(1).rolling(6, min_periods=2).mean())
    d["dealer_norm"] = d.dealer_share - g.dealer_share.transform(
        lambda s: s.shift(1).rolling(6, min_periods=2).mean())

    # tail proxy against the previous close at the matched tenor
    z = C.load_gsw(start="2023-01-01")
    tails = []
    for _, r in d.iterrows():
        col = float(int(r.tenor))
        if col not in z.columns:
            tails.append(np.nan); continue
        prior = z[col][z.index < r.date]
        tails.append((r.high_yield - prior.iloc[-1]) * 100 if len(prior) else np.nan)
    d["tail_bp"] = tails
    d["tail_norm"] = d.tail_bp - d.groupby("tenor").tail_bp.transform(
        lambda s: s.shift(1).rolling(6, min_periods=2).mean())
    return d


def daily(d, start="2024-01-01", end="2026-09-24"):
    idx = pd.bdate_range(start, end)
    g = d[d.date >= start].groupby("date")
    out = pd.DataFrame(index=idx)
    out["auc_btc"] = g.btc_norm.mean().reindex(idx)
    out["auc_dealer"] = g.dealer_norm.mean().reindex(idx)
    out["auc_tail"] = g.tail_norm.mean().reindex(idx)
    out["auc_ten10"] = g.ten10.sum().reindex(idx).fillna(0.0)
    out["is_auction"] = (~out.auc_btc.isna()).astype(int)
    # demand-weighted duration: size times how badly it went
    out["weak_supply"] = out.auc_ten10 * (-out.auc_btc.fillna(0.0))
    return out.rename_axis("date")


if __name__ == "__main__":
    import regression as R
    pd.set_option("display.width", 220)
    d = build()
    print("=" * 78)
    print("TREASURY COUPON AUCTIONS, nominal only")
    print("=" * 78)
    print(f"  {len(d)} auctions, {d.date.min().date()} -> {d.date.max().date()}")
    print("\n  bid-to-cover by tenor, 2024 onward:")
    s = d[d.date >= "2024-01-01"]
    print(s.groupby("tenor").bid_to_cover_ratio.agg(["count", "mean", "std", "min"]).round(3).to_string())

    print("\n  the 23 September 2026 five-year, in context:")
    five = s[s.tenor == 5].tail(8)
    print(five[["date", "offering_amt", "bid_to_cover_ratio", "dealer_share",
                "btc_norm", "tail_bp"]]
          .assign(offering_amt=lambda x: (x.offering_amt / 1e9).round(0),
                  dealer_share=lambda x: x.dealer_share.round(3),
                  btc_norm=lambda x: x.btc_norm.round(3),
                  tail_bp=lambda x: x.tail_bp.round(1)).to_string(index=False))
    w = s.btc_norm.dropna()
    sep23 = s[(s.date == "2026-09-23") & (s.tenor == 5)]
    if len(sep23):
        v = float(sep23.btc_norm.iloc[0])
        print(f"\n  btc surprise on 23 Sep 5Y = {v:+.3f}, "
              f"percentile {100*(w < v).mean():.1f} of all 2024+ auctions")

    # ------------------------------------------------------- the regression
    dl = daily(d)
    df = R.dataset().join(dl, how="left")
    for c in ["auc_btc", "auc_dealer", "auc_tail"]:
        df[c] = df[c].fillna(0.0)
    df["weak_supply"] = df.weak_supply.fillna(0.0)
    print("\n" + "=" * 78)
    print("DOES WEAK AUCTION DEMAND MOVE THE TERM PREMIUM?")
    print("=" * 78)
    print(f"  sample {df.index.min().date()} -> {df.index.max().date()}, n={len(df)}, "
          f"auction days {int(df.is_auction.fillna(0).sum())}")
    print("  prediction: btc NEGATIVE, dealer share POSITIVE, tail POSITIVE\n")
    base = ["dbe", "doil", "dvix"]
    for name, cols in [("bid-to-cover surprise", ["auc_btc"]),
                       ("dealer share surprise", ["auc_dealer"]),
                       ("tail proxy", ["auc_tail"]),
                       ("btc + dealer", ["auc_btc", "auc_dealer"]),
                       ("size x weakness", ["weak_supply"]),
                       ("AI supply + btc", ["dD", "auc_btc"])]:
        X = sm.add_constant(df[cols + base])
        m = sm.OLS(df.dTP10, X).fit(cov_type="HAC",
                                    cov_kwds={"maxlags": 6, "use_correction": True})
        parts = "   ".join(f"{c}={m.params[c]:+.4f} (t={m.tvalues[c]:+.2f})" for c in cols)
        print(f"  {name:24s} {parts}")

    print("\n  --- same, but only on auction days (cleaner comparison) ---")
    au = df[df.is_auction == 1]
    for cols in (["auc_btc"], ["auc_dealer"], ["auc_tail"]):
        X = sm.add_constant(au[cols + base])
        m = sm.OLS(au.dTP10, X).fit(cov_type="HAC",
                                    cov_kwds={"maxlags": 3, "use_correction": True})
        c = cols[0]
        print(f"    n={len(au)}  {c:12s} coef={m.params[c]:+.4f}  t={m.tvalues[c]:+.2f}  "
              f"p={m.pvalues[c]:.3f}")
    df.to_csv(PROC / "auction_panel.csv")
    d.to_csv(PROC / "auction_detail.csv", index=False)
