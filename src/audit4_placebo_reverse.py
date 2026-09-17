"""Audit 4: placebo on the local projection, and reverse causality."""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, RANDOM_SEED
import localproj as L

df = L.panel()
sh = L.shocks()
rng = np.random.default_rng(RANDOM_SEED)
idx = df.index

print("=" * 78)
print("PLACEBO ON THE LOCAL PROJECTION (randomised announcement dates, sizes kept)")
print("=" * 78)
real = set()
for a in sh.index:
    p = idx.searchsorted(a)
    real |= {idx[j] for j in range(max(0, p - 5), min(len(idx), p + 6))}
pool = np.array([i for i, d in enumerate(idx) if d not in real and 5 < i < len(idx) - 65])
sizes = sh.values
NDRAW = 1000
for h in (0, 2, 5):
    obs = L.project(df, sh, dep="TP10", hmax=h)
    bobs = obs[obs.h == h].iloc[0].b
    draws = []
    for _ in range(NDRAW):
        pick = rng.choice(pool, size=len(sizes), replace=False)
        fake = pd.Series(sizes, index=idx[pick]).groupby(level=0).sum()
        lp = L.project(df, fake, dep="TP10", hmax=h)
        draws.append(lp[lp.h == h].iloc[0].b)
    d = np.array(draws)
    print(f"  h={h}: observed b={bobs:+.4f} | placebo mean={d.mean():+.4f} sd={d.std():.4f} "
          f"95% CI [{np.percentile(d,2.5):+.4f},{np.percentile(d,97.5):+.4f}] "
          f"p={np.mean(np.abs(d)>=abs(bobs)):.4f}")

print("\n" + "=" * 78)
print("REVERSE CAUSALITY: do yields predict issuance timing?")
print("=" * 78)
fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
y = fred.DGS10.reindex(idx).ffill()
v = fred.VIXCLS.reindex(idx).ffill()
X = pd.DataFrame(index=idx)
X["d5"] = (y - y.shift(5)) * 100
X["d20"] = (y - y.shift(20)) * 100
X["pctile60"] = y.rolling(60).apply(lambda s: (s.iloc[-1] > s).mean(), raw=False)
X["vix"] = v
X["lvl"] = y
X["issue"] = 0
for a in sh.index:
    if a in X.index: X.loc[a, "issue"] = 1
X = X.dropna()
print(f"  n={len(X)}, issuance days={int(X.issue.sum())}")
print(f"\n  {'variable':>10} {'mean|issue=1':>13} {'mean|issue=0':>13} {'t':>7} {'p':>7}")
from scipy import stats
for c in ["d5", "d20", "pctile60", "vix", "lvl"]:
    a, b = X[X.issue == 1][c], X[X.issue == 0][c]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    print(f"  {c:>10} {a.mean():13.3f} {b.mean():13.3f} {t:7.2f} {p:7.3f}")
lg = sm.Logit(X.issue, sm.add_constant(X[["d5", "d20", "pctile60", "vix"]])).fit(disp=0)
print("\n  logit P(announce) on pre-announcement rate conditions:")
for k in lg.params.index:
    print(f"    {k:12s} coef={lg.params[k]:+8.4f} z={lg.tvalues[k]:+6.2f} p={lg.pvalues[k]:.3f}")
print(f"    pseudo-R2 = {lg.prsquared:.4f}, LR p = {lg.llr_pvalue:.4f}")

print("\n  path of the 10Y in the 10 bdays BEFORE announcement (bp, vs t-10):")
paths = []
for a in sh.index:
    p = idx.searchsorted(a)
    if p < 11 or p + 6 > len(idx): continue
    seg = (y.iloc[p-10:p+6].values - y.iloc[p-10]) * 100
    paths.append(seg)
P = np.array(paths)
lab = [f"t{k:+d}" for k in range(-10, 6)]
print("   " + " ".join(f"{l:>6}" for l in lab))
print("   " + " ".join(f"{x:6.1f}" for x in P.mean(0)))
allp = []
for i in range(11, len(idx) - 6):
    allp.append((y.iloc[i-10:i+6].values - y.iloc[i-10]) * 100)
A = np.array(allp)
print("   unconditional mean for comparison:")
print("   " + " ".join(f"{x:6.1f}" for x in np.nanmean(A, 0)))
d0 = P[:, 10] - P[:, 0]
a0 = A[:, 10] - A[:, 0]
t, p = stats.ttest_ind(d0, a0[~np.isnan(a0)], equal_var=False)
print(f"\n  10Y change over t-10 to t: issuance days {np.nanmean(d0):+.1f}bp vs "
      f"all days {np.nanmean(a0):+.1f}bp, t={t:.2f}, p={p:.3f}")
