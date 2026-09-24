"""Pre-registered held-out test. Review items F2 and M7.

Every result in this project was produced by searching over specifications on
2024-2026 data, and no correction survives that search. The only repair is a
test on data the project has never touched, with the specification frozen before
the data exists. This file is that test. See research/10_PREREGISTRATION.md.

RULES THIS FILE ENFORCES
- Only deals announced on or after HOLDOUT_START enter the shock series.
- Only trading days on or after HOLDOUT_START enter the regression, so the
  control sample is out-of-sample too.
- Nothing is reported as a test until at least N_MIN held-out deals exist. Below
  that it prints the count and stops, so there is nothing to peek at.
- The frozen parameters are hashed. The hash is recorded in the preregistration
  document. If this file's FROZEN dict changes, the hash changes, and the test is
  no longer the registered one.
"""
import hashlib, json, sys
import numpy as np, pandas as pd
from config import PROC, RANDOM_SEED
import localproj as L
import placebo_matched as PM

FROZEN = {
    "hypothesis": "announced USD duration supply from the five issuers raises the "
                  "10Y term premium on the announcement day",
    "holdout_start": "2026-09-24",
    "universe": "USD bond deals, issuers Amazon Alphabet Meta Microsoft Oracle, all sizes",
    "shock": "10-year-equivalent duration announced, $bn, dated by FWP trade date",
    "dependent": "ACM TP10, h-day change TP(t+h) - TP(t-1), bp",
    "horizon": 0,
    "controls": ["dbe", "doil", "dvix", "auc_10y"],
    "inference": "timing-matched randomization (placebo dates at the same lag after the "
                 "last FOMC/CPI/NFP release), 2000 draws",
    "test": "one-sided, H1: b > 0",
    "alpha": 0.05,
    "n_min": 32,          # 80% one-sided power at b = 0.081, given the matched-placebo sd
    "decision": "reject H0 if p < 0.05. Report the point estimate and p regardless. "
                "A failure to reject at n_min is reported as a failure, not extended.",
}
N_MIN = FROZEN["n_min"]


def spec_hash():
    return hashlib.sha256(json.dumps(FROZEN, sort_keys=True).encode()).hexdigest()[:16]


def main():
    print("=" * 72)
    print("PRE-REGISTERED HELD-OUT TEST")
    print("=" * 72)
    print(f"  spec hash {spec_hash()}  (must match research/10_PREREGISTRATION.md)")
    start = pd.Timestamp(FROZEN["holdout_start"])
    deals = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    new = deals[deals.announce >= start]
    print(f"  held-out deals announced since {start.date()}: {len(new)}  (need {N_MIN})")
    if len(new) < N_MIN:
        print("  NOT EVALUATED. Nothing to report until the minimum is reached.")
        print("  Refresh the event list (edgar_list, edgar_fetch, eventlist) as deals")
        print("  arrive; do not change FROZEN.")
        return
    p = L.panel()
    p = p[p.index >= start]
    sh = (new.groupby("announce").tenyr_equiv.sum() / 1e9)
    sh = sh[sh.index.isin(p.index)]
    r = L.project(p, sh, dep="TP10", hmax=FROZEN["horizon"], ctrl=tuple(FROZEN["controls"]))
    b = float(r[r.h == FROZEN["horizon"]].iloc[0].b)
    lt = PM.lag_table(p.index)
    rng = np.random.default_rng(RANDOM_SEED)
    draws = []
    for _ in range(2000):
        f = PM.draw_matched(sh, lt, rng)
        rr = L.project(p, f, dep="TP10", hmax=FROZEN["horizon"], ctrl=tuple(FROZEN["controls"]))
        draws.append(rr[rr.h == FROZEN["horizon"]].iloc[0].b)
    d = np.array(draws)
    pval = float(np.mean(d >= b))                     # one-sided, as registered
    print(f"  b = {b:+.4f} bp per $bn   one-sided p = {pval:.4f}   n = {len(sh)}")
    print(f"  decision: {'REJECT H0' if pval < FROZEN['alpha'] else 'FAIL TO REJECT'}")


if __name__ == "__main__":
    if "--hash" in sys.argv:
        print(spec_hash())
    else:
        main()
