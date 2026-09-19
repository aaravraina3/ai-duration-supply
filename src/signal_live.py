"""Live signal generator: scan EDGAR for new hyperscaler deals and print the
position the v3 rule implies.

This is tooling. It computes a rule mechanically; it is not advice and it has no
demonstrated edge. The statistical health block prints with every signal on
purpose, so the number never travels without its error bar.

RULE (v3, the only construction that is both hedged and free of the intercept)
  1. Detect a new USD bond deal from the five issuers via the FWP pricing term
     sheet, which carries the trade date.
  2. Compute the deal's 10-year-equivalent duration D.
  3. Compare it to the expanding-window mean of prior deals, z = D - E[D].
  4. Position = sign(z) * |z| / mean|z|  units of a DV01-matched 2s10s spread,
     expressed as: short 10Y duration / long 2Y duration when z > 0.
  5. Hold 5 business days, then flat.

    z > 0  (bigger than typical deal)  -> STEEPENER  (short 10Y vs 2Y, DV01 matched)
    z < 0  (smaller than typical deal) -> FLATTENER (long 10Y vs 2Y, DV01 matched)

WHY THE HEDGE RATIO IS 0.664 AND NOT FITTED HERE
It comes from abnormal.py, estimated on 625 NON-event windows. Refitting it on
the event sample would be the leak this whole project has been trying to avoid.
"""
import json, sys, time, datetime as dt
import numpy as np, pandas as pd, requests
from config import PROC, RAW, SEC_UA, ISSUERS
from eventlist import mod_duration, DUR10

BETA = 0.664
HOLD = 5
LOOKBACK_DAYS = 10

HEALTH = """
  ------------------------------------------------------------------
  STATISTICAL HEALTH OF THIS SIGNAL   (read before sizing anything)
    backtested N                16 events
    signal-to-noise             0.22  (2.56bp effect vs 11.36bp noise)
    v3 Sharpe after costs       +0.31
    bootstrap 95% CI on Sharpe  includes zero
    leave-one-out variants t>2  0 of 15
    configurations tried        30 on the same 16 events
    events needed for t=2       ~80
  The backtest cannot distinguish this rule from noise. Position size
  implied by the evidence is zero. See research/07_WHY_VOLATILE.md.
  ------------------------------------------------------------------
"""


def recent_filings(days=LOOKBACK_DAYS):
    """Poll EDGAR submissions for FWP / 424B filings in the last `days`."""
    S = requests.Session(); S.headers.update({"User-Agent": SEC_UA})
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    hits = []
    for cik, name in ISSUERS.items():
        try:
            r = S.get(f"https://data.sec.gov/submissions/CIK{cik}.json", timeout=60)
            r.raise_for_status()
            rec = pd.DataFrame(json.loads(r.content)["filings"]["recent"])
            m = rec[rec.form.isin(["FWP", "424B2", "424B5"]) & (rec.filingDate >= cutoff)]
            for _, x in m.iterrows():
                hits.append(dict(issuer=name, cik=cik, form=x.form,
                                 date=x.filingDate, accession=x.accessionNumber,
                                 doc=x.primaryDocument))
            time.sleep(0.25)
        except Exception as e:
            print(f"  [warn] {name}: {e}", file=sys.stderr)
    return pd.DataFrame(hits).sort_values("date") if hits else pd.DataFrame()


def position_for(size10, prior_sizes):
    """v3 rule. prior_sizes must contain ONLY deals announced before this one."""
    if len(prior_sizes) < 6:
        return None, "insufficient history (need >=6 prior deals)"
    z = size10 - np.mean(prior_sizes)
    scale = abs(z) / np.mean(np.abs(np.array(prior_sizes) - np.mean(prior_sizes)))
    side = "STEEPENER (short 10Y / long 2Y, DV01 matched)" if z > 0 else \
           "FLATTENER (long 10Y / short 2Y, DV01 matched)"
    return dict(z=z, units=scale, side=side, hedge_ratio=BETA, hold_days=HOLD), None


