"""Upgrade A12: find every number in PAPER.pdf and README.md and look for it in
the committed tables. Prints the numbers that trace to nothing.

A number traces if some committed value rounds to it at the precision it is
printed, directly or as a percentage. The match table goes to
output/tables/number_trace.csv so each trace can be checked by eye; a value can
match by coincidence, so an empty untraced list is necessary, not sufficient.

Constants that are not results (dates, the injection size, worked examples in
the text) are listed in CONSTANTS with the reason, and skipped.

    .venv/bin/python src/verify_numbers.py
"""
import json, re, sys
import pandas as pd
from pypdf import PdfReader
from config import ROOT, TAB, PROC

CONSTANTS = {
    # worked examples and definitions in the explainer boxes, not results
    "4.94%": "bp explainer", "6bp": "bp explainer", "1%": "duration explainer",
    "8%": "duration explainer", "4.250%": "cover-page example", "5bp": "size of the injected bump",
    "30bp": "the sell-side claim being tested", "30": "the sell-side claim / 10-to-30-year bucket",
    "5.10%": "press report of the 2026-09-23 intraday print, noted in headline.json Y.note",
    "$5B": "duration example", "$25": "two $25 billion deals, deal sizes in deals_all.csv",
    "424": "form name 424B", "10": "10-year maturity / 10 Hz", "20": "maturity or horizon label",
    "2": "maturity or horizon label", "3": "horizon label", "5": "horizon label", "0": "horizon label",
    "60": "LP horizon range", "1.000": "R2 of the control fit, see research/05_METHODS.md",
    "0.999": "rhetorical", "$93": "quoted consensus 2025 total (external)",
    "$132 billion": "quoted 2026 total (external)", "$93B": "quoted consensus 2025 total (external)",
    "$5,000,000,000": "cover-page example", "36,000": "run-time note, 6 horizons x 3 placebos x 2000 draws", "24": "holdout start day", "30-year": "maturity",
}

POOL_FILES = ["localproj_all.csv", "placebo_matched.csv", "buyback_vs_ai_lp.csv",
              "auction_lp_alltenor.csv"]


def leaves(x, key=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{key}.{k}" if key else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{key}[{i}]")
    elif isinstance(x, bool):
        return
    elif isinstance(x, (int, float)):
        yield key, float(x)


def pool():
    # hand-mapped paper numbers first, so a coincidental match elsewhere never wins
    pn = json.loads((TAB / "paper_numbers.json").read_text())
    out = [(f"paper_numbers.{k}", v["value"]) for k, v in pn.items()]
    out += list(leaves(json.loads((TAB / "headline.json").read_text()), "headline"))
    for f in sorted(TAB.glob("*.json")):
        if f.name not in ("headline.json", "paper_numbers.json"):
            out += list(leaves(json.loads(f.read_text()), f.stem))
    tabs = [TAB / f for f in sorted(p.name for p in TAB.glob("*.csv")) if f != "number_trace.csv"]
    for f in tabs + [PROC / f for f in POOL_FILES]:
        d = pd.read_csv(f)
        for c in d.select_dtypes("number").columns:
            out += [(f"{f.name}:{c}[{i}]", float(v)) for i, v in d[c].dropna().items()]
    return out


NUM = re.compile(r"(?<![\w.])[−\-+~$]?\d[\d,]*(?:\.\d+)?(?:%|bp|B| billion)?")


def tokens(text, where):
    for line in text.splitlines():
        for m in NUM.finditer(line):
            t = m.group(0)
            core = t.lstrip("−-+~$").rstrip("%").replace("bp", "").replace("B", "").replace(" billion", "").replace(",", "")
            if not core or re.fullmatch(r"(19|20)\d\d", core):
                continue
            after = line[m.end():m.end() + 3]
            before = line[max(0, m.start() - 8):m.start()]
            if re.match(r"[-/]\d", after) or re.search(r"(Figure|h ?=|day-|\d-)\s*$", before):
                continue                              # dates, figure numbers, horizon labels
            yield t, core, where, line.strip()[:120]


def traced(core, values):
    nd = len(core.split(".")[1]) if "." in core else 0
    x = float(core)
    for key, v in values:
        for cand in (v, v * 100):
            if round(abs(cand), nd) == x:
                return key
    return None


def main():
    text = "\n".join(p.extract_text() for p in PdfReader(ROOT / "PAPER.pdf").pages)
    readme = (ROOT / "README.md").read_text()
    values = pool()
    rows, seen = [], set()
    for t, core, where, ctx in list(tokens(text, "PAPER.pdf")) + list(tokens(readme, "README.md")):
        if (t, where) in seen:
            continue
        seen.add((t, where))
        if t in CONSTANTS or core in CONSTANTS:
            rows.append(dict(number=t, where=where, source="CONSTANT: " + CONSTANTS.get(t, CONSTANTS.get(core, "")), context=ctx))
            continue
        rows.append(dict(number=t, where=where, source=traced(core, values), context=ctx))
    df = pd.DataFrame(rows)
    df.to_csv(TAB / "number_trace.csv", index=False)
    bad = df[df.source.isna()]
    print(f"{len(df)} distinct numbers, {len(bad)} untraced")
    for _, r in bad.iterrows():
        print(f"  {r['where']:9s} {r['number']:>10s}  {r['context']}")
    return len(bad)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
