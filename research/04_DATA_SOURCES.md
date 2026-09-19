# Data sources

Everything free. Endpoint, what it gives, what it costs you. Verified working on
19 September 2026 unless noted.

---

## Working

| Source | Endpoint | Frequency | Notes |
|---|---|---|---|
| Treasury par curve, controls | `fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>` | Daily | `DGS1MO`..`DGS30`, `T5YIE`, `T10YIE`, `DCOILWTICO`, `VIXCLS`, `DFF`, `SOFR`, `DTB3`. No API key needed for the CSV endpoint |
| GSW zero curve | `federalreserve.gov/data/yield-curve-tables/feds200628.csv` | Daily | 16MB. `SVENY01`..`SVENY30`. Header block precedes the real header row, find the line starting `Date,` |
| ACM term premium | `newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls` | Daily | **Read the "ACM Daily" sheet.** The default sheet is monthly and will silently give you 783 rows. Needs `xlrd` |
| SEC filings index | `data.sec.gov/submissions/CIK<10-digit>.json` | As filed | Recent block plus overflow files. Requires a real User-Agent with contact info |
| SEC documents | `sec.gov/Archives/edgar/data/<cik>/<accession>/<doc>` | As filed | Rate limit politely, ~0.25s between requests |
| Treasury auctions | `api.fiscaldata.treasury.gov/.../od/auctions_query` | Per auction | 1457 records from 2023-06. URL-encode the brackets as `page%5Bsize%5D` |
| Treasury buybacks | `api.fiscaldata.treasury.gov/.../od/buybacks_operations` | Per operation | 223 operations back to 2000-03. Has `maturity_bucket` and `total_par_amt_accepted` |
| FOMC calendar | `federalreserve.gov/monetarypolicy/fomccalendars.htm` | Per meeting | Strip `(Released ...)` spans first, those are minutes not meetings. Require a dash range to get the 8 two-day meetings |
| BLS releases | `bls.gov/schedule/<year>/<MM>_sched.htm` | Monthly grid | One page per month. Grid is Mon-Fri only, so a month starting on a weekend never shows a cell numbered 1. Segment on falling day numbers and take the longest run |
| Japan 10Y | FRED `IRLTLT01JPM156N` | **Monthly** | Last 2026-08-01 at 2.940% |
| Japan 3m | FRED `IR3TIB01JPM156N` | **Monthly** | Last 2026-07-01 at 1.458% |
| USDJPY | FRED `DEXJPUS` | Daily | Publishes with a lag, last 2026-09-11 |

---

## Not available free, and what it costs the project

| Wanted | Why | Status |
|---|---|---|
| Security-level Treasury quotes (TRACE, CRSP) | The only way to measure maturity-localized concession. Published curves are pre-smoothed | Paid. **This is the binding constraint on H2** |
| Agency MBS issuance | Named half of the sell-side "corporate and MBS" claim | SIFMA xlsx endpoints 404, no FRED equivalent found. **Untested and untestable here** |
| Daily JGB curve | Would make the Japan channel daily instead of monthly | MOF CSV endpoints return an HTML error page. `jgbcm.csv` and the English path both fail. Retry the BOJ statistics portal |
| Earnings call transcripts | Forward capex language ahead of filings | Not SEC filings, not free. Substituted 10-K/10-Q MD&A |
| Swap spreads | Would sharpen the H10 flow-vs-premium test | No free daily source found yet |
| IG corporate issuance aggregate | Denominator for "how much of corporate supply is AI" | SIFMA, same 404 problem |

---

## Traps hit, so they are not hit twice

**ACM defaults to monthly.** `pd.read_excel` on the workbook gives you the
"ACM Monthly" sheet, 783 rows, and nothing warns you. Pass
`sheet_name="ACM Daily"`.

**TreasuryDirect's `/TA_WS/securities/auctioned` ignores date parameters** and
caps at 250 rows regardless of what you ask for. It silently returns the most
recent 250. Use the Fiscal Data API instead.

**No parquet engine in this environment.** Everything caches to CSV.

**FRED holiday rows are `.` not blank.** Coerce with `errors="coerce"` or you get
object dtype columns that fail silently downstream.

**SEC 424B5 filings are mostly preliminary.** A preliminary has every dollar
amount blank and is filed on announcement morning. The final is filed one to two
days later. Using the final's filing date as the event date introduces a
two-day look-ahead. Take the date from the FWP `Trade Date:` field instead.

**Currency is only visible in the document.** Alphabet and Amazon file EUR, GBP
and JPY deals through the same form types on adjacent days. Read the currency
symbol off the cover page tranche lines; do not assume USD.

**The 2025 Q4 macro calendar is unreliable.** The 1 Oct to 12 Nov 2025 government
shutdown disrupted BLS releases. My parser found 11 CPI releases in 2025 instead
of 12 and irregular 2026 payroll dates. That is real, not a parse bug.

**Treasury coupon auction sizes have been constant since May 2026.** Any
regression using auction size as a supply proxy has almost no identifying
variation in the back half of the sample. I drew a wrong conclusion from this
before noticing.
