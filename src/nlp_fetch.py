"""Download 10-K/10-Q for the five issuers and keep only capex/financing passages.

The doc asks for earnings-call transcripts. Those are not SEC filings and are not
freely available, so the forward-capex language is taken from the MD&A and
liquidity sections of the periodic reports instead, which is the same content
under audit. Prospectus use-of-proceeds text comes from the 424B files already on disk.
"""
import json, re, time, pathlib
import pandas as pd, requests
from bs4 import BeautifulSoup
from config import RAW, PROC, SEC_UA, ISSUERS

S = requests.Session(); S.headers.update({"User-Agent": SEC_UA})
OUT = RAW / "periodic"; OUT.mkdir(exist_ok=True)
START = "2023-06-01"

KEY = re.compile(
    r"capital expenditure|purchases of property and equipment|property and equipment|"
    r"data cent|artificial intelligence|AI infrastructure|technical infrastructure|"
    r"servers and network|cloud infrastructure|capacity|use of proceeds|"
    r"general corporate purposes|commercial paper|senior notes|finance lease", re.I)


def docs_for(cik):
    d = json.loads((RAW / f"sub_{cik}.json").read_text())
    rec = pd.DataFrame(d["filings"]["recent"])
    for f in d["filings"].get("files", []):
        if f["filingTo"] >= START:
            q = RAW / f["name"]
            if q.exists():
                rec = pd.concat([rec, pd.DataFrame(json.loads(q.read_text()))], ignore_index=True)
    return rec[rec.form.isin(["10-K", "10-Q"]) & (rec.filingDate >= START)]


def run():
    rows = []
    for cik, name in ISSUERS.items():
        sub = docs_for(cik)
        print(f"{name}: {len(sub)} periodic filings", flush=True)
        for _, r in sub.iterrows():
            acc = r.accessionNumber.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{r.primaryDocument}"
            cache = OUT / f"{name}_{r.filingDate}_{r.form}.txt"
            if not cache.exists():
                try:
                    resp = S.get(url, timeout=300)
                    if resp.status_code != 200:
                        print("   MISS", resp.status_code, url, flush=True); continue
                    t = BeautifulSoup(resp.content, "lxml").get_text("\n")
                    t = re.sub(r"[ \t\xa0]+", " ", t); t = re.sub(r"\n\s*\n+", "\n", t)
                    cache.write_text(t)
                    time.sleep(0.3)
                except Exception as e:
                    print("   ERR", e, flush=True); continue
            txt = cache.read_text(errors="ignore")
            for para in re.split(r"(?<=[.!?])\s+", txt):
                p = para.strip()
                if 120 <= len(p) <= 1200 and KEY.search(p):
                    rows.append(dict(issuer=name, date=r.filingDate, form=r.form,
                                     src="periodic", text=p))
    # prospectus use-of-proceeds
    for p in sorted((RAW / "filings").glob("*.htm")):
        issuer, fdate, form, acc = p.stem.split("_", 3)
        t = BeautifulSoup(p.read_bytes(), "lxml").get_text("\n")
        t = re.sub(r"[ \t\xa0]+", " ", t)
        m = re.search(r"USE OF PROCEEDS(.{200,6000}?)(?:CAPITALIZATION|DESCRIPTION OF|UNDERWRIT)",
                      t, re.I | re.S)
        if m:
            for para in re.split(r"(?<=[.!?])\s+", m.group(1)):
                q = para.strip()
                if 100 <= len(q) <= 1200:
                    rows.append(dict(issuer=issuer, date=fdate, form=form,
                                     src="prospectus", text=q))
    df = pd.DataFrame(rows).drop_duplicates(subset=["issuer", "text"])
    df.to_csv(PROC / "nlp_corpus.csv", index=False)
    print(f"\ncorpus: {len(df)} passages, {df.date.min()} -> {df.date.max()}", flush=True)
    print(df.groupby(["issuer", "src"]).size().unstack(fill_value=0), flush=True)


if __name__ == "__main__":
    run()
