"""Audit 2: event independence and leave-one-out."""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC
import localproj as L, abnormal as A, concession as K, curve as C

df = L.panel()
allsh = L.shocks()
ev7 = pd.read_csv(PROC / "events.csv", parse_dates=["announce"])
tr = pd.read_csv(PROC / "tranches.csv", parse_dates=["announce"])

print("=" * 78)
print("OVERLAPPING SHOCKS IN THE LOCAL-PROJECTION SET (all 16 USD deals)")
print("=" * 78)
d = sorted(allsh.index)
for a, b in zip(d[:-1], d[1:]):
    gap = len(pd.bdate_range(a, b)) - 1
    if gap <= 5:
        print(f"  {a.date()} -> {b.date()}: {gap} bdays  OVERLAPS h<=5 window")

def b_at(sh, h=0, dep="TP10"):
    lp = L.project(df, sh, dep=dep, hmax=h)
    r = lp[lp.h == h].iloc[0]
    return r.b, r.t, r.n

print("\n" + "=" * 78)
print("LOCAL PROJECTION h=0, DROPPING PROBLEM OBSERVATIONS")
print("=" * 78)
b, t, n = b_at(allsh)
print(f"  {'baseline (16 shocks)':46s} b={b:+.4f} t={t:5.2f}")
drops = {
    "drop 2026-02-09 (5 bdays after Oracle 02-02)": ["2026-02-09"],
    "drop 2026-02-02 (keep Alphabet 02-09)":        ["2026-02-02"],
    "drop 2025-11-03 (2 bdays after Meta 10-30)":   ["2025-11-03"],
    "drop 2026-05-05 (3 bdays after Meta 04-30)":   ["2026-05-05"],
    "drop ALL 3 second-of-pair deals":              ["2026-02-09", "2025-11-03", "2026-05-05"],
    "drop 2024-08-07 (only pre-2025 obs)":          ["2024-08-07"],
    "2025+ only":                                   ["2024-08-07", "2024-09-25"],
}
for lab, dd in drops.items():
    s = allsh.drop([pd.Timestamp(x) for x in dd], errors="ignore")
    b, t, n = b_at(s)
    print(f"  {lab:46s} b={b:+.4f} t={t:5.2f}  (n_shocks={len(s)})")

print("\n" + "=" * 78)
print("LEAVE-ONE-OUT: local projection h=0, drop each of the 16 deals")
print("=" * 78)
rows = []
for a in allsh.index:
    s = allsh.drop(a)
    b, t, n = b_at(s)
    rows.append((str(a.date()), allsh[a], b, t))
r = pd.DataFrame(rows, columns=["dropped", "size_10y_bn", "b", "t"]).sort_values("b")
print(r.to_string(index=False, float_format=lambda v: f"{v:8.4f}"))
print(f"\n  range of b: {r.b.min():+.4f} to {r.b.max():+.4f}  (baseline +0.0803)")
print(f"  range of t: {r.t.min():5.2f} to {r.t.max():5.2f}")
print(f"  min |t| across LOO: {r.t.abs().min():.2f} -> "
      f"{'survives' if r.t.abs().min() > 1.96 else 'DOES NOT survive'} at 5% in every LOO fit")

print("\n" + "=" * 78)
print("LEAVE-ONE-OUT: X (time-series abnormal), drop each of the 7 events")
print("=" * 78)
dfa, tn = A.panel(); W = A.build_windows(dfa, tn)
res, det, models, est = A.abnormal(ev7, tr, W, verbose=False)
base = A.agg(res)
print(f"  baseline X = {base['mean']:+.3f} bp, t={base['t']:+.2f}")
rows = []
for i in range(len(ev7)):
    sub = ev7.drop(ev7.index[i]).reset_index(drop=True)
    r2, _, _, _ = A.abnormal(sub, tr, W, verbose=False)
    a2 = A.agg(r2)
    rows.append((str(ev7.announce[i].date()), ev7.issuer[i],
                 float(res.abn_bp[i]), a2["mean"], a2["t"]))
q = pd.DataFrame(rows, columns=["dropped", "issuer", "own_abn_bp", "X_wo", "t_wo"]).sort_values("X_wo")
print(q.to_string(index=False, float_format=lambda v: f"{v:8.3f}"))
print(f"\n  range of X: {q.X_wo.min():+.3f} to {q.X_wo.max():+.3f} bp  (baseline {base['mean']:+.3f})")
print(f"  range of t: {q.t_wo.min():+.2f} to {q.t_wo.max():+.2f}")
