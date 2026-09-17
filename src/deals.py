"""Step 3: collapse filings into deals. One row per USD bond offering, with the
announcement (trade) date recovered from the matching FWP pricing term sheet."""
import re, pathlib, pandas as pd
from config import PROC, RAW
import events as E

FDIR = RAW / "filings"

def load():
    docs = []
    for p in sorted(FDIR.glob("*.htm")):
        issuer, fdate, form, acc = p.stem.split("_", 3)
        c = E.classify(p); d = E.parse_doc(p)
        ccy = c["ccy"]
        if d["tranches"]:                       # authoritative: what the sizes are quoted in
            ccy = max({t["ccy"] for t in d["tranches"]},
                      key=lambda x: sum(t["notional"] for t in d["tranches"] if t["ccy"] == x))
        docs.append(dict(issuer=issuer, fdate=pd.Timestamp(fdate), form=form, acc=acc, file=p.name,
                         ccy=ccy, prelim=c["prelim"], subj_date=c["subj_date"],
                         trade_date=c["trade_date"], coupons=set(c["coupons"]),
                         is_exchange=c["is_exchange"], is_equity=c["is_equity"],
                         tranches=d["tranches"], total=d["total"], full_coupons=_allcpn(p)))
    return pd.DataFrame(docs)

def _allcpn(p):
    return set(E.RE_CPN.findall(E.text_of(p)))

def build_deals():
    docs = load()
    finals = docs[(docs.total > 0) & (~docs.is_exchange) & (docs.ccy == "USD")
                  & (docs.form.isin(["424B2", "424B5"]))].copy()
    # Meta files the priced FWP and the final 424B2 with identical tranches; keep the 424B
    fwps = docs[docs.form == "FWP"]
    out = []
    for _, f in finals.iterrows():
        cand = fwps[(fwps.issuer == f.issuer) &
                    (fwps.fdate >= f.fdate - pd.Timedelta(days=8)) & (fwps.fdate <= f.fdate)]
        best, score = None, 0.0
        for _, w in cand.iterrows():
            cp = {f"{t['coupon']:.3f}" for t in f.tranches if t["coupon"] is not None}
            if not cp: continue
            s = len(cp & w.full_coupons) / len(cp)
            if s > score: best, score = w, s
        ann = best.trade_date if best is not None and best.trade_date else None
        if ann is None:     # fall back to the preliminary of the same currency
            pre = docs[(docs.issuer == f.issuer) & docs.prelim & (docs.ccy == "USD") &
                       (docs.fdate >= f.fdate - pd.Timedelta(days=8)) & (docs.fdate <= f.fdate)]
            if len(pre):
                ann = pre.sort_values("fdate").iloc[-1].fdate.date()
        out.append(dict(issuer=f.issuer, final_filing=f.fdate.date(), form=f.form,
                        announce=ann, match=round(score, 2),
                        fwp=(best.file if best is not None else None),
                        n_tranches=len(f.tranches), total_usd=f.total, file=f.file,
                        tranches=f.tranches))
    d = pd.DataFrame(out).sort_values("announce").reset_index(drop=True)
    return d

if __name__ == "__main__":
    d = build_deals()
    pd.set_option("display.width", 250)
    print(d[["issuer","announce","final_filing","n_tranches","total_usd","match","fwp"]]
          .assign(total_usd=lambda x: (x.total_usd/1e9).round(2)).to_string(index=False))
