"""D1: anticipated versus surprise supply. Registered in commit 96cd725.

If markets anticipate issuance, only the unexpected part of a deal should move
the term premium on the day. A filing-level model forecasts each issuer's next
90 days of 10y-equivalent issuance from its 10-K/10-Q passages; each deal is
split into the forecast part and the surprise.

Model ladder (UPGRADE_PLAN 5.0): rung 0 trailing issuance; 1 adds the decayed
passage count; 2 adds stated capex; 3 ridge on sentence embeddings plus rung 2.
"""
import json, re
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, TAB, RANDOM_SEED, SAMPLE_END, NLP_HALFLIFE_DAYS
import localproj as L, placebo_matched as PM, speccurve as SC

MODEL = "sentence-transformers/all-mpnet-base-v2"
DEDUP = 0.90
WINDOW = 90
WARMUP = 12
ALPHAS = [0.01, 0.1, 1, 10, 100, 1000, 10000]
CAPEX = re.compile(r"capital expenditures?[^.]{0,200}?\$\s?([\d.]+)\s?billion", re.I)


def embed(texts):
    from sentence_transformers import SentenceTransformer
    import sentence_transformers
    m = SentenceTransformer(MODEL)
    return m.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False), sentence_transformers.__version__


def dedup(c, E):
    order = np.argsort(c.date.values, kind="stable")
    keep, kept = [], []
    for i in order:
        if kept and float(np.max(E[kept] @ E[i])) > DEDUP:
            continue
        keep.append(i); kept.append(i)
    return np.array(sorted(keep))


def filings(c, E, keep, deals):
    end = pd.Timestamp(SAMPLE_END)
    lam = np.log(2) / NLP_HALFLIFE_DAYS
    ck = c.iloc[keep].assign(_row=keep)
    rows = []
    for (iss, date, form), g in c.groupby(["issuer", "date", "form"]):
        dt = pd.Timestamp(date)
        mine = deals[deals.issuer == iss]
        prior = ck[(ck.issuer == iss) & (pd.to_datetime(ck.date) <= dt)]
        age = (dt - pd.to_datetime(prior.date)).dt.days.values
        own = ck[(ck.issuer == iss) & (ck.date == date) & (ck.form == form)]
        cap = [float(x) for t in g.text for x in CAPEX.findall(t)]
        rows.append(dict(
            issuer=iss, date=dt, form=form,
            trailing365=float(mine[(mine.announce < dt) & (mine.announce >= dt - pd.Timedelta(days=365))].tenyr_equiv.sum() / 1e9),
            decayed_count=float(np.exp(-lam * age).sum()),
            capex_bn=max(cap) if cap else 0.0,
            emb=E[own._row.values].mean(0) if len(own) else np.zeros(E.shape[1]),
            target=float(mine[(mine.announce >= dt) & (mine.announce < dt + pd.Timedelta(days=WINDOW))].tenyr_equiv.sum() / 1e9),
            complete=bool(dt + pd.Timedelta(days=WINDOW) <= end)))
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


RUNGS = {0: ["trailing365"], 1: ["trailing365", "decayed_count"], 2: ["trailing365", "decayed_count", "capex_bn"]}


def design(F, rung):
    X = F[RUNGS[min(rung, 2)]].values
    if rung == 3:
        X = np.column_stack([X, np.vstack(F.emb.values)])
    return X


def fit_predict(Ftr, Fte, rung, alpha=None):
    from sklearn.linear_model import Ridge, LinearRegression
    Xtr, Xte = design(Ftr, rung), design(Fte, rung)
    if rung < 3:
        m = LinearRegression().fit(Xtr, Ftr.target.values)
    else:
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd
        m = Ridge(alpha=alpha).fit(Xtr, Ftr.target.values)
    return m.predict(Xte)


def usable(F, i):
    """Training filings for test filing i: complete targets whose window ends before i's date."""
    return F[(F.index < i) & F.complete & (F.date + pd.Timedelta(days=WINDOW) < F.date[i])]


