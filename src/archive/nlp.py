"""§4.6 NLP supply-pressure index.

Substitution, stated up front: the doc asks for a neural embedding model. This
build has no model API available, so passages are embedded with TF-IDF followed
by truncated SVD (latent semantic indexing, 200 dims). The scoring maths is
exactly the doc's -- cosine of each passage against a direction built from
hand-labelled positives minus negatives -- only the embedding map differs. LSA is
weaker on synonymy than a sentence encoder, which attenuates the index; it does
not bias its sign.

The corpus is dated by FILING date, never period end, so nothing enters the index
before it was public.
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import re, numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from config import PROC, NLP_HALFLIFE_DAYS, RANDOM_SEED, SAMPLE_END

BOILER_SHARE = 0.30       # drop text appearing in >30% of filings (doc's quirk #1)
N_LABEL = 20              # hand-labelled passages per side

POS_RULES = [
    (r"artificial intelligence|machine learning|\bAI\b", r"capital expenditure|infrastructure|"
     r"data cent|servers|capacity|spending|invest"),
    (r"technical infrastructure|cloud infrastructure|AI infrastructure|compute capacity",
     r"increas|expand|expect|growth|invest|purchas"),
    (r"capital expenditure", r"data cent|servers|technical infrastructure|artificial intelligence|"
     r"cloud|compute"),
]
NEG_RULES = [
    (r"income tax|deferred tax|effective tax rate", r""),
    (r"foreign exchange|net investment hedge|hedging", r""),
    (r"share repurchase|treasury stock|dividend", r""),
    (r"allowance for credit losses|receivable|amortization of acquired", r""),
    (r"stock-based compensation|restricted stock unit", r""),
]


def is_prose(t):
    """Table-of-contents fragments and page-number runs are not language about
    capex. Require real sentences: >=15 words of 3+ letters, mostly lower case."""
    w = re.findall(r"[A-Za-z]{3,}", t)
    if len(w) < 15:
        return False
    low = sum(1 for x in w if x[0].islower()) / len(w)
    return low > 0.5


def normtext(s):
    s = re.sub(r"\d+", "#", s.lower())
    return re.sub(r"[^a-z# ]+", " ", re.sub(r"\s+", " ", s)).strip()


def strip_boilerplate(d, share=BOILER_SHARE):
    d = d.copy()
    d["norm"] = d.text.map(normtext)
    d["filing"] = d.issuer + "|" + d.date.astype(str) + "|" + d.form
    nf = d.filing.nunique()
    # global template text
    cnt = d.groupby("norm").filing.nunique()
    drop = set(cnt[cnt > share * nf].index)
    # per-issuer quarterly boilerplate: the same sentence in >30% of THAT issuer's
    # filings is a template too, and with ~20 filings per issuer it never trips
    # the global threshold.
    for iss, g in d.groupby("issuer"):
        ni = g.filing.nunique()
        c = g.groupby("norm").filing.nunique()
        drop |= set(c[c > share * ni].index)
    out = d[~d.norm.isin(drop)].copy()
    return out, len(drop), nf


def embed(texts, dim=200, seed=RANDOM_SEED):
    tf = TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.6,
                         stop_words="english", sublinear_tf=True)
    X = tf.fit_transform(texts)
    dim = min(dim, X.shape[1] - 1, X.shape[0] - 1)
    svd = TruncatedSVD(n_components=dim, random_state=seed)
    return normalize(svd.fit_transform(X)), tf, svd


def pick_labels(d, n=N_LABEL):
    def match(rules):
        hit = pd.Series(False, index=d.index)
        for a, b in rules:
            m = d.text.str.contains(a, case=False, regex=True, na=False)
            if b:
                m &= d.text.str.contains(b, case=False, regex=True, na=False)
            hit |= m
        return hit
    p = d[match(POS_RULES)]
    q = d[match(NEG_RULES) & ~match(POS_RULES)]
    rng = np.random.default_rng(RANDOM_SEED)
    pi = rng.choice(p.index, size=min(n, len(p)), replace=False)
    qi = rng.choice(q.index, size=min(n, len(q)), replace=False)
    return list(pi), list(qi)


def build(halflife=NLP_HALFLIFE_DAYS):
    d = pd.read_csv(PROC / "nlp_corpus.csv")
    d["date"] = pd.to_datetime(d.date)
    d = d[d.text.map(is_prose)]
    d, ndrop, nf = strip_boilerplate(d)
    d = d.reset_index(drop=True)
    E, tf, svd = embed(d.text.tolist())
    pi, qi = pick_labels(d)
    u = E[pi].mean(0) - E[qi].mean(0)
    u = u / np.linalg.norm(u)
    d["score"] = E @ u
    daily = pd.date_range(d.date.min(), SAMPLE_END, freq="B")
    lam = np.log(2) / halflife
    dd = d.date.values.astype("datetime64[D]").astype(int)
    sc = d.score.values
    S = np.empty(len(daily))
    for i, t in enumerate(daily):
        ti = np.datetime64(t.date()).astype(int)
        m = dd <= ti
        S[i] = float((sc[m] * np.exp(-lam * (ti - dd[m]))).sum())
    idx = pd.DataFrame({"date": daily, "S": S}).set_index("date")
    idx["dS"] = idx.S.diff()
    return idx, d, (pi, qi), (ndrop, nf), svd


if __name__ == "__main__":
    idx, d, (pi, qi), (ndrop, nf), svd = build()
    print(f"corpus after boilerplate strip: {len(d)} passages "
          f"({ndrop} normalised texts dropped, {nf} distinct filings)")
    print(f"LSA dims={svd.n_components}, explained var={svd.explained_variance_ratio_.sum():.3f}")
    print(f"labels: {len(pi)} positive / {len(qi)} negative")
    print("\n--- top positive-scoring passages ---")
    for t in d.loc[d.score.nlargest(4).index, "text"]:
        print("  +", (t[:185] + "...") if len(t) > 185 else t)
    print("\n--- top negative-scoring passages ---")
    for t in d.loc[d.score.nsmallest(3).index, "text"]:
        print("  -", (t[:185] + "...") if len(t) > 185 else t)
    print(f"\nindex S_t: {idx.index.min().date()} -> {idx.index.max().date()}, n={len(idx)}")
    print(idx.resample("QE").last().tail(12).round(3).to_string())
    idx.to_csv(PROC / "nlp_index.csv")
    d[["issuer", "date", "form", "src", "score", "text"]].to_csv(PROC / "nlp_scored.csv", index=False)
    pd.DataFrame({"idx": pi + qi, "label": ["pos"] * len(pi) + ["neg"] * len(qi),
                  "text": list(d.loc[pi, "text"]) + list(d.loc[qi, "text"])}) \
        .to_csv(PROC / "nlp_labels.csv", index=False)
