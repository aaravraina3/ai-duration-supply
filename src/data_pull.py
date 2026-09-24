"""Download every free source. Idempotent: re-running uses the local cache."""
import io, time, sys
import pandas as pd, requests
from config import RAW, PROC, SEC_UA, FRED_TENORS, FRED_CONTROLS, SAMPLE_START, SAMPLE_END

S = requests.Session()
S.headers.update({"User-Agent": SEC_UA})

def _cache(name, url, binary=False):
    p = RAW / name
    if p.exists() and p.stat().st_size > 1000:
        return p
    r = S.get(url, timeout=180); r.raise_for_status()
    p.write_bytes(r.content)
    print(f"  downloaded {name} ({len(r.content):,} bytes)")
    return p

# --------------------------------------------------------------- FRED
def fred():
    frames = {}
    for sid in list(FRED_TENORS) + FRED_CONTROLS:
        p = _cache(f"fred_{sid}.csv", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")
        d = pd.read_csv(p)
        d.columns = ["date", sid]
        d["date"] = pd.to_datetime(d["date"])
        d[sid] = pd.to_numeric(d[sid], errors="coerce")   # '.' -> NaN on holidays
        frames[sid] = d.set_index("date")[sid]
        time.sleep(0.2)
    df = pd.DataFrame(frames).sort_index()
    df.to_csv(PROC / "fred.csv")
    print(f"FRED: {df.shape}, {df.index.min().date()} -> {df.index.max().date()}")
    return df

# --------------------------------------------------------------- GSW zero-coupon
def gsw():
    p = _cache("feds200628.csv", "https://www.federalreserve.gov/data/yield-curve-tables/feds200628.csv")
    # header block is a long note; find the real header row
    txt = p.read_text(errors="ignore").splitlines()
    hdr = next(i for i, l in enumerate(txt) if l.startswith("Date,"))
    d = pd.read_csv(p, skiprows=hdr)
    d["Date"] = pd.to_datetime(d["Date"])
    d = d.set_index("Date").sort_index()
    keep = [c for c in d.columns if c.startswith(("SVENY", "SVENPY", "SVENF", "BETA", "TAU"))]
    d = d[keep].apply(pd.to_numeric, errors="coerce")
    d.to_csv(PROC / "gsw.csv")
    print(f"GSW: {d.shape}, {d.index.min().date()} -> {d.index.max().date()}")
    return d

# --------------------------------------------------------------- ACM term premium
def acm():
    p = _cache("ACMTermPremium.xls",
               "https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls")
    d = pd.read_excel(p, engine="xlrd", sheet_name="ACM Daily")   # daily sheet, not the monthly default
    dc = d.columns[0]
    d[dc] = pd.to_datetime(d[dc], format="%d-%b-%Y", errors="coerce")
    if d[dc].isna().mean() > .5:
        d[dc] = pd.to_datetime(d.iloc[:, 0], errors="coerce")
    d = d.dropna(subset=[dc]).set_index(dc).sort_index()
    d.index.name = "date"
    d = d.apply(pd.to_numeric, errors="coerce")
    d.to_csv(PROC / "acm.csv")
    print(f"ACM: {d.shape}, cols {list(d.columns)[:6]}..., {d.index.min().date()} -> {d.index.max().date()}")
    return d

# --------------------------------------------------------------- Treasury auctions
def auctions():
    p = RAW / "auctions.json"
    if not p.exists():
        url = ("https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json"
               f"&dateFieldName=auctionDate&startDate=2023-06-01&endDate={SAMPLE_END}")
        r = S.get(url, timeout=180); r.raise_for_status(); p.write_bytes(r.content)
    d = pd.read_json(p)
    if len(d):
        d["auctionDate"] = pd.to_datetime(d["auctionDate"], errors="coerce")
        d.to_csv(PROC / "auctions.csv")
    print(f"Auctions: {d.shape}")
    return d

if __name__ == "__main__":
    fred(); gsw(); acm(); auctions()