def inner_alpha(Ftr):
    if len(Ftr) < 8:
        return 100.0
    errs = {a: [] for a in ALPHAS}
    for j in range(len(Ftr) // 2, len(Ftr)):
        tr = Ftr.iloc[:j]; tr = tr[tr.date + pd.Timedelta(days=WINDOW) < Ftr.date.iloc[j]]
        if len(tr) < 4:
            continue
        for a in ALPHAS:
            errs[a].append((fit_predict(tr, Ftr.iloc[[j]], 3, a)[0] - Ftr.target.iloc[j]) ** 2)
    return min(ALPHAS, key=lambda a: np.mean(errs[a]) if errs[a] else np.inf)


def walk_forward(F):
    preds = {r: np.full(len(F), np.nan) for r in range(4)}
    for i in range(WARMUP, len(F)):
        tr = usable(F, i)
        if len(tr) < 5:
            continue
        for r in range(3):
            preds[r][i] = fit_predict(tr, F.iloc[[i]], r)[0]
        preds[3][i] = fit_predict(tr, F.iloc[[i]], 3, inner_alpha(tr))[0]
    return preds


def ladder(F, preds):
    ok = F.complete.values & ~np.isnan(preds[0])
    rows, se = [], {}
    for r in range(4):
        e2 = (preds[r][ok] - F.target.values[ok]) ** 2
        se[r] = e2.std(ddof=1) / np.sqrt(len(e2))
        rows.append(dict(rung=r, oos_mse=float(e2.mean()), se=float(se[r]), n=int(ok.sum())))
    t = pd.DataFrame(rows)
    best = t.oos_mse.idxmin()
    chosen = int(t[t.oos_mse <= t.oos_mse[best] + t.se[best]].rung.min())   # one-SE rule
    return t, chosen


def decompose(F, preds, chosen, deals):
    rows = []
    for _, dl in deals.iterrows():
        prior = F[(F.issuer == dl.issuer) & (F.date < dl.announce)]
        size = dl.tenyr_equiv / 1e9
        if prior.empty:
            rows.append(dict(announce=dl.announce, issuer=dl.issuer, size=size, expected=0.0, source="no filing"))
            continue
        i = prior.index[-1]
        f = preds[chosen][i]
        src = f"rung {chosen}"
        if np.isnan(f):                     # filing inside warm-up: naive rate (DECISIONS D-18)
            f = F.trailing365[i] * WINDOW / 365; src = "warm-up naive rate"
        done = deals[(deals.issuer == dl.issuer) & (deals.announce >= F.date[i]) & (deals.announce < dl.announce)]
        exp = max(0.0, f - done.tenyr_equiv.sum() / 1e9)
        rows.append(dict(announce=dl.announce, issuer=dl.issuer, size=size, expected=exp, source=src))
    D = pd.DataFrame(rows)
    D["surprise"] = D["size"] - D.expected
    return D


def two_shock_test(D):
    P = L.panel()
    d, lt = SC.deal_table(P)
    D = D.set_index("announce").reindex(d.announce)
    pos = SC.draw_assignments(P, d, lt, PM.N_DRAW, RANDOM_SEED)
    n = len(P)
    y = (P.TP10 - P.TP10.shift(1)).values
    C = np.column_stack([np.ones(n)] + [P[c].values for c in ["dbe", "doil", "dvix", "auc_10y"]])
    ok = ~np.isnan(y) & ~np.isnan(C).any(1)

    def coefs(day_pos):
        E = np.zeros((n, 2))
        np.add.at(E[:, 0], day_pos, D.expected.values)
        np.add.at(E[:, 1], day_pos, D.surprise.values)
        X = np.column_stack([E, C])[ok]
        return np.linalg.lstsq(X, y[ok], rcond=None)[0][:2]
    obs = coefs([P.index.get_loc(t) for t in d.announce])
    null = np.array([coefs(pos[k]) for k in range(PM.N_DRAW)])
    diff = obs[1] - obs[0]
    return dict(b_expected=float(obs[0]), b_surprise=float(obs[1]),
                p_expected=float(np.mean(np.abs(null[:, 0]) >= abs(obs[0]))),
                p_surprise=float(np.mean(np.abs(null[:, 1]) >= abs(obs[1]))),
                p_surprise_minus_expected=float(np.mean(np.abs(null[:, 1] - null[:, 0]) >= abs(diff))))


def main():
    c = pd.read_csv(PROC / "nlp_corpus.csv")
    deals = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    E, ver = embed(c.text.astype(str).tolist())
    keep = dedup(c, E)
    F = filings(c, E, keep, deals)
    preds = walk_forward(F)
    lad, chosen = ladder(F, preds)
    D = decompose(F, preds, chosen, deals)
    test = two_shock_test(D)
    out = dict(registered_in="96cd725", model=MODEL, sentence_transformers_version=ver,
               passages_before=int(len(c)), passages_after_dedup=int(len(keep)), filings=int(len(F)),
               filings_with_complete_target=int(F.complete.sum()),
               ladder=lad.to_dict(orient="records"), chosen_rung=chosen,
               deals=D.assign(announce=D.announce.astype(str)).to_dict(orient="records"), lp=test)
    (TAB / "expected_supply.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({k: v for k, v in out.items() if k != "deals"}, indent=2, default=float))
    print(D.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
