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
| 9 | Placebo draw streams differ by script, so the same placebo test gives p 0.0705 in `speccurve.py` and 0.0825 in `placebo_matched.py`. Each test should own a dedicated generator. | `placebo_matched.py`, `speccurve.py` | medium | open |
| 10 | `speccurve.py` fills the placebo shock matrix with a Python loop over 2000 draws per spec. Vectorisable. | `speccurve.py` | low | open |
| 11 | `oos_forecast.py` aligns the volatility series to the forecast errors by position (`WARM:WARM+len(y)`), which assumes the valid-forecast mask is contiguous. Should align on the index. | `oos_forecast.py` | medium | open |
| 12 | `altdv.panel()` is imported by `timing.py` and `tenorlocal.py`, and `speccurve` helpers (`deal_table`, `draw_assignments`, `fwl_b`) are imported by four modules. They belong in a shared module, not in the B9 script. | `speccurve.py` and importers | medium | open |
| 13 | `expected_supply.py` re-embeds the whole corpus on every run (about 2 minutes plus a 420MB model). Cache the embeddings. | `expected_supply.py` | low | open |
| 14 | `timing.py` power simulation runs about 200,000 logit fits. | `timing.py` | low | open |
