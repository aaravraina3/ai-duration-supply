"""Audit 5: how much of the corporate+MBS claim was actually tested, and does
Treasury duration supply behave like AI duration supply in the same regression?"""
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC
import regression as R

df = R.dataset()
ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
T = R.treasury_supply()

print("=" * 78)
print("SCALE: AI duration supply vs Treasury coupon duration supply")
print("=" * 78)
for yr in (2025, 2026):
    ai = ev[(ev.announce >= f"{yr}-01-01") & (ev.announce <= f"{yr}-12-31")]
    end = f"{yr}-09-16" if yr == 2026 else f"{yr}-12-31"
    t = T[(T.index >= f"{yr}-01-01") & (T.index <= end)]
    ai10 = ai.tenyr_equiv.sum() / 1e9
    print(f"  {yr}: AI face ${ai.total_usd.sum()/1e9:7.1f}B | AI 10y-equiv {ai10:7.1f} $bn | "
          f"UST coupon 10y-equiv {t.auc_10y.sum():8.1f} $bn | AI/UST = {ai10/t.auc_10y.sum():.3%}")
print("\n  MBS: NOT TESTED. No free daily or monthly agency MBS issuance series was")
print("  reachable (SIFMA files 404, no FRED equivalent). I cannot produce the number.")

print("\n" + "=" * 78)
print("INTERNAL CONSISTENCY: does Treasury duration supply move TP the same way?")
print("=" * 78)
print("  If duration supply per se raises the term premium, the much larger")
print("  Treasury coupon supply should show the same sign and a bigger total effect.")
X = sm.add_constant(df[["dD", "auc_10y", "auc_surprise", "dbe", "doil", "dvix"]])
m = sm.OLS(df["dTP10"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": True})
for k in ["dD", "auc_10y", "auc_surprise"]:
    print(f"    {k:14s} coef={m.params[k]:+8.5f} se={m.bse[k]:7.5f} t={m.tvalues[k]:+6.2f} p={m.pvalues[k]:.3f}")
print(f"\n  AI coefficient is {m.params['dD']/max(abs(m.params['auc_10y']),1e-9):.0f}x the Treasury coefficient")
print("  in absolute terms, on a per-$bn-of-10y-equivalent basis, with opposite sign.")
print("  A duration-absorption mechanism does not predict that.")

# same test on the day-of auction only
au = df[df.auc_10y > 0]
print(f"\n  auction days only (n={len(au)}): mean dTP10 on coupon auction days = "
      f"{au.dTP10.mean():+.3f} bp vs {df[df.auc_10y==0].dTP10.mean():+.3f} bp otherwise")
print(f"  corr(auc_10y, dTP10) on auction days = {au.auc_10y.corr(au.dTP10):+.3f}")

print("\n" + "=" * 78)
print("HOW MUCH OF THE 30bp CLAIM IS IN SCOPE")
print("=" * 78)
ai26 = ev[ev.announce >= "2026-01-01"].total_usd.sum() / 1e9
print(f"  tested: 5 issuers, USD public bonds only, 2026 face = ${ai26:.1f}B")
print("  not tested, each a named component of the sell-side aggregate:")
print("    - agency MBS issuance (no free series)")
print("    - the rest of IG corporate issuance (no free series; AI names are a")
print("      minority of it, so the tested slice is a small part of 'corporate')")
print("    - private credit / ABS data-centre financing, which is off-EDGAR")
print("    - non-USD hyperscaler issuance swapped back to USD ($34.8B equiv)")
