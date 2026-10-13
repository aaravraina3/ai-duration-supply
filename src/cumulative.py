"""P1 in research/11_UPGRADE_PREREG.md: the pooled early response.

S = (b_0 + b_1 + b_2) / 3 from the local projections, tested against the
timing-matched placebo. Each draw recomputes all three coefficients on the same
placebo dates, so the placebo keeps the correlation between horizons that the
real path has. Registered in commit e469395 before this ran.
"""
import json
import numpy as np, pandas as pd
from config import RANDOM_SEED, TAB
import localproj as L, placebo_matched as PM

H = (0, 1, 2)


def pooled(panel, shocks):
    lp = L.project(panel, shocks, dep="TP10", hmax=max(H))
    return float(lp[lp.h.isin(H)].b.mean())


def main(n=PM.N_DRAW):
    p = L.panel()
    sh = L.shocks(); sh = sh[sh.index.isin(p.index)]
    lt = PM.lag_table(p.index)
    s_obs = pooled(p, sh)
    rng = np.random.default_rng(RANDOM_SEED)
    out = {"statistic": "mean of b_0, b_1, b_2", "registered_in": "e469395", "S_obs": s_obs}
    for name, draw in [("matched on lag", lambda: PM.draw_matched(sh, lt, rng)),
                       ("uniform", lambda: PM.draw_uniform(sh, lt, rng))]:
        s = np.array([pooled(p, draw()) for _ in range(n)])
        out[name] = dict(draws=n, mean=float(s.mean()), sd=float(s.std()),
                         p_two_sided=float(np.mean(np.abs(s) >= abs(s_obs))),
                         p_one_sided=float(np.mean(s >= s_obs)))
        print(f"{name:16s} mean {s.mean():+.4f} sd {s.std():.4f}  "
              f"p two-sided {out[name]['p_two_sided']:.4f}  one-sided {out[name]['p_one_sided']:.4f}")
    print(f"S_obs = {s_obs:+.4f}")
    (TAB / "pooled_early_response.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
