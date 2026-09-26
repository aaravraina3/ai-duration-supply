# Data vintages

The NY Fed and Treasury overwrite these files in place, so a fresh download is a
different dataset. The exact files every result was computed on are committed,
and `src/verify_vintage.py` checks them against the hashes below.

| File | Source | Downloaded | Covers | SHA-256 |
|---|---|---|---|---|
| `data/raw/ACMTermPremium.xls` | https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls | 2026-09-23 20:56 ET | daily through 2026-09-22 | `05af9b24144dc1c816cd689d66e41c8057eb45865a2ad331ee3d5d5a7860f94d` |
| `data/processed/acm.csv` | parsed from the file above by `src/data_pull.py acm()` ("ACM Daily" sheet) | 2026-09-23 20:56 ET | daily through 2026-09-22 | `3a14077ec2ae29f0d1964830c40b279db28f583637359dadafef0705a05ef216` |
| `data/raw/auctions_full.json` | https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=auction_date:gte:2023-06-01&page%5Bsize%5D=10000&format=json | 2026-09-23 17:26 ET | auctions 2023-06-12 through 2026-09-24 | `cceb91eb31ae10204c65a401ddc56f279293c029cc0c07bccd35304f5ffea1b2` |

The dependent variable is `ACMTP10` from `acm.csv`. A comparison against a
2026-09-17 download found no revisions to overlapping dates
(`research/09_ADVERSARIAL_REVIEW.md`).

The auction file runs two days past `SAMPLE_END`. Everything that uses it is cut at
`SAMPLE_END` (2026-09-22) in code, including the coupon duration shares in
`output/tables/headline.json`.
