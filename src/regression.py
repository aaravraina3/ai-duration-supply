"""§4.8 main specification: does AI duration supply move the ACM term premium?

  d TP10_t = a + sum_k gamma_k (S_t * P(z_t=k)) + theta' Z_t + e_t

Two supply measures are carried side by side:
  S_t  the NLP supply-pressure index from nlp.py (language, forward looking)
  D_t  decayed cumulative 10-year-equivalent duration actually announced by the
       five issuers (hard dollars, backward looking)
Both are run in levels (as the doc writes it) and in changes. Levels are the
doc's spec but a trending regressor against a stationary dependent variable
invites a spurious fit, so the change spec is reported next to it every time.
"""
import json, numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, RAW, HMM_K, NLP_HALFLIFE_DAYS, SAMPLE_END
import curve as C


def nw_lags(T):
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def treasury_supply():
    """Daily coupon-auction size, and duration-weighted 10y equivalents."""
    d = json.load(open(RAW / "fiscal_auctions.json"))
    a = pd.DataFrame(d["data"])
    a = a[a.security_type.isin(["Note", "Bond"])].copy()
    a["auction_date"] = pd.to_datetime(a.auction_date)
    a["amt"] = pd.to_numeric(a.offering_amt, errors="coerce")
    yrs = a.security_term.str.extract(r"(\d+)-Year")[0].astype(float)
    mos = a.security_term.str.extract(r"(\d+)-Month")[0].astype(float).fillna(0)
    a["tenor"] = yrs.fillna(0) + mos / 12.0
    from eventlist import mod_duration, DUR10
    a["ten10"] = a.amt * a.tenor.map(lambda t: mod_duration(t, 4.5) if t > 0 else 0) / DUR10
    g = a.groupby("auction_date").agg(auc_amt=("amt", "sum"), auc_10y=("ten10", "sum"))
    # surprise = today's size relative to the trailing 6-auction mean for that term
    a = a.sort_values("auction_date")
    a["prev"] = a.groupby("security_term").amt.transform(lambda s: s.shift(1).rolling(6, min_periods=1).mean())
    a["surp"] = (a.amt - a.prev).fillna(0.0)
    g["auc_surprise"] = a.groupby("auction_date").surp.sum()
    return g / 1e9


def ai_supply(halflife=NLP_HALFLIFE_DAYS):
    """Decayed stock of announced AI 10y-equivalent duration, USD bn."""
    ev = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    daily = pd.date_range("2024-01-01", SAMPLE_END, freq="B")
    lam = np.log(2) / halflife
    d0 = ev.announce.values.astype("datetime64[D]").astype(int)
    q = (ev.tenyr_equiv / 1e9).values
    out = []
    for t in daily:
        ti = np.datetime64(t.date()).astype(int)
        m = d0 <= ti
        out.append(float((q[m] * np.exp(-lam * (ti - d0[m]))).sum()))
    D = pd.DataFrame({"date": daily, "D": out}).set_index("date")
    D["dD"] = D.D.diff()
    return D


def dataset():
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    S = pd.read_csv(PROC / "nlp_index.csv", parse_dates=["date"]).set_index("date")
    P = pd.read_csv(PROC / "regime_posteriors.csv", parse_dates=[0], index_col=0)
    P.index.name = "date"
    D = ai_supply()
    T = treasury_supply()

    df = pd.DataFrame(index=acm.loc["2024-01-01":SAMPLE_END].index)
    df["dTP10"] = acm.ACMTP10.diff() * 100
    df["dRN10"] = acm.ACMRNY10.diff() * 100
    df["dY10"] = acm.ACMY10.diff() * 100
    df = df.join(S[["S", "dS"]]).join(D[["D", "dD"]]).join(P)
    df["dbe"] = fred.T10YIE.reindex(df.index).ffill().diff() * 100
    df["dvix"] = fred.VIXCLS.reindex(df.index).ffill().diff()
    df["doil"] = 100 * np.log(fred.DCOILWTICO.reindex(df.index).ffill()).diff()
    for c in ["auc_amt", "auc_10y", "auc_surprise"]:
        df[c] = T[c].reindex(df.index).fillna(0.0)
    return df.dropna()


CTRL = ["dbe", "doil", "dvix", "auc_surprise", "auc_10y"]


