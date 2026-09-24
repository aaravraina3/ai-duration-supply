"""Is the supply-pressure index measuring text, or just counting filings?"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np, pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from config import PROC, NLP_HALFLIFE_DAYS
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import nlp as N

idx, d, (pi, qi), (ndrop, nf), svd = N.build()
lam = np.log(2) / NLP_HALFLIFE_DAYS
daily = idx.index
dd = d.date.values.astype("datetime64[D]").astype(int)

def decay_agg(w):
    out = []
    for t in daily:
        ti = np.datetime64(t.date()).astype(int)
        m = dd <= ti
        out.append(float((w[m] * np.exp(-lam * (ti - dd[m]))).sum()))
    return pd.Series(out, index=daily)

S      = idx.S
COUNT  = decay_agg(np.ones(len(d)))                 # pure decayed passage count
MEANSC = decay_agg(np.full(len(d), d.score.mean())) # count x constant score
rng = np.random.default_rng(0)
SHUF   = decay_agg(rng.permutation(d.score.values)) # scores shuffled across passages

print("=" * 74)
print("DOES THE SCORE ADD ANYTHING OVER COUNTING PASSAGES?")
print("=" * 74)
for lab, s in [("decayed passage COUNT", COUNT), ("count x mean score", MEANSC),
               ("scores SHUFFLED across passages", SHUF)]:
    print(f"  corr(S_t, {lab:34s}) = {S.corr(s):+.4f}")
print(f"  corr(dS_t, d[count])                              = {S.diff().corr(COUNT.diff()):+.4f}")
print(f"\n  R2 of S_t on decayed count alone = {S.corr(COUNT)**2:.4f}")

print("\n" + "=" * 74)
print("HOW DISTINCT IS THE CORPUS?")
print("=" * 74)
E, tf, svd2 = N.embed(d.text.tolist())
n = len(E)
sim = cosine_similarity(E)
np.fill_diagonal(sim, 0)
for thr in (0.95, 0.90, 0.80):
    has = (sim > thr).any(axis=1)
    print(f"  passages with a near-duplicate at cos>{thr}: {has.sum():4d} / {n} ({has.mean():.1%})")
# greedy dedup at 0.9
keep, taken = [], np.zeros(n, bool)
order = np.argsort(-np.asarray(E).dot(np.asarray(E).mean(0)))
for i in order:
    if taken[i]: continue
    keep.append(i); taken |= (sim[i] > 0.90); taken[i] = True
print(f"  effectively distinct passages after 0.90 dedup   : {len(keep)}")
print(f"  vocabulary (TF-IDF terms, min_df=3)              : {len(tf.vocabulary_):,}")
print(f"  distinct source filings                          : {d.groupby(['issuer','date','form']).ngroups}")
print(f"  median passage length (words)                    : {int(d.text.str.split().str.len().median())}")

print("\n" + "=" * 74)
print("DOES THE REGRESSION CARE WHICH ONE YOU USE?")
print("=" * 74)
import statsmodels.api as sm, regression as R
df = R.dataset()
base = df.copy()
for lab, s in [("S (scored index)", S), ("decayed COUNT", COUNT)]:
    x = s.reindex(base.index).ffill()
    X = sm.add_constant(pd.DataFrame({"x": x, **{c: base[c] for c in R.CTRL}}))
    m = sm.OLS(base["dTP10"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": True})
    xd = x.diff().fillna(0)
    Xd = sm.add_constant(pd.DataFrame({"x": xd, **{c: base[c] for c in R.CTRL}}))
    md = sm.OLS(base["dTP10"], Xd).fit(cov_type="HAC", cov_kwds={"maxlags": 6, "use_correction": True})
    print(f"  {lab:18s} level: coef={m.params['x']:+7.4f} t={m.tvalues['x']:+5.2f} | "
          f"change: coef={md.params['x']:+7.4f} t={md.tvalues['x']:+5.2f}")