def main():
    print("=" * 70)
    print(f"DURATION-SUPPLY SIGNAL   {dt.date.today()}")
    print("=" * 70)

    hist = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"]).sort_values("announce")
    prior = (hist.tenyr_equiv / 1e9).tolist()
    print(f"  history: {len(prior)} USD deals, mean {np.mean(prior):.1f} $bn 10y-equiv, "
          f"last {hist.announce.max().date()}")

    print(f"\n  scanning EDGAR for FWP/424B filings in the last {LOOKBACK_DAYS} days...")
    f = recent_filings()
    if f.empty:
        print("  no new filings from the five issuers.")
        print("\n  POSITION: FLAT (no live signal)")
        print(HEALTH)
        return

    print(f"  found {len(f)} filing(s):")
    for _, x in f.iterrows():
        print(f"    {x.date}  {x.issuer:9s} {x.form:6s} {x.accession}")

    # Currency check. Alphabet and Amazon file EUR/GBP/JPY deals through the same
    # form types on adjacent days, and those supply duration to bunds, gilts and
    # JGBs rather than Treasuries. Without this the tool signals on a gilt deal.
    print("\n  classifying currency (non-USD deals supply no Treasury duration)...")
    usd_hits = []
    S = requests.Session(); S.headers.update({"User-Agent": SEC_UA})
    for _, x in f.iterrows():
        url = (f"https://www.sec.gov/Archives/edgar/data/{int(x.cik)}/"
               f"{x.accession.replace('-','')}/{x.doc}")
        try:
            resp = S.get(url, timeout=90)
            # parse_doc infers issuer/date/form/accession from the stem, so the
            # temp file has to follow the same naming convention as the corpus
            tmp = RAW / "filings" / f"{x.issuer}_{x.date}_{x.form}_{x.accession}.htm"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(resp.content)
            import events as E
            d = E.parse_doc(tmp)
            ccys = {t["ccy"] for t in d["tranches"]}
            tot = sum(t["notional"] for t in d["tranches"]) / 1e9
            tag = ("/".join(sorted(ccys)) if ccys else "no tranche table")
            print(f"    {x.date} {x.issuer:9s} {x.form:6s} -> {tag}"
                  + (f", {tot:.2f}B" if tot else ""))
            if "USD" in ccys:
                usd_hits.append((x, d))
            time.sleep(0.25)
        except Exception as e:
            print(f"    {x.date} {x.issuer:9s} {x.form:6s} -> parse failed: {e}")

    if not usd_hits:
        print("\n  no USD bond deal in the window.")
        print("  POSITION: FLAT (recent filings are non-USD or not bond offerings)")
        print(HEALTH)
        return

    print(f"\n  {len(usd_hits)} USD deal(s) detected. Sizing:")
    for x, d in usd_hits:
        usd = [t for t in d["tranches"] if t["ccy"] == "USD"]
        ann = pd.Timestamp(d["trade_date"] or x.date)
        size10 = sum(t["notional"] * mod_duration(t["mat_year"] - ann.year,
                                                  t["coupon"], t["floating"])
                     for t in usd) / DUR10 / 1e9
        pos, err = position_for(size10, prior)
        print(f"    {x.issuer} announced {ann.date()}: {size10:.1f} $bn 10y-equiv")
        if err:
            print(f"      {err}")
        else:
            print(f"      z = {pos['z']:+.1f} $bn -> {pos['side']}, "
                  f"{pos['units']:.2f} units, hold {pos['hold_days']}d")

    # worked example so the output is never abstract
    print("\n  worked example, a $25B deal with typical 8.5y duration:")
    ex_size = 25.0 * mod_duration(8.5, 4.5) / DUR10
    pos, err = position_for(ex_size, prior)
    if err:
        print(f"    {err}")
    else:
        print(f"    10y-equivalents  : {ex_size:.1f} $bn")
        print(f"    z vs prior mean  : {pos['z']:+.1f} $bn")
        print(f"    position         : {pos['side']}")
        print(f"    size             : {pos['units']:.2f} units")
        print(f"    hedge ratio      : {pos['hedge_ratio']} (2Y DV01 per 1.0 of 10Y DV01)")
        print(f"    hold             : {pos['hold_days']} business days, then flat")
    print(HEALTH)


if __name__ == "__main__":
    main()
