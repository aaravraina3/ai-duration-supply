"""Timing-matched placebo for the announcement effect. Fixes review item M1.

THE PROBLEM
Every placebo in this project drew fake event dates uniformly from non-event
days. But real deals are not uniform in time: 8 of the 11 jumbos the macro filter
dropped priced 1-3 business days AFTER an FOMC decision, CPI print or payrolls
release. Treasurers wait for the print, then issue into the quiet behind it.

If yields drift in the days after macro releases (a documented pattern), real
deal days inherit that drift and uniform placebo days do not. Then the
randomization p = 0.069 could be measuring post-macro drift, not supply.

THE FIX
For every trading day, compute its lag: business days since the most recent
macro release on or before it. Each real deal has a lag. For each placebo draw,
replace every real deal with a date that has the SAME lag, drawn from days not
within five sessions of any real deal, and give it the real deal's size. The
placebo then shares the real events' timing structure exactly.

PREDICTION, written before running
If the AI effect is post-macro drift, the matched placebo distribution shifts
toward the observed coefficient: its mean moves up from ~0 and the p-value rises.
If the effect is about supply, the matched placebo stays centred near zero and
the p-value is roughly unchanged.

ROBUSTNESS
Primary match is on lag alone. Secondary match is on (lag, type of the most
recent release), which is stricter but leaves fewer candidate dates per cell.
"""
import numpy as np, pandas as pd
from config import PROC, RANDOM_SEED
import localproj as L

N_DRAW = 2000
EXCL = 5          # sessions around real events that placebo dates may not use


def lag_table(idx):
    cal = pd.read_csv(PROC / "macro_calendar.csv", parse_dates=["date"])
    cal = cal[cal.date.isin(idx)].sort_values("date")
    pos = {d: i for i, d in enumerate(idx)}
    rel_pos = np.array([pos[d] for d in cal.date])
    rel_kind = cal.kind.values
    lag, kind = np.full(len(idx), -1), np.array([""] * len(idx), dtype=object)
    for i in range(len(idx)):
        k = np.searchsorted(rel_pos, i, side="right") - 1
        if k >= 0:
            lag[i] = i - rel_pos[k]
            kind[i] = rel_kind[k]
    return pd.DataFrame({"lag": lag, "kind": kind}, index=idx)


def draw_matched(shocks, lt, rng, by_kind=False, excl=EXCL, tail=6):
    idx = lt.index
    real_pos = [idx.get_loc(d) for d in shocks.index]
    banned = set()
    for p in real_pos:
        banned |= set(range(max(0, p - excl), min(len(idx), p + excl + 1)))
    ok = np.array([i not in banned and i < len(idx) - tail for i in range(len(idx))])
    out, used = [], set()
    for d, size in shocks.items():
        p = idx.get_loc(d)
        m = ok & (lt.lag.values == lt.lag.values[p])
        if by_kind:
            m &= (lt.kind.values == lt.kind.values[p])
        cand = [i for i in np.flatnonzero(m) if i not in used]
        if not cand:                       # empty cell: fall back to lag-only match
            cand = [i for i in np.flatnonzero(ok & (lt.lag.values == lt.lag.values[p]))
                    if i not in used]
        j = rng.choice(cand)
        used.add(j)
        out.append((idx[j], size))
    return pd.Series(dict(out)).groupby(level=0).sum()


def draw_uniform(shocks, lt, rng, excl=EXCL, tail=6):
    idx = lt.index
    banned = set()
    for d in shocks.index:
        p = idx.get_loc(d)
        banned |= set(range(max(0, p - excl), min(len(idx), p + excl + 1)))
    pool = [i for i in range(len(idx)) if i not in banned and i < len(idx) - tail]
    pick = rng.choice(pool, size=len(shocks), replace=False)
    return pd.Series(shocks.values, index=idx[pick]).groupby(level=0).sum()


def run(h=0, n=N_DRAW, seed=RANDOM_SEED):
    p = L.panel()
    sh = L.shocks()
    sh = sh[sh.index.isin(p.index)]
    lt = lag_table(p.index)
    obs = L.project(p, sh, dep="TP10", hmax=h)
    b_obs = obs[obs.h == h].iloc[0].b
    rng = np.random.default_rng(seed)
    res = {}
    for name, fn in [("uniform", lambda: draw_uniform(sh, lt, rng)),
                     ("matched on lag", lambda: draw_matched(sh, lt, rng)),
                     ("matched on lag and release type",
                      lambda: draw_matched(sh, lt, rng, by_kind=True))]:
        b = []
        for _ in range(n):
            f = fn()
            r = L.project(p, f, dep="TP10", hmax=h)
            b.append(r[r.h == h].iloc[0].b)
        res[name] = np.array(b)
    return b_obs, res, sh, lt


if __name__ == "__main__":
    p = L.panel()
    sh = L.shocks(); sh = sh[sh.index.isin(p.index)]
    lt = lag_table(p.index)
    real = lt.loc[sh.index]
    print("=" * 76)
    print("TIMING OF THE 16 REAL DEALS RELATIVE TO THE LAST MACRO RELEASE")
    print("=" * 76)
    print(real.assign(size10=sh.round(1)).to_string())
    print(f"\n  lag distribution of real deals : {real.lag.value_counts().sort_index().to_dict()}")
    print(f"  lag distribution of all days   : "
          f"{lt.lag.value_counts().sort_index().head(8).to_dict()} ...")

    # is there post-release drift in the term premium at all?
    d = (p.TP10.shift(0) - p.TP10.shift(1)).rename("dTP")
    drift = pd.concat([d, lt], axis=1).dropna()
    print("\n  mean dTP10 by lag (is there post-release drift to inherit?):")
    for k in range(0, 6):
        s = drift[drift.lag == k].dTP
        print(f"    lag {k}: mean {s.mean():+.3f} bp  sd {s.std():.2f}  n={len(s)}")

    rows = []
    for h in (0, 2, 5):
        b_obs, res, _, _ = run(h=h)
        print("\n" + "=" * 76)
        print(f"PLACEBO COMPARISON, h = {h}   observed b = {b_obs:+.4f}")
        print("=" * 76)
        for name, b in res.items():
            pv = float(np.mean(np.abs(b) >= abs(b_obs)))
            print(f"  {name:34s} mean {b.mean():+.4f}  sd {b.std():.4f}  p = {pv:.4f}")
            rows.append(dict(h=h, placebo=name, b_obs=b_obs, mean=b.mean(), sd=b.std(), p=pv))
            if h == 0:
                np.save(PROC / f"placebo_{name.replace(' ', '_')}.npy", b)
    pd.DataFrame(rows).to_csv(PROC / "placebo_matched.csv", index=False)
