"""FOMC / CPI / payrolls release dates, for the §3.4 event exclusion rule.

FOMC: federalreserve.gov meeting calendar. Two-day meetings only; the decision
lands on day 2. "(Released ...)" spans are minutes publications and are stripped.
CPI / NFP: bls.gov monthly release calendars, one page per month.
"""
import re, time, pandas as pd, requests
from bs4 import BeautifulSoup
from config import RAW, PROC

UA = {"User-Agent": "Mozilla/5.0 (Macintosh) academic research raina.aa@northeastern.edu"}
MONTHS = ("January February March April May June July August September October "
          "November December").split()

def _get(name, url):
    p = RAW / name
    if not p.exists():
        r = requests.get(url, headers=UA, timeout=120); r.raise_for_status()
        p.write_bytes(r.content); time.sleep(0.3)
    return p.read_text(errors="ignore")

def fomc():
    html = _get("fomc.htm", "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm")
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    txt = re.sub(r"\(Released[^)]*\)", " ", txt)          # minutes, not meetings
    out = []
    for yr in (2023, 2024, 2025, 2026):
        i = txt.find(f"{yr} FOMC Meetings")
        if i < 0: continue
        nxt = [k for k in (txt.find(f"{y} FOMC Meetings", i + 5) for y in range(2021, 2028)) if k > i]
        blk = txt[i:min(nxt) if nxt else i + 4000]
        for m in re.finditer(r"(" + "|".join(MONTHS) + r")\s+(\d{1,2})\s*[-–]\s*(\d{1,2})", blk):
            mon, d2 = m.group(1), int(m.group(3))
            try: out.append(pd.Timestamp(year=yr, month=MONTHS.index(mon) + 1, day=d2))
            except ValueError: pass
    return pd.Series(sorted(set(out)))

def bls_month(year, month):
    """Parse one BLS monthly grid. The grid's first row can carry trailing days of
    the previous month and its last row the opening days of the next one, so anchor
    on the first cell numbered 1 and walk forward while the day count rises."""
    html = _get(f"bls_{year}_{month:02d}.htm",
                f"https://www.bls.gov/schedule/{year}/{month:02d}_sched.htm")
    soup = BeautifulSoup(html, "lxml")
    tb = soup.find("table")
    if tb is None: return []
    cells = []
    for tr in tb.find_all("tr"):
        for td in tr.find_all("td"):
            txt = td.get_text(" ", strip=True)
            m = re.match(r"^(\d{1,2})\b", txt)
            if m: cells.append((int(m.group(1)), txt))
    # The grid is Mon-Fri only, so a month starting on a weekend never shows a
    # cell numbered 1. Segment on every point where the day count falls; the
    # month itself is the longest run.
    breaks = [0] + [i for i in range(1, len(cells)) if cells[i][0] < cells[i-1][0]] + [len(cells)]
    segs = [cells[breaks[i]:breaks[i+1]] for i in range(len(breaks)-1)]
    if not segs: return []
    month_cells = max(segs, key=len)
    hits = []
    for day, txt in month_cells:
        for key, lab in (("Consumer Price Index", "CPI"), ("Employment Situation", "NFP")):
            if key in txt:
                hits.append((pd.Timestamp(year=year, month=month, day=day), lab))
    return hits

def build():
    rows = [{"date": d, "kind": "FOMC"} for d in fomc()]
    for y in (2023, 2024, 2025, 2026):
        for m in range(1, 13):
            if y == 2026 and m > 9: break
            try:
                for d, lab in bls_month(y, m):
                    rows.append({"date": d, "kind": lab})
            except Exception as e:
                print(f"  bls {y}-{m:02d}: {e}")
    df = pd.DataFrame(rows).drop_duplicates().sort_values("date").reset_index(drop=True)
    df.to_csv(PROC / "macro_calendar.csv", index=False)
    return df

if __name__ == "__main__":
    d = build()
    for k in ("FOMC", "CPI", "NFP"):
        s = d[d.kind == k].date
        print(f"{k}: n={len(s)}  per-year {s.dt.year.value_counts().sort_index().to_dict()}")
        print("   2026:", [str(x.date()) for x in s if x.year == 2026])