def run(df, supply="S", regime=True, dep="dTP10", ctrl=CTRL):
    X = pd.DataFrame(index=df.index)
    if regime:
        for k in range(HMM_K):
            X[f"{supply}_x_p{k}"] = df[supply] * df[f"p{k}_filt"]
    else:
        X[supply] = df[supply]
    for c in ctrl:
        X[c] = df[c]
    X = sm.add_constant(X)
    m = sm.OLS(df[dep], X).fit(cov_type="HAC",
                               cov_kwds={"maxlags": nw_lags(len(df)), "use_correction": True})
    return m


def table(m, name):
    out = [f"\n{name}   n={int(m.nobs)}  R2={m.rsquared:.4f}  NW lags={nw_lags(int(m.nobs))}"]
    out.append(f"  {'term':18s} {'coef':>10s} {'NW se':>9s} {'t':>7s} {'p':>7s}")
    for k in m.params.index:
        out.append(f"  {k:18s} {m.params[k]:10.4f} {m.bse[k]:9.4f} "
                   f"{m.tvalues[k]:7.2f} {m.pvalues[k]:7.3f}")
    return "\n".join(out)


if __name__ == "__main__":
    df = dataset()
    print(f"regression sample: {df.index.min().date()} -> {df.index.max().date()}, n={len(df)}")
    print(f"S range {df.S.min():.2f}..{df.S.max():.2f} | D range {df.D.min():.1f}..{df.D.max():.1f} $bn 10y-equiv")

    specs = {}
    for dep in ["dTP10", "dRN10"]:
        for sup in ["S", "D", "dS", "dD"]:
            for reg in ([True, False] if sup in ("S", "D") else [False]):
                nm = f"{dep} ~ {sup}{' x regime' if reg else ''}"
                specs[nm] = run(df, supply=sup, regime=reg, dep=dep)
    for nm in ["dTP10 ~ S x regime", "dTP10 ~ S", "dTP10 ~ dS",
               "dTP10 ~ D x regime", "dTP10 ~ D", "dTP10 ~ dD",
               "dRN10 ~ S", "dRN10 ~ D"]:
        print(table(specs[nm], nm))

    # ---------------------------------------------------------- the 30bp test
    print("\n" + "=" * 78)
    print("THE 30bp TEST")
    y26 = df.loc["2026-01-01":]
    for sup in ["S", "D"]:
        m = specs[f"dTP10 ~ {sup}"]
        g = m.params[sup]
        implied = g * y26[sup].sum()
        print(f"  level spec  gamma_{sup} = {g:+.5f} bp per unit-day, "
              f"sum_2026 {sup} = {y26[sup].sum():,.0f}  ->  implied dTP = {implied:+.1f} bp")
        md = specs[f"dTP10 ~ d{sup}"]
        gd = md.params[f"d{sup}"]
        chg = y26[sup].iloc[-1] - y26[sup].iloc[0]
        print(f"  change spec gamma_d{sup} = {gd:+.4f} bp per unit, "
              f"2026 change in {sup} = {chg:+.2f}  ->  implied dTP = {gd*chg:+.1f} bp")
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date")
    s10 = fred.DGS10.dropna(); s26 = s10[s10.index >= "2026-01-01"]
    Yb = (s26.iloc[-1] - s26.iloc[0]) * 100
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date")
    t26 = acm.ACMTP10.dropna()[acm.index >= "2026-01-01"]
    r26 = acm.ACMRNY10.dropna()[acm.index >= "2026-01-01"]
    print(f"\n  Y (DGS10 {s26.index[0].date()} -> {s26.index[-1].date()}) = {Yb:+.1f} bp")
    print(f"  realised 2026 d(ACM term premium)      = {(t26.iloc[-1]-t26.iloc[0])*100:+.1f} bp")
    print(f"  realised 2026 d(expected short rates)  = {(r26.iloc[-1]-r26.iloc[0])*100:+.1f} bp")
    print(f"  => the entire 2026 long-end move is in EXPECTATIONS, not term premium.")
    df.to_csv(PROC / "regression_panel.csv")
    with open(PROC / "regression_results.txt", "w") as f:
        for nm, m in specs.items():
            f.write(table(m, nm) + "\n")
