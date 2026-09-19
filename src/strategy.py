"""Is the duration finding tradable? An honest backtest.

THE TRADE, AND WHERE IT COMES FROM
The local projections say a jumbo announcement pushes long-end yields up on the
day and the effect decays to zero within about five business days. Cumulatively,
from h=0 to h=5:

    10Y spot:  b(5) - b(0)  =  -0.028 - 0.095  =  -0.123 bp per $bn 10y-equiv

So the mechanical trade is: at the CLOSE of announcement day t, after the
cheapening has already happened, buy duration. Exit at t+5. You are being paid
to warehouse the duration the dealers could not place, which is the same economic
role the concession compensates.

WHY ENTRY AT THE CLOSE OF t AND NOT INTRADAY
The FWP pricing term sheet hits EDGAR the afternoon of the trade date, and the
deal is on the screens in the morning. Entering at the close of t is the earliest
timestamp I can defend without intraday data I do not have. Entering at t-1 would
require knowing the deal before it was announced, which is the look-ahead the
whole event-dating exercise was built to avoid.

INSTRUMENT CHOICE
Modelled as a 10Y note position, P&L converted from yield via modified duration.
Reasons:
  - 10Y futures (ZN) are the deepest rates instrument and the natural expression
  - the effect is present across the curve, so I am not forced into a spread
  - a cash position would carry repo and settlement detail the free data cannot
    support, and futures embed financing in the basis
REJECTED: the 20y10y forward, where the coefficient was largest. Expressing it
needs a duration-neutral 20s30s spread, two legs of cost, and the point estimate
there is noisier. A strategy that only works in the hardest-to-trade part of the
curve is not a strategy.

COSTS
Base case 3.0bp of PRICE round trip. That is roughly two ZN ticks (1 tick =
1/64 point = 1.56bp of price) covering bid-ask plus slippage. Sensitivity run at
1.5 and 6.0. No commission modelled separately; at institutional size it is
inside the tick.

WHAT I AM NOT DOING
No parameter is optimised in sample. The holding period is fixed at 5 days from
the local projection, which was itself estimated on the same data, so the honest
version is the walk-forward below where the holding period is chosen using only
prior events.
"""
import numpy as np, pandas as pd
from config import PROC, RANDOM_SEED
import curve as C

MODDUR_10Y = 8.0          # modified duration of a ~4.5% 10Y par note
COST_BP_PRICE = 3.0       # round-trip, in bp of price
HOLD = 5                  # business days


def pnl_table(hold=HOLD, cost=COST_BP_PRICE, jumbo_only=False, dep=10.0):
    z = C.load_gsw(start="2024-01-01")
    y = z[dep] * 100                                   # bp
    ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    if jumbo_only:
        ev = ev[ev.total_usd >= 10e9]
    idx = y.index
    rows = []
    for _, e in ev.iterrows():
        p = idx.searchsorted(pd.Timestamp(e.announce))
        if p >= len(idx) or p + hold >= len(idx):
            continue
        dy = y.iloc[p + hold] - y.iloc[p]              # bp, entry close t -> exit t+hold
        gross = -dy * MODDUR_10Y / 100 * 100           # bp of price; long duration
        rows.append(dict(announce=e.announce, issuer=e.issuer,
                         size10=e.tenyr_equiv / 1e9,
                         entry=idx[p], exit=idx[p + hold],
                         dy_bp=dy, gross_bp=gross, net_bp=gross - cost))
    return pd.DataFrame(rows)


def stats(r, col="net_bp", per_year=None):
    x = r[col].values
    n = len(x)
    if n < 2:
        return {}
    span_years = (r.exit.max() - r.entry.min()).days / 365.25
    freq = per_year or (n / span_years)
    mu, sd = x.mean(), x.std(ddof=1)
    sharpe = mu / sd * np.sqrt(freq) if sd > 0 else np.nan
    eq = np.cumsum(x)
    dd = float((np.maximum.accumulate(eq) - eq).max()) if n else np.nan
    return dict(n=n, trades_per_year=freq, mean_bp=mu, sd_bp=sd,
                total_bp=x.sum(), hit=float((x > 0).mean()),
                sharpe=sharpe, maxdd_bp=dd,
                t=mu / (sd / np.sqrt(n)) if sd > 0 else np.nan)


def boot_sharpe(r, col="net_bp", n_boot=10000, seed=RANDOM_SEED):
    """IID bootstrap on trade P&L. Trades are ~monthly and the holding period is
    5 days, so they do not overlap and a block bootstrap is unnecessary."""
    rng = np.random.default_rng(seed)
    x = r[col].values
    span_years = (r.exit.max() - r.entry.min()).days / 365.25
    freq = len(x) / span_years
    out = []
    for _ in range(n_boot):
        s = rng.choice(x, size=len(x), replace=True)
        sd = s.std(ddof=1)
        out.append(s.mean() / sd * np.sqrt(freq) if sd > 0 else np.nan)
    return np.array(out)


