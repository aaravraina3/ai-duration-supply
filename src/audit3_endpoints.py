"""Audit 3: what is the Meta 2024-08-07 event, and endpoint sensitivity."""
import numpy as np, pandas as pd
from config import PROC

fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")

print("=" * 78)
print("CONTEXT AROUND THE EVENT THAT DRIVES X  (Meta, 2024-08-07)")
print("=" * 78)
w = fred.loc["2024-07-29":"2024-08-16", ["DGS2", "DGS10", "DGS30", "VIXCLS", "T10YIE"]]
print(w.to_string())
print(f"\n  VIX 2024-08-05 = {fred.loc['2024-08-05','VIXCLS']:.2f}  "
      f"(sample max = {fred.loc['2024-01-01':'2026-09-16','VIXCLS'].max():.2f} on "
      f"{fred.loc['2024-01-01':'2026-09-16','VIXCLS'].idxmax().date()})")
v = fred.loc["2024-01-01":"2026-09-16", "VIXCLS"].dropna()
print(f"  VIX percentile on 2024-08-07: {(v < fred.loc['2024-08-07','VIXCLS']).mean():.1%}")
print("  This event sits inside the August 2024 yen-carry unwind.")

print("\n" + "=" * 78)
print("ENDPOINT SENSITIVITY: 2026 decomposition")
print("=" * 78)
starts = ["2026-01-02", "2026-01-15", "2026-02-02", "2026-02-27", "2025-12-31"]
ends = ["2026-09-15", "2026-08-31", "2026-06-30", "2026-09-11", "2026-07-31"]
s10 = fred.DGS10.dropna(); tp = acm.ACMTP10.dropna(); rn = acm.ACMRNY10.dropna()

def at(s, d):
    d = pd.Timestamp(d)
    ss = s[s.index <= d]
    return ss.iloc[-1], ss.index[-1]

print(f"  {'start':>12} {'end':>12} {'dY10':>8} {'dTP':>8} {'dExp':>8} {'TP sign':>8}")
rows = []
for st in starts:
    for en in ends:
        if pd.Timestamp(en) <= pd.Timestamp(st): continue
        y0, _ = at(s10, st); y1, _ = at(s10, en)
        t0, _ = at(tp, st);  t1, _ = at(tp, en)
        r0, _ = at(rn, st);  r1, _ = at(rn, en)
        dY, dT, dR = (y1-y0)*100, (t1-t0)*100, (r1-r0)*100
        rows.append(dict(start=st, end=en, dY=dY, dTP=dT, dExp=dR))
        print(f"  {st:>12} {en:>12} {dY:8.1f} {dT:8.1f} {dR:8.1f} {'+' if dT>0 else '-':>8}")
r = pd.DataFrame(rows)
print(f"\n  dTP range across {len(r)} endpoint pairs: {r.dTP.min():+.1f} to {r.dTP.max():+.1f} bp")
print(f"  pairs with dTP > 0: {int((r.dTP>0).sum())} of {len(r)}")
print(f"  dY range: {r.dY.min():+.1f} to {r.dY.max():+.1f} bp")
print(f"  in EVERY pair, |dExp| > |dTP|: {bool((r.dExp.abs() > r.dTP.abs()).all())}")

print("\n  trailing-12m window (not calendar 2026):")
y0,_ = at(s10,"2025-09-15"); y1,_ = at(s10,"2026-09-15")
t0,_ = at(tp,"2025-09-15");  t1,_ = at(tp,"2026-09-15")
r0,_ = at(rn,"2025-09-15");  r1,_ = at(rn,"2026-09-15")
print(f"    2025-09-15 -> 2026-09-15: dY={(y1-y0)*100:+.1f}  dTP={(t1-t0)*100:+.1f}  dExp={(r1-r0)*100:+.1f}")
y0,_ = at(s10,"2024-01-02"); t0,_ = at(tp,"2024-01-02"); r0,_ = at(rn,"2024-01-02")
print(f"    full sample 2024-01-02 -> 2026-09-15: dY={(y1-y0)*100:+.1f}  "
      f"dTP={(t1-t0)*100:+.1f}  dExp={(r1-r0)*100:+.1f}")
print(f"\n  ACM TP10 level: 2026 min {tp[tp.index>='2026-01-01'].min():.3f} "
      f"max {tp[tp.index>='2026-01-01'].max():.3f} last {tp.iloc[-1]:.3f}")
