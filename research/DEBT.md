# Code debt

Created during the upgrade. Severity: high (fix before finishing), medium, low.

| # | Item | Where | Severity | Status |
|---|---|---|---|---|
| 1 | The h = 0 local-projection design (y = TP(t) - TP(t-1), shock, four controls) is rebuilt by hand in `headline.py` (h0_inference), `diagnostics.target_lp`, `diagnostics_b48.design` and `b3_tests`. Should come from one function in `localproj.py`. | several | medium | open |
| 2 | Lag-matched placebo drawing is implemented twice: `draw_matched` and `draw_vol_matched` share the exclusion and fallback logic. | `placebo_matched.py` | low | open |
| 3 | Seeds: `diagnostics_b48` uses `RANDOM_SEED + 1` for the lag-only arm, a hardcoded offset. | `diagnostics_b48.py` | low | open |
| 4 | `diagnostics_b48.py` reruns 20,000 fits including median regression, about 15 minutes, and is not cached. | `diagnostics_b48.py` | low | open |
| 5 | `verify_numbers.py` matches values by rounding, so small integers can trace by coincidence. | `verify_numbers.py` | medium | open |
| 6 | No unit tests for any upgrade module (`diagnostics`, `b3_tests`, `cumulative`, `verify_numbers`). The only test file is `test_curve.py`. | src | high | open |
| 7 | `paper_numbers.py` hardcodes `0.123` (the LP reversion) inherited from `variance.py`. | `paper_numbers.py`, `variance.py`, `figures_blog2.py` | medium | open |
| 8 | Trailing 20-day volatility window (20) is hardcoded in four places instead of `config.py`. | `b3_tests`, `diagnostics_b48`, `placebo_matched` | high | open |