def walk_forward(costs=COST_BP_PRICE, min_train=6, holds=(1, 2, 3, 5, 8, 10)):
    """Choose the holding period using ONLY prior events, then trade the next one.
    This is the purged-walk-forward discipline the brief demands. With one
    parameter and ~monthly events there is no overlap to purge, but the parameter
    must still never see its own trade."""
    tabs = {h: pnl_table(hold=h, cost=costs).set_index("announce") for h in holds}
    dates = sorted(tabs[holds[0]].index)
    picked, real = [], []
    for i, d in enumerate(dates):
        if i < min_train:
            continue
        best, bestval = None, -np.inf
        for h in holds:
            t = tabs[h]
            hist = t.loc[t.index < d, "net_bp"]
            if len(hist) < min_train:
                continue
            v = hist.mean() / hist.std(ddof=1) if hist.std(ddof=1) > 0 else -np.inf
            if v > bestval:
                best, bestval = h, v
        if best is None:
            continue
        picked.append(best)
        real.append(tabs[best].loc[d, "net_bp"])
    return np.array(real), np.array(picked), dates[min_train:]


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    print("=" * 78)
    print("STRATEGY: buy duration at the close of a jumbo announcement, hold 5 days")
    print("=" * 78)
    r = pnl_table()
    print(r[["announce", "issuer", "size10", "dy_bp", "gross_bp", "net_bp"]]
          .round(2).to_string(index=False))

    s = stats(r)
    print(f"\n  trades {s['n']}  ({s['trades_per_year']:.1f}/yr)   hit rate {s['hit']:.0%}")
    print(f"  mean {s['mean_bp']:+.2f} bp of price per trade, sd {s['sd_bp']:.2f}")
    print(f"  total {s['total_bp']:+.1f} bp   max drawdown {s['maxdd_bp']:.1f} bp")
    print(f"  t-stat on the mean {s['t']:+.2f}")
    print(f"  annualised Sharpe {s['sharpe']:+.2f}")

    bs = boot_sharpe(r)
    print(f"  bootstrap Sharpe 95% CI [{np.nanpercentile(bs,2.5):+.2f}, "
          f"{np.nanpercentile(bs,97.5):+.2f}]   P(Sharpe>0) = {np.nanmean(bs>0):.2f}")

    print("\n  --- cost sensitivity ---")
    for c in (0.0, 1.5, 3.0, 6.0):
        st = stats(pnl_table(cost=c))
        print(f"    cost {c:4.1f} bp: mean {st['mean_bp']:+6.2f} bp  "
              f"Sharpe {st['sharpe']:+5.2f}  total {st['total_bp']:+7.1f} bp")

    print("\n  --- holding-period sensitivity (in-sample, so not a result) ---")
    for h in (1, 2, 3, 5, 8, 10, 20):
        st = stats(pnl_table(hold=h))
        print(f"    hold {h:2d}d: mean {st['mean_bp']:+6.2f} bp  Sharpe {st['sharpe']:+5.2f}  "
              f"hit {st['hit']:.0%}  n={st['n']}")

    print("\n  --- jumbo filter ---")
    for j in (False, True):
        st = stats(pnl_table(jumbo_only=j))
        print(f"    {'jumbo only' if j else 'all deals ':12s}: n={st['n']:2d} "
              f"mean {st['mean_bp']:+6.2f} bp  Sharpe {st['sharpe']:+5.2f}")

    print("\n" + "=" * 78)
    print("WALK-FORWARD (holding period chosen from prior events only)")
    print("=" * 78)
    wf, picks, dts = walk_forward()
    if len(wf) > 1:
        sd = wf.std(ddof=1)
        span = (pd.Timestamp(dts[-1]) - pd.Timestamp(dts[0])).days / 365.25
        fr = len(wf) / max(span, 1e-9)
        print(f"  out-of-sample trades: {len(wf)}   holding periods chosen: {list(picks)}")
        print(f"  mean {wf.mean():+.2f} bp   sd {sd:.2f}   total {wf.sum():+.1f} bp")
        print(f"  Sharpe {wf.mean()/sd*np.sqrt(fr):+.2f}" if sd > 0 else "  Sharpe n/a")
        print(f"  hit rate {np.mean(wf>0):.0%}")
    else:
        print("  not enough events to walk forward")

    print("\n" + "=" * 78)
    print("CAPACITY AND POWER")
    print("=" * 78)
    s5 = stats(pnl_table())
    print(f"  events per year                 : {s5['trades_per_year']:.1f}")
    print(f"  expected gross per year         : {s5['mean_bp']*s5['trades_per_year']:+.0f} bp of price")
    se_sharpe = np.nanstd(bs)
    print(f"  bootstrap sd of Sharpe          : {se_sharpe:.2f}")
    need = int(np.ceil((2.0 / max(s5['sharpe'], 1e-9)) ** 2 * s5['trades_per_year'])) \
        if s5['sharpe'] > 0 else -1
    if need > 0:
        print(f"  years of data to get t=2 at this Sharpe: {need/ s5['trades_per_year']:.0f}")
    print("  For reference, a 5-day 10Y position has a price sd of roughly")
    print(f"  {s5['sd_bp']:.0f} bp here. The edge has to clear that plus costs.")
    r.to_csv(PROC / "strategy_trades.csv", index=False)
