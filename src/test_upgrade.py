"""Tests for the upgrade modules (DEBT.md item 6). Same style as test_curve.py:
run directly, prints PASS/FAIL, exits non-zero on any failure."""
import json, sys
import numpy as np, pandas as pd, statsmodels.api as sm
from config import TAB, RANDOM_SEED

OK = True
def check(name, cond, detail=""):
    global OK
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    OK = OK and bool(cond)


def t_fwl_equals_ols():
    import speccurve as SC
    rng = np.random.default_rng(0)
    n = 300
    C = np.column_stack([np.ones(n), rng.normal(size=(n, 3))])
    x = np.where(rng.random(n) < 0.05, rng.normal(5, 1, n), 0.0)
    y = C @ [0.1, 0.5, -0.2, 0.3] + 0.8 * x + rng.normal(size=n)
    b = SC.fwl_b(y, C, x[:, None])[0]
    ols = sm.OLS(y, np.column_stack([C, x])).fit().params[-1]
    check("Frisch-Waugh coefficient equals OLS", abs(b - ols) < 1e-10, f"{b:.6f} vs {ols:.6f}")


def t_adjustments_bounded():
    import speccurve as SC
    rng = np.random.default_rng(1)
    null = [rng.normal(0, 1, 500) for _ in range(20)]
    t = pd.DataFrame({"b": rng.normal(0.5, 1, 20)})
    a = SC.adjust(t, null)
    check("Romano-Wolf p >= raw p for every spec", bool((a.p_romano_wolf >= a.p_raw - 1e-12).all()))
    check("BH p >= raw p for every spec", bool((a.p_bh >= a.p_raw - 1e-12).all()))
    order = np.argsort(-(a.b.abs() / a.sd_placebo).values)
    check("Romano-Wolf p is monotone in the studentised statistic", bool(np.all(np.diff(a.p_romano_wolf.values[order]) >= -1e-12)))


def t_tenor_weights():
    import tenorlocal as T
    check("weights sum to one", all(abs(T.weights(m).sum() - 1) < 1e-12 for m in (0.5, 2, 4, 10, 15, 30, 40)))
    check("grid point gets all weight", T.weights(10)[T.GRID.index(10)] == 1.0)
    w = T.weights(8.5)
    check("8.5y splits 7y and 10y linearly", abs(w[T.GRID.index(7)] - 0.5) < 1e-12 and abs(w[T.GRID.index(10)] - 0.5) < 1e-12)
    check("beyond 30y is clipped to 30y", T.weights(50)[-1] == 1.0)


def t_placebo_preserves_timing():
    import localproj as L, placebo_matched as PM
    P = L.panel(); sh = L.shocks(); sh = sh[sh.index.isin(P.index)]
    lt = PM.add_vol_tercile(PM.lag_table(P.index), P)
    rng = np.random.default_rng(RANDOM_SEED)
    f = PM.draw_matched(sh, lt, rng)
    check("matched placebo keeps the deal count", len(f) == len(sh))
    check("matched placebo keeps the lag distribution",
          sorted(lt.lag.reindex(f.index)) == sorted(lt.lag.reindex(sh.index)))
    real = [P.index.get_loc(d) for d in sh.index]
    near = min(min(abs(P.index.get_loc(d) - r) for r in real) for d in f.index)
    check("no placebo date within the exclusion band", near > PM.EXCL, f"closest {near}")
    stats = {}
    g = PM.draw_vol_matched(sh, lt, rng, stats=stats)
    check("vol-matched placebo keeps lags", sorted(lt.lag.reindex(g.index)) == sorted(lt.lag.reindex(sh.index)))
    if stats.get("fallback", 0) == 0:
        check("vol-matched placebo keeps terciles", sorted(lt.vol3.reindex(g.index)) == sorted(lt.vol3.reindex(sh.index)))


def t_hac_helpers():
    import diagnostics as D
    u = np.random.default_rng(2).normal(size=5000)
    lrv = D.bartlett_lrv(u, 10)
    check("Bartlett LRV of iid noise is close to its variance", abs(lrv / u.var() - 1) < 0.1, f"ratio {lrv / u.var():.3f}")
    lag = D.nw1994_lags(u)
    check("NW1994 bandwidth is a small non-negative integer for iid noise", isinstance(lag, int) and 0 <= lag < 20, f"{lag}")


def t_number_tools():
    import verify_numbers as V, paper_numbers as PN
    toks = [t for t, *_ in V.tokens("Effect −0.067 on 2026-09-22, p 0.71 and 54% of it.", "x")]
    check("tokens keep signed decimals and percentages", "−0.067" in toks and "54%" in toks and "0.71" in toks, str(toks))
    check("tokens skip ISO dates", not any(t.startswith("2026") for t in toks), str(toks))
    PN.put("t_round", 0.0595, "0.059", "test")
    check("paper_numbers rounding check", PN.OUT["t_round"]["matches"] is True)


def t_dedup_keeps_earliest():
    import expected_supply as E
    c = pd.DataFrame({"date": ["2025-03-01", "2025-01-01", "2025-02-01"]})
    v = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    keep = E.dedup(c, v)
    check("dedup drops the later duplicate and keeps the earliest", list(keep) == [1, 2], str(list(keep)))


def t_headline_reproduced():
    import speccurve as SC
    s = json.loads((TAB / "speccurve_summary.json").read_text())["headline"]["b"]
    h = json.loads((TAB / "headline.json").read_text())["term_premium"]["impact_b0_bp_per_bn"]
    check("spec-curve headline spec equals headline.json", abs(s - h) < 1e-9, f"{s:.6f} vs {h:.6f}")


if __name__ == "__main__":
    for fn in [t_fwl_equals_ols, t_adjustments_bounded, t_tenor_weights, t_placebo_preserves_timing,
               t_hac_helpers, t_number_tools, t_dedup_keeps_earliest, t_headline_reproduced]:
        print(f"\n{fn.__name__}:"); fn()
    print("\n" + ("ALL UPGRADE TESTS PASSED" if OK else "SOME TESTS FAILED"))
    sys.exit(0 if OK else 1)
