"""Project-wide constants. Everything that could be a researcher degree of freedom
lives here and is set ONCE, before looking at outcomes."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "output"
FIG = OUT / "figures"
TAB = OUT / "tables"
for _p in (RAW, PROC, OUT, FIG, TAB):
    _p.mkdir(parents=True, exist_ok=True)

SEC_UA = "Northeastern University Research raina.aa@northeastern.edu"

# ---------------------------------------------------------------- sample
SAMPLE_START = "2024-01-01"
SAMPLE_END   = "2026-09-22"     # last ACM + FRED day. GSW lags to 2026-09-18.
# Every module reads this. Hardcoded end dates are how the samples drifted apart.

# ---------------------------------------------------------------- universe
ISSUERS = {
    "0001018724": "Amazon",
    "0001652044": "Alphabet",
    "0001326801": "Meta",
    "0000789019": "Microsoft",
    "0001341439": "Oracle",
}
ROBUSTNESS_ISSUERS = {      # used only in the §4 robustness sample
    "0001045810": "Nvidia",
    "0001730168": "Broadcom",
    "0001769628": "CoreWeave",
    "0001045609": "Digital Realty",
    "0001045810_x": "unused",
}

# ------------------------------------------------- PRE-REGISTERED CHOICES
# (fixed before any yield data was merged onto the event list)
JUMBO_USD = 10e9          # §3.3 total deal size threshold
# §3.4. The doc pre-registered +/-3 business days. That rule is infeasible here:
# it retains N=1 of 12 jumbos, because issuers deliberately price 1-3 days AFTER
# FOMC/CPI/NFP, so a symmetric 3-day filter is close to a filter on issuance
# itself (37% of business days are "clean", but only 8% of jumbos survive).
# PRIMARY RULE is therefore window contamination: drop an event if a top-tier
# release falls inside the t-1..t+1 return window actually being measured.
# The original +/-3 is reported as a robustness row, not discarded.
MACRO_EXCL_BDAYS = 1
MACRO_EXCL_LADDER = [0, 1, 2, 3]
EXCL_BAND_YEARS = 2.0     # §4.4 +/- band around a tranche maturity -> "target"
EVENT_WINDOW = (-1, +1)   # t-1 close to t+1 close, in business days
CLUSTER_MERGE_BDAYS = 4   # §6 two jumbos within N bdays are one event
NLP_HALFLIFE_DAYS = 30    # §4.6 exponential decay half-life, set a priori
HMM_K = 3                 # §4.7
HMM_RESTARTS = 20
N_PLACEBO = 2000          # randomized event dates

# FRED tenor grid (par yields)
FRED_TENORS = {
    "DGS1MO": 1/12, "DGS3MO": 0.25, "DGS6MO": 0.5, "DGS1": 1.0,
    "DGS2": 2.0, "DGS3": 3.0, "DGS5": 5.0, "DGS7": 7.0,
    "DGS10": 10.0, "DGS20": 20.0, "DGS30": 30.0,
}
FRED_CONTROLS = ["T5YIE", "T10YIE", "DCOILWTICO", "VIXCLS"]

# PCA / concession tenor grid (years). Long end is what we care about.
PCA_TENORS = [0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

RANDOM_SEED = 20261015
