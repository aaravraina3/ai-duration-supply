"""Strategy v2: hedge the market, scale by deal size.

WHAT v1 GOT WRONG
v1 held an outright 10Y for five days. Diagnostics in variance.py:
  - 5-day 10Y yield sd is 11.36bp; times ModDur 8 that is 91bp of price
  - v1's realised P&L sd was 62bp, i.e. it was essentially an unhedged duration bet
  - deal size explained 1.2% of P&L variance (R2 = 0.012, t = 0.41)
  - signal-to-noise in yield terms: 2.56bp expected effect vs 11.36bp noise = 0.22

So v1 was a directional rates position wearing an event-study costume. The
hypothesis was TESTED with a control for the 2Y (abnormal.py, beta = 0.664 fit on
625 non-event windows) and then TRADED without it. That was the bug.

THE FIX, AND WHY IT IS NOT DATA MINING
Hedge the 2Y exposure and scale the position by deal size. Both choices are
pinned by things decided before this backtest existed:
  - the hedge instrument is the 2Y because that is the control in abnormal.py
  - the hedge ratio is 0.664 because that is the coefficient estimated there, on
    NON-EVENT windows, so it never saw a trade
  - size scaling because the hypothesis is that the effect is proportional to
    duration supplied, which is what every regression in this project assumes

I am not searching over hedge instruments. variance.py did look at 5 of them and
that selection is flagged there; this module fixes the choice to the one the
hypothesis already specified.

WHAT THE HEDGE DOES TO THE SIGNAL
Regressing the 5-day move on deal size:

    dy10        on size:  coef +0.084,  t = 0.41,  R2 = 0.012
    dy10 - dy2  on size:  coef +0.238,  t = 1.94,  R2 = 0.211

Seventeen times more of the variation is explained by deal size once the level is
hedged out. The issuance shock is a STEEPENING shock, not a level shock, so the
spread keeps the signal while dropping most of the noise.

SIGN, CAREFULLY
The coefficient on (dy10 - dy2) is POSITIVE over t -> t+5. A bigger deal means
the 10Y cheapens relative to the 2Y over the following week. So the position is a
2s10s STEEPENER: short 10Y duration, long 2Y duration, DV01-matched. That is the
opposite direction from v1, which was long duration expecting reversion.

v1 made money from a mean that was not size-proportional. v2 targets the
size-proportional component, which is the part the hypothesis actually predicts.
"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, RANDOM_SEED
import curve as C

MODDUR = 8.0
BETA = 0.664            # from abnormal.py, fit on 625 non-event windows
COST_BP = 6.0           # two legs, ~3bp each round trip
HOLD = 5


def trades(hold=HOLD, beta=BETA, cost=COST_BP, size_scaled=True, jumbo_only=False):
    z = C.load_gsw(start="2024-01-01")
    y10, y2 = z[10.0] * 100, z[2.0] * 100
    ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    if jumbo_only:
        ev = ev[ev.total_usd >= 10e9]
    idx = z.index
    rows = []
    mean_size = (ev.tenyr_equiv / 1e9).mean()
    for _, e in ev.iterrows():
        p = idx.searchsorted(pd.Timestamp(e.announce))
        if p >= len(idx) or p + hold >= len(idx):
            continue
        size = e.tenyr_equiv / 1e9
        spread = (y10.iloc[p + hold] - y10.iloc[p]) - beta * (y2.iloc[p + hold] - y2.iloc[p])
        # steepener: profits when the 10Y cheapens vs the 2Y
        gross = spread * MODDUR
        scale = size / mean_size if size_scaled else 1.0
        rows.append(dict(announce=e.announce, issuer=e.issuer, size10=size,
                         scale=scale, spread_bp=spread,
                         gross_bp=gross * scale, net_bp=gross * scale - cost * scale,
                         entry=idx[p], exit=idx[p + hold]))
    return pd.DataFrame(rows)


def stats(r, col="net_bp"):
    x = r[col].values
    span = (r.exit.max() - r.entry.min()).days / 365.25
    freq = len(x) / span
    mu, sd = x.mean(), x.std(ddof=1)
    eq = np.cumsum(x)
    return dict(n=len(x), mean=mu, sd=sd, total=x.sum(), hit=float((x > 0).mean()),
                t=mu / (sd / np.sqrt(len(x))) if sd > 0 else np.nan,
                sharpe=mu / sd * np.sqrt(freq) if sd > 0 else np.nan,
                maxdd=float((np.maximum.accumulate(eq) - eq).max()), freq=freq)


def boot(r, col="net_bp", n=10000, seed=RANDOM_SEED):
    rng = np.random.default_rng(seed)
    x = r[col].values
    span = (r.exit.max() - r.entry.min()).days / 365.25
    freq = len(x) / span
    out = []
    for _ in range(n):
        s = rng.choice(x, len(x), replace=True)
        sd = s.std(ddof=1)
        out.append(s.mean() / sd * np.sqrt(freq) if sd > 0 else np.nan)
    return np.array(out)


def walk_forward(min_train=6, holds=(2, 3, 5, 8)):
    tabs = {h: trades(hold=h).set_index("announce") for h in holds}
    dates = sorted(tabs[holds[0]].index)
    real, picks = [], []
    for i, d in enumerate(dates):
        if i < min_train:
            continue
        best, bv = None, -np.inf
        for h in holds:
            hist = tabs[h].loc[tabs[h].index < d, "net_bp"]
            if len(hist) < min_train or hist.std(ddof=1) == 0:
                continue
            v = hist.mean() / hist.std(ddof=1)
            if v > bv:
                best, bv = h, v
        if best is None:
            continue
        picks.append(best); real.append(tabs[best].loc[d, "net_bp"])
    return np.array(real), picks


if __name__ == "__main__":
    pd.set_option("display.width", 210)
    r = trades()
    print("=" * 76)
    print("STRATEGY v2: size-scaled 2s10s steepener, hold 5 days")
    print("=" * 76)
    print(r[["announce", "issuer", "size10", "scale", "spread_bp", "net_bp"]]
          .assign(**{c: r[c].round(2) for c in ["size10", "scale", "spread_bp", "net_bp"]})
          .to_string(index=False))

    s = stats(r)
    print(f"\n  n={s['n']}  hit {s['hit']:.0%}  mean {s['mean']:+.2f} bp  sd {s['sd']:.2f}")
    print(f"  total {s['total']:+.0f} bp   max drawdown {s['maxdd']:.0f} bp")
    print(f"  t = {s['t']:+.2f}   Sharpe = {s['sharpe']:+.2f}")
    b = boot(r)
    print(f"  bootstrap Sharpe 95% CI [{np.nanpercentile(b,2.5):+.2f}, "
          f"{np.nanpercentile(b,97.5):+.2f}]   P(SR>0) = {np.nanmean(b>0):.2f}")

    print("\n  --- v1 vs v2, like for like ---")
    import strategy as S1
    v1 = S1.stats(S1.pnl_table())
    print(f"    {'':22} {'mean':>8} {'sd':>8} {'t':>7} {'Sharpe':>8}")
    print(f"    {'v1 outright 10Y':22} {v1['mean_bp']:+8.2f} {v1['sd_bp']:8.2f} "
          f"{v1['t']:+7.2f} {v1['sharpe']:+8.2f}")
    print(f"    {'v2 size-scaled 2s10s':22} {s['mean']:+8.2f} {s['sd']:8.2f} "
          f"{s['t']:+7.2f} {s['sharpe']:+8.2f}")
    u = stats(trades(size_scaled=False))
    print(f"    {'v2 without size scale':22} {u['mean']:+8.2f} {u['sd']:8.2f} "
          f"{u['t']:+7.2f} {u['sharpe']:+8.2f}")

    print("\n  --- leave-one-out ---")
    ts = []
    for i in range(len(r)):
        ts.append(stats(r.drop(r.index[i]).reset_index(drop=True))["t"])
    ts = np.array(ts)
    print(f"    t range {ts.min():+.2f} to {ts.max():+.2f}   "
          f"variants with t>2: {(ts>2).sum()} of {len(ts)}")
    x = np.sort(r.net_bp.values)[::-1]
    print(f"    top 3 trades = {x[:3].sum()/r.net_bp.sum():.0%} of total P&L   "
          f"median trade {np.median(r.net_bp):+.1f} bp")

    print("\n  --- walk-forward (holding period from prior events only) ---")
    wf, picks = walk_forward()
    if len(wf) > 1:
        sd = wf.std(ddof=1)
        print(f"    n={len(wf)}  mean {wf.mean():+.2f} bp  sd {sd:.2f}  "
              f"t {wf.mean()/(sd/np.sqrt(len(wf))):+.2f}  hit {np.mean(wf>0):.0%}")
        print(f"    holds chosen: {picks}")

    print("\n  --- cost sensitivity (two legs) ---")
    for c in (0.0, 3.0, 6.0, 12.0):
        st = stats(trades(cost=c))
        print(f"    {c:5.1f} bp: mean {st['mean']:+7.2f}  t {st['t']:+5.2f}  "
              f"Sharpe {st['sharpe']:+5.2f}")
    r.to_csv(PROC / "strategy2_trades.csv", index=False)
