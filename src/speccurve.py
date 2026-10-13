"""B9: the specification curve, registered as F1 in research/11_UPGRADE_PREREG.md
(commit f304594) before it ran.

216 specifications = dependent (2) x horizon (2) x controls (3) x shock (3) x
sample start (2) x macro filter (3). Each deal is assigned one timing-matched
placebo date per draw, and every spec reads the same assignment, so the joint
null across specs is kept for Romano-Wolf.

Coefficients are computed by Frisch-Waugh (residualise y and the shock on the
controls), which equals the OLS coefficient in localproj.project; the headline
spec is checked against headline.json.
"""
import itertools, json
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, TAB, FIG, RANDOM_SEED, JUMBO_USD
import localproj as L, placebo_matched as PM

N_DRAW = 2000
CONTROLS = {"headline": ["dbe", "doil", "dvix", "auc_10y"], "none": [],
            "headline minus auc_10y": ["dbe", "doil", "dvix"]}
STARTS = {"2024-01-03": "2024-01-03", "2025-01-02": "2025-01-02"}
HORIZONS = {"h0": (0,), "pooled h0-2": (0, 1, 2)}
DEPS = ("ACM TP10", "DGS10")
SHOCKS = ("10y-equivalent", "face value", "10y-equivalent, jumbo only")
FILTERS = ("none", "drop release-day deals", "drop release in t-1..t+1")
MIN_DEALS = 5


def panel():
    P = L.panel()
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    P["DGS10"] = fred.DGS10.reindex(P.index).ffill() * 100
    P["ACM TP10"] = P.TP10
    return P


def deal_table(P):
    d = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    d = d[d.announce.isin(P.index)].reset_index(drop=True)
    lt = PM.lag_table(P.index)
    lag0 = lt.lag.reindex(d.announce).values
    nxt = lt.lag.shift(-1).reindex(d.announce).values          # release on t+1 has lag 0 there
    d["release_day"] = lag0 == 0
    d["release_in_window"] = (lag0 == 0) | (lag0 == 1) | (nxt == 0)
    return d, lt


def draw_assignments(P, d, lt, n, seed):
    """n x deals array of panel positions: the placebo date each deal moves to."""
    rng = np.random.default_rng(seed)
    ids = pd.Series(np.arange(1, len(d) + 1, dtype=float), index=d.announce)
    pos = np.empty((n, len(d)), dtype=int)
    for k in range(n):
        f = PM.draw_matched(ids, lt, rng)
        m = {int(v) - 1: P.index.get_loc(dt) for dt, v in f.items()}
        pos[k] = [m[i] for i in range(len(d))]
    return pos


def sizes(d, shock):
    if shock == "face value":
        return d.total_usd.values / 1e9
    s = d.tenyr_equiv.values / 1e9
    if shock == "10y-equivalent, jumbo only":
        s = np.where(d.total_usd.values >= JUMBO_USD, s, 0.0)
    return s


def keep(d, filt):
    if filt == "drop release-day deals":
        return ~d.release_day.values
    if filt == "drop release in t-1..t+1":
        return ~d.release_in_window.values
    return np.ones(len(d), bool)


def fwl_b(y, C, S):
    """Coefficient on each column of S in y ~ C + S_col, by Frisch-Waugh."""
    beta = np.linalg.lstsq(C, np.column_stack([y, S]), rcond=None)[0]
    R = np.column_stack([y, S]) - C @ beta
    yr, Sr = R[:, 0], R[:, 1:]
    return (Sr * yr[:, None]).sum(0) / (Sr ** 2).sum(0)


def run():
    P0 = panel()
    rows, nulls = [], []
    for start in STARTS:
        P = P0.loc[start:]
        d, lt = deal_table(P)
        pos = draw_assignments(P, d, lt, N_DRAW, RANDOM_SEED)
        n = len(P)
        for dep, hz, ctrl, shock, filt in itertools.product(DEPS, HORIZONS, CONTROLS, SHOCKS, FILTERS):
            s = sizes(d, shock) * keep(d, filt)
            n_deals = int((s > 0).sum())
            spec = dict(dep=dep, horizon=hz, controls=ctrl, shock=shock, start=start, filter=filt, n_deals=n_deals)
            if n_deals < MIN_DEALS:
                rows.append({**spec, "b": np.nan}); nulls.append(None); continue
            obs = np.zeros(n); np.add.at(obs, [P.index.get_loc(t) for t in d.announce], s)
            plac = np.zeros((n, N_DRAW))
            for k in range(N_DRAW):
                np.add.at(plac[:, k], pos[k], s)
            S = np.column_stack([obs, plac])
            bs = []
            for h in HORIZONS[hz]:
                y = (P[dep].shift(-h) - P[dep].shift(1)).values
                C = np.column_stack([np.ones(n)] + [P[c].values for c in CONTROLS[ctrl]])
                ok = ~np.isnan(y) & ~np.isnan(C).any(1)
                bs.append(fwl_b(y[ok], C[ok], S[ok]))
            b = np.mean(bs, axis=0)
            rows.append({**spec, "b": float(b[0])}); nulls.append(b[1:])
    return pd.DataFrame(rows), nulls


