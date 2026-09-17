"""Step 2: parse filings into a tranche-level table, then into events.

Document taxonomy learned from the filings themselves:
  * preliminary 424B5/424B2 ("SUBJECT TO COMPLETION", blank $ amounts) -> ANNOUNCEMENT
  * FWP pricing term sheet ("Trade Date: ...", real sizes)             -> PRICING timestamp
  * final 424B5/424B2 (cover page carries "$X 4.250% NOTES DUE 2031")  -> authoritative sizes
We take sizes from the final and the event date from the FWP trade date, which is
the announcement/pricing day. That resolves the §3 look-ahead quirk directly.
"""
import re, pathlib, datetime as dt
import pandas as pd
from bs4 import BeautifulSoup
from config import RAW, PROC

FDIR = RAW / "filings"

def text_of(p: pathlib.Path) -> str:
    s = BeautifulSoup(p.read_bytes(), "lxml")
    t = s.get_text("\n")
    t = t.replace("’", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t)

# cover-page tranche lines
RE_FIXED = re.compile(
    r"([$€£])\s?([\d,]{7,})\s+(\d+\.\d+)\s?%\s+(?:SENIOR\s+)?NOTES\s+DUE\s+(?:[A-Z]+\s+\d{1,2},\s*)?(\d{4})",
    re.I)
RE_FLOAT = re.compile(
    r"([$€£])\s?([\d,]{7,})\s+FLOATING\s+RATE\s+NOTES\s+DUE\s+(?:[A-Z]+\s+\d{1,2},\s*)?(\d{4})",
    re.I)
RE_TRADE = re.compile(r"Trade\s*Date\s*:?\s*\n?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})")
RE_ISSUED = re.compile(r"Issued\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})")
CCY = {"$": "USD", "€": "EUR", "£": "GBP"}

# things that are not senior unsecured duration supply
NOT_DEBT = re.compile(
    r"mandatory\s+convertible|convertible\s+(?:senior\s+)?notes|preferred\s+stock|"
    r"depositary\s+shares|common\s+stock\s+offering|exchange\s+offer", re.I)

def parse_doc(p):
    t = text_of(p)
    head = t[:9000]                       # cover page region
    issuer, fdate, form, acc = p.stem.split("_", 3)
    prelim = bool(re.search(r"subject\s+to\s+completion", head, re.I))
    tranches = []
    for m in RE_FIXED.finditer(head):
        tranches.append(dict(ccy=CCY[m.group(1)], notional=float(m.group(2).replace(",", "")),
                             coupon=float(m.group(3)), mat_year=int(m.group(4)), floating=False))
    for m in RE_FLOAT.finditer(head):
        tranches.append(dict(ccy=CCY[m.group(1)], notional=float(m.group(2).replace(",", "")),
                             coupon=None, mat_year=int(m.group(3)), floating=True))
    td = RE_TRADE.search(t) or RE_ISSUED.search(head)
    trade = pd.to_datetime(td.group(1)).date() if td else None
    return dict(issuer=issuer, filing_date=fdate, form=form, accession=acc, file=p.name,
                prelim=prelim, trade_date=trade, n_tranches=len(tranches),
                total=sum(x["notional"] for x in tranches),
                not_debt=bool(NOT_DEBT.search(head)), tranches=tranches, nchars=len(t))

def parse_all():
    rows = [parse_doc(p) for p in sorted(FDIR.glob("*.htm"))]
    df = pd.DataFrame(rows)
    df.drop(columns=["tranches"]).to_csv(PROC / "filing_parse.csv", index=False)
    return df, rows

if __name__ == "__main__":
    df, rows = parse_all()
    pd.set_option("display.width", 250, "display.max_rows", 200)
    print(df[["issuer","filing_date","form","prelim","trade_date","n_tranches","total","not_debt"]]
          .assign(total=lambda d: (d.total/1e9).round(2))
          .to_string(index=False))

# ---------------------------------------------------------------- deal assembly
CCY_SYM = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
RE_ANYTRANCHE = re.compile(
    r"([$€£¥])\s?[\d, ]{0,20}(?:[\d.]*\s?%\s+|FLOATING\s+RATE\s+)?(?:SENIOR\s+)?NOTES?\s+DUE", re.I)
RE_SUBJ = re.compile(r"SUBJECT\s+TO\s+COMPLETION,?\s+DATED\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.I)
RE_CPN  = re.compile(r"(\d\.\d{3})\s?%\s+(?:SENIOR\s+)?NOTES?\s+DUE", re.I)
RE_EXCH = re.compile(r"exchange\s+offer|offer\s+to\s+exchange", re.I)

def classify(p):
    """Cover-page classification that works on preliminaries (blank amounts) too."""
    t = text_of(p); head = t[:9000]
    syms = [CCY_SYM[m.group(1)] for m in RE_ANYTRANCHE.finditer(head)]
    ccy = max(set(syms), key=syms.count) if syms else None
    subj = RE_SUBJ.search(head)
    trade = RE_TRADE.search(t)
    return dict(ccy=ccy, is_notes=bool(syms),
                prelim=bool(subj) or bool(re.search(r"subject\s+to\s+completion", head, re.I)),
                subj_date=pd.to_datetime(subj.group(1)).date() if subj else None,
                trade_date=pd.to_datetime(trade.group(1)).date() if trade else None,
                coupons=sorted({m.group(1) for m in RE_CPN.finditer(head)}),
                is_exchange=bool(RE_EXCH.search(head)),
                is_equity=bool(NOT_DEBT.search(head)))
