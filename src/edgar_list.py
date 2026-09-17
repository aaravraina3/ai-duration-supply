"""Step 1 of the event list: enumerate every 424B2/424B5/FWP the five issuers
filed in the sample window, from the EDGAR submissions API."""
import json, time
import pandas as pd, requests
from config import RAW, PROC, SEC_UA, ISSUERS

S = requests.Session(); S.headers.update({"User-Agent": SEC_UA})
FORMS = {"424B2", "424B5", "424B3", "FWP"}
START = "2023-06-01"

def _blocks(cik):
    """recent block + any older overflow files"""
    p = RAW / f"sub_{cik}.json"
    if not p.exists():
        r = S.get(f"https://data.sec.gov/submissions/CIK{cik}.json", timeout=120)
        r.raise_for_status(); p.write_bytes(r.content); time.sleep(0.3)
    d = json.loads(p.read_text())
    out = [pd.DataFrame(d["filings"]["recent"])]
    for f in d["filings"].get("files", []):
        # only fetch overflow files whose range can reach into our window
        if f["filingTo"] < START:
            continue
        q = RAW / f["name"]
        if not q.exists():
            r = S.get(f"https://data.sec.gov/submissions/{f['name']}", timeout=120)
            r.raise_for_status(); q.write_bytes(r.content); time.sleep(0.3)
        out.append(pd.DataFrame(json.loads(q.read_text())))
    return pd.concat(out, ignore_index=True), d["name"]

def build():
    rows = []
    for cik, name in ISSUERS.items():
        df, legal = _blocks(cik)
        df = df[df["form"].isin(FORMS) & (df["filingDate"] >= START)]
        for _, r in df.iterrows():
            acc = r["accessionNumber"].replace("-", "")
            rows.append(dict(
                issuer=name, cik=cik, legal_name=legal, form=r["form"],
                filing_date=r["filingDate"], accession=r["accessionNumber"],
                primary_doc=r["primaryDocument"],
                url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{r['primaryDocument']}",
                idx=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/",
            ))
        print(f"{name:10s} {len(df):3d} filings since {START}")
    out = pd.DataFrame(rows).sort_values(["filing_date", "issuer"])
    out.to_csv(PROC / "edgar_filings.csv", index=False)
    print(f"\ntotal {len(out)}")
    print(out.groupby(["issuer", "form"]).size().unstack(fill_value=0))
    return out

if __name__ == "__main__":
    b = build()
    print("\n--- by year/form ---")
    b["yr"] = b.filing_date.str[:4]
    print(b.groupby(["yr", "form"]).size().unstack(fill_value=0))
