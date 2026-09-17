"""Audit 1: effective sample size, NW lag sweep, cluster-by-event."""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC
import regression as R

df = R.dataset()
T = len(df)
x = df["dD"].values
ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
ann = [a for a in ev.announce if a in df.index]

print("=" * 76)
print("EFFECTIVE SAMPLE SIZE  (dep = dTP10, regressor = dD)")
print("=" * 76)
print(f"  nominal T (daily obs)                       : {T}")
print(f"  distinct announcement shocks in sample      : {len(ann)}")
nz = int((np.abs(x) > 1e-9).sum())
print(f"  days with |dD| > 0                          : {nz}")
# how concentrated is the regressor's variation?
v = x ** 2
srt = np.sort(v)[::-1]
for k in (16, 32, 64):
    print(f"  share of sum(dD^2) in top {k:3d} days          : {srt[:k].sum()/v.sum():.3f}")

# Kish effective n from the regressor weights (variance of OLS slope is driven by x^2)
kish = (v.sum() ** 2) / (v ** 2).sum()
print(f"  Kish effective n from dD^2 weights          : {kish:.1f}")

# autocorrelation-adjusted N_eff on the score x_t*e_t
m6 = R.run(df, supply="dD", regime=False)
e = m6.resid.values
s = x * e
rho = [pd.Series(s).autocorr(k) for k in range(1, 21)]
neff_score = T / (1 + 2 * np.nansum(rho))
print(f"  N_eff from score autocorrelation (20 lags)  : {neff_score:.0f}")
rx = pd.Series(x).autocorr(1)
print(f"  AR(1) of dD = {rx:.3f} -> N_eff = T(1-r)/(1+r) : {T*(1-rx)/(1+rx):.0f}")
print("\n  Honest read: the regressor carries 16 independent shocks. Everything")
print("  else is deterministic decay. Treat inference as N~16, not T~673.")

print("\n" + "=" * 76)
print("NEWEY-WEST LAG SWEEP  (dTP10 ~ dD + controls)")
print("=" * 76)
X = sm.add_constant(df[["dD"] + R.CTRL])
y = df["dTP10"]
print(f"  {'lags':>6} {'coef':>10} {'se':>9} {'t':>7} {'p':>8}")
base = sm.OLS(y, X).fit()
print(f"  {'OLS':>6} {base.params['dD']:10.4f} {base.bse['dD']:9.4f} "
      f"{base.tvalues['dD']:7.2f} {base.pvalues['dD']:8.4f}")
for L in (0, 2, 5, 6, 10, 20, 40):
    m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": L, "use_correction": True})
    print(f"  {L:6d} {m.params['dD']:10.4f} {m.bse['dD']:9.4f} "
          f"{m.tvalues['dD']:7.2f} {m.pvalues['dD']:8.4f}")

print("\n" + "=" * 76)
print("CLUSTER BY EVENT EPISODE")
print("=" * 76)
# every day belongs to the episode of the most recent announcement
cut = pd.Series(0, index=df.index)
for i, a in enumerate(sorted(ann), start=1):
    cut[df.index >= a] = i
print(f"  clusters (episodes): {cut.nunique()}   sizes: "
      f"min {cut.value_counts().min()}, median {int(cut.value_counts().median())}, max {cut.value_counts().max()}")
mc = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": cut.values})
print(f"  cluster-robust: coef={mc.params['dD']:.4f} se={mc.bse['dD']:.4f} "
      f"t={mc.tvalues['dD']:.2f} p={mc.pvalues['dD']:.4f}")

# wild cluster bootstrap (Rademacher), imposing the null
rng = np.random.default_rng(20261015)
Xr = X.drop(columns="dD")
r0 = sm.OLS(y, Xr).fit()
u0 = r0.resid.values
fit0 = r0.fittedvalues.values
groups = cut.values
uniq = np.unique(groups)
tb = []
for b in range(2000):
    w = rng.choice([-1.0, 1.0], size=len(uniq))
    wm = pd.Series(w, index=uniq).reindex(groups).values
    yb = fit0 + u0 * wm
    mb = sm.OLS(yb, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
    tb.append(mb.tvalues["dD"])
tb = np.array(tb)
tobs = mc.tvalues["dD"]
print(f"  wild cluster bootstrap (2000 reps, null imposed): "
      f"p = {np.mean(np.abs(tb) >= abs(tobs)):.4f}   "
      f"boot t 2.5/97.5 pct = [{np.percentile(tb,2.5):.2f}, {np.percentile(tb,97.5):.2f}]")
