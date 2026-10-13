"""C4: a rough bound on MBS supply, the other half of the sell-side claim.
Registered in commit 96cd725.

Weekly, Wednesday to Wednesday. The change in Fed MBS holdings (FRED WSHOMCB)
proxies net MBS supply to private investors: runoff (holdings falling) leaves
more for the private sector. The AI coefficient with and without it is the
sensitivity. A bound, not a fix.
"""
import json
import numpy as np, pandas as pd, statsmodels.api as sm
from config import PROC, TAB, SAMPLE_START, SAMPLE_END
import regression as R


def weekly():
    acm = pd.read_csv(PROC / "acm.csv", parse_dates=["date"]).set_index("date").loc[SAMPLE_START:SAMPLE_END]
    fred = pd.read_csv(PROC / "fred.csv", parse_dates=["date"]).set_index("date").loc[SAMPLE_START:SAMPLE_END]
    extra = pd.read_csv(PROC / "fred_extra.csv", parse_dates=["date"]).set_index("date").loc[SAMPLE_START:SAMPLE_END]
    deals = pd.read_csv(PROC / "deals_all.csv", parse_dates=["announce"])
    auc = R.treasury_supply()["auc_10y"].loc[SAMPLE_START:SAMPLE_END]
    rule = "W-WED"
    w = pd.DataFrame({"TP10": acm.ACMTP10.resample(rule).last() * 100})
    w["ai"] = (deals.set_index("announce").tenyr_equiv / 1e9).resample(rule).sum().reindex(w.index).fillna(0.0)
    w["mbs"] = extra.WSHOMCB.resample(rule).last() / 1e3          # $bn
    w["be"] = fred.T10YIE.resample(rule).last() * 100
    w["vix"] = fred.VIXCLS.resample(rule).last()
    w["oil"] = np.log(fred.DCOILWTICO.resample(rule).last()) * 100
    w["auc_10y"] = auc.resample(rule).sum().reindex(w.index).fillna(0.0)
    for c in ("TP10", "mbs", "be", "vix", "oil"):
        w["d" + c] = w[c].diff()
    return w.dropna()


def fit(w, cols):
    X = sm.add_constant(w[cols])
    return sm.OLS(w.dTP10, X).fit(cov_type="HAC", cov_kwds={"maxlags": 4, "use_correction": True})


def main():
    head = open(PROC.parent / "raw" / "fred_WSHOMCB.csv").readline().strip()
    w = weekly()
    base = ["ai", "dbe", "doil", "dvix", "auc_10y"]
    a = fit(w, base); b = fit(w, base + ["dmbs"])
    out = dict(registered_in="96cd725", series_header=head, weeks=int(len(w)),
               ai_without_mbs=dict(b=float(a.params["ai"]), t=float(a.tvalues["ai"])),
               ai_with_mbs=dict(b=float(b.params["ai"]), t=float(b.tvalues["ai"])),
               ai_change_pct=float((b.params["ai"] / a.params["ai"] - 1) * 100),
               mbs=dict(b=float(b.params["dmbs"]), t=float(b.tvalues["dmbs"]), p=float(b.pvalues["dmbs"])),
               mbs_holdings_change_over_sample_bn=float(w.mbs.iloc[-1] - w.mbs.iloc[0]))
    (TAB / "mbs.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
