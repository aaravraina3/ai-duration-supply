"""B10: minimum detectable effect by number of events.

Anchored on the timing-matched placebo sd of the h = 0 coefficient at 16 deals
(placebo_matched.csv), scaled by sqrt(16 / n), the same scaling as the holdout
power table in research/10_PREREGISTRATION.md. One-sided alpha 0.05, matching the
holdout test.
"""
import json
import numpy as np, pandas as pd
from scipy import stats
from config import PROC, TAB, FIG

ALPHA = 0.05


def main():
    pm = pd.read_csv(PROC / "placebo_matched.csv")
    sd16 = float(pm[(pm.h == 0) & (pm.placebo == "matched on lag")].sd.iloc[0])
    b_obs = float(pm[(pm.h == 0)].b_obs.iloc[0])
    n = np.arange(16, 101)
    za = stats.norm.ppf(1 - ALPHA)
    rows = [dict(n=int(k), se=sd16 * np.sqrt(16 / k),
                 mde80=(za + stats.norm.ppf(0.80)) * sd16 * np.sqrt(16 / k),
                 mde95=(za + stats.norm.ppf(0.95)) * sd16 * np.sqrt(16 / k)) for k in n]
    t = pd.DataFrame(rows)
    t.to_csv(TAB / "power_mde.csv", index=False)
    pick = t.set_index("n").loc[[16, 32, 100]]
    out = dict(anchor_sd_at_16=sd16, alpha_one_sided=ALPHA, observed_b=b_obs,
               mde80={str(k): float(v) for k, v in pick.mde80.items()},
               mde95={str(k): float(v) for k, v in pick.mde95.items()},
               power_at_observed_b={str(k): float(stats.norm.cdf(b_obs / (sd16 * np.sqrt(16 / k)) - za))
                                    for k in (16, 32, 100)})
    (TAB / "power_summary.json").write_text(json.dumps(out, indent=2))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ax.plot(t.n, t.mde80, color="#1f4e79", label="MDE, 80% power")
    ax.plot(t.n, t.mde95, color="#1f4e79", ls="--", label="MDE, 95% power")
    ax.axhline(b_obs, color="#c0392b", lw=1, label=f"in-sample estimate {b_obs:+.3f}")
    ax.axvline(32, color="k", ls=":", lw=1, label="holdout gate, 32 deals")
    ax.set_xlabel("number of deals"); ax.set_ylabel("bp per $bn 10y-equiv")
    ax.set_title("Smallest day-0 effect the design can detect (one-sided 5%)", fontsize=9)
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "power_mde.png", dpi=140); plt.close(fig)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