def adjust(t, null):
    """Romano-Wolf stepdown on |b|/sd_placebo, and Benjamini-Hochberg on raw p."""
    ok = t.b.notna().values
    B = np.array([z for z in null if z is not None])               # specs x draws
    sd = B.std(1)
    tobs = np.abs(t.b.values[ok]) / sd
    tnull = np.abs(B) / sd[:, None]
    raw = (np.abs(B) >= np.abs(t.b.values[ok])[:, None]).mean(1)
    order = np.argsort(-tobs); rw = np.empty(len(order)); run = 0.0
    for r, j in enumerate(order):
        mx = tnull[order[r:]].max(0)
        run = max(run, float(np.mean(mx >= tobs[j]))); rw[j] = run
    m = len(raw); o = np.argsort(raw); bh = np.empty(m); prev = 1.0
    for r in range(m - 1, -1, -1):
        prev = min(prev, raw[o[r]] * m / (r + 1)); bh[o[r]] = prev
    t = t.copy()
    for c, v in (("sd_placebo", sd), ("p_raw", raw), ("p_romano_wolf", rw), ("p_bh", bh)):
        t.loc[ok, c] = v
    return t


def figure(t):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    s = t.dropna(subset=["b"]).sort_values("b").reset_index(drop=True)
    head = (s.dep == "ACM TP10") & (s.horizon == "h0") & (s.controls == "headline") & (s.shock == "10y-equivalent") \
        & (s.start == "2024-01-03") & (s["filter"] == "none")
    dims = [("dep", DEPS), ("horizon", tuple(HORIZONS)), ("controls", tuple(CONTROLS)), ("shock", SHOCKS),
            ("start", tuple(STARTS)), ("filter", FILTERS)]
    nrow = sum(len(v) for _, v in dims)
    fig, ax = plt.subplots(2, 1, figsize=(9.6, 7.2), sharex=True, gridspec_kw={"height_ratios": [1.2, 1.6]})
    x = np.arange(len(s))
    ax[0].errorbar(x, s.b, yerr=1.96 * s.sd_placebo, fmt="none", ecolor="#bbb", lw=.6)
    ax[0].scatter(x, s.b, s=6, c=np.where(s.p_raw < 0.10, "#1f4e79", "#999"))
    ax[0].scatter(x[head], s.b[head], s=40, facecolors="none", edgecolors="#c0392b", label="headline spec")
    ax[0].axhline(0, color="k", lw=.7)
    ax[0].set_ylabel("coefficient")
    ax[0].set_title("Specification curve: 216 specs, sorted (blue = raw placebo p < 0.10, bars = ±1.96 placebo sd)", fontsize=9)
    ax[0].legend(frameon=False, fontsize=7)
    labels, r = [], 0
    for col, vals in dims:
        for v in vals:
            on = (s[col] == v).values
            ax[1].scatter(x[on], np.full(on.sum(), r), s=3, color="#1f4e79")
            labels.append(f"{col}: {v}"); r += 1
    ax[1].set_yticks(range(nrow)); ax[1].set_yticklabels(labels, fontsize=6); ax[1].invert_yaxis()
    ax[1].set_xlabel("specification, sorted by estimate")
    fig.tight_layout(); fig.savefig(FIG / "speccurve.png", dpi=140); plt.close(fig)


def main():
    t, null = run()
    t = adjust(t, null)
    t.to_csv(TAB / "speccurve.csv", index=False)
    figure(t)
    ok = t.dropna(subset=["b"])
    h = ok[(ok.dep == "ACM TP10") & (ok.horizon == "h0") & (ok.controls == "headline") & (ok.shock == "10y-equivalent")
           & (ok.start == "2024-01-03") & (ok["filter"] == "none")].iloc[0]
    summary = dict(registered_in="f304594", n_specs=len(t), n_estimated=len(ok), n_missing=int(t.b.isna().sum()),
                   share_positive=float((ok.b > 0).mean()), share_p_raw_below_10=float((ok.p_raw < 0.10).mean()),
                   share_p_raw_below_05=float((ok.p_raw < 0.05).mean()),
                   share_rw_below_10=float((ok.p_romano_wolf < 0.10).mean()),
                   share_bh_below_10=float((ok.p_bh < 0.10).mean()),
                   headline=dict(b=float(h.b), p_raw=float(h.p_raw), p_romano_wolf=float(h.p_romano_wolf),
                                 p_bh=float(h.p_bh)))
    (TAB / "speccurve_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
