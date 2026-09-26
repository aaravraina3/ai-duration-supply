"""Check the committed data files against the hashes in data/VINTAGES.md, so a
silent re-download can't change the dependent variable without anyone noticing."""
import hashlib, re, sys
from config import ROOT

rows = re.findall(r"^\| `([^`]+)` .*`([0-9a-f]{64})` \|$", (ROOT / "data" / "VINTAGES.md").read_text(), re.M)
bad = 0
for path, want in rows:
    got = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    ok = got == want
    bad += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {path}")
sys.exit(1 if bad or not rows else 0)
