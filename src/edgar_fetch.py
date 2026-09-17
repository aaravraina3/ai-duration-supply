import time, pandas as pd, requests
from config import RAW, PROC, SEC_UA
S = requests.Session(); S.headers.update({"User-Agent": SEC_UA})
D = RAW / "filings"; D.mkdir(exist_ok=True)

f = pd.read_csv(PROC / "edgar_filings.csv")
for i, r in f.iterrows():
    p = D / f"{r.issuer}_{r.filing_date}_{r.form}_{r.accession}.htm"
    if p.exists() and p.stat().st_size > 500:
        continue
    try:
        resp = S.get(r.url, timeout=120)
        if resp.status_code == 200:
            p.write_bytes(resp.content)
        else:
            print("  MISS", resp.status_code, r.url)
    except Exception as e:
        print("  ERR", e, r.url)
    time.sleep(0.25)
import os
print("files:", len(list(D.glob("*.htm"))))
print("total MB:", round(sum(x.stat().st_size for x in D.glob('*.htm'))/1e6, 1))
