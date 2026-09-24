# Retired modules

Kept so every number that ever appeared in a writeup can be regenerated, but no
longer part of the pipeline and nothing in `src/` depends on them.

| Module | Why it was retired |
|---|---|
| `nlp.py`, `nlp_fetch.py` | TF-IDF plus SVD supply-pressure index. 716 effectively distinct passages after 0.90 dedup, wrong-signed coefficient (t = -1.20), beaten by a plain decayed passage count (t = +2.86). |
| `audit6_nlp_real.py` | The audit that showed the above. |
| `regime.py` | Three-state HMM on curve factors. States are volatility clocks with 2-12 day dwell times, breakevens co-move with yields at ~0.6 in every state, and BIC cannot separate K=2 from K=3. It also silently truncated the main regression at 2026-09-11 through a stale posterior file. |

Run from the repo `src/` directory, e.g. `../.venv/bin/python archive/nlp.py`.
