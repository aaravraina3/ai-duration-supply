# Data vintages

The NY Fed and Treasury overwrite these files in place, so a fresh download is a
different dataset. The exact files every result was computed on are committed,
and `src/verify_vintage.py` checks them against the hashes below.

| File | Source | Downloaded | Covers | SHA-256 |
|---|---|---|---|---|
| `data/raw/ACMTermPremium.xls` | https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls | 2026-09-23 20:56 ET | daily through 2026-09-22 | `05af9b24144dc1c816cd689d66e41c8057eb45865a2ad331ee3d5d5a7860f94d` |
| `data/processed/acm.csv` | parsed from the file above by `src/data_pull.py acm()` ("ACM Daily" sheet) | 2026-09-23 20:56 ET | daily through 2026-09-22 | `3a14077ec2ae29f0d1964830c40b279db28f583637359dadafef0705a05ef216` |
| `data/raw/auctions_full.json` | https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query?filter=auction_date:gte:2023-06-01&page%5Bsize%5D=10000&format=json | 2026-09-23 17:26 ET | auctions 2023-06-12 through 2026-09-24 | `cceb91eb31ae10204c65a401ddc56f279293c029cc0c07bccd35304f5ffea1b2` |
| `data/processed/gsw.csv` | Fed Board GSW zero curve (feds200628.csv), parsed by `src/data_pull.py gsw()` | 2026-09-23 23:46 ET | as downloaded | `aa6a94fff487abb99895bad21996b24355c1cd5d91bcf423f1b6ed91a9196f20` |
| `data/processed/fred.csv` | FRED series, merged by `src/data_pull.py fred()` | 2026-09-23 17:27 ET | as downloaded | `22ff891aa86a648569b790fb1f606e5d039d84f8e1fa4080c17a0e8a7e6135f1` |
| `data/raw/buybacks.json` | Treasury Fiscal Data buybacks API, `src/buybacks.py fetch()` | 2026-09-19 13:28 ET | as downloaded | `8b06c7ca01dace4e50d5854ddf6999278a027b04066dca95648c8aa1771571a9` |
| `data/raw/fred_DCOILWTICO.csv` | FRED `DCOILWTICO` | 2026-09-23 17:27 ET | as downloaded | `344a4a7cce2b66e4e1d1789b3b15be4a96e24e4cad1d043e5c093be83d51bbcf` |
| `data/raw/fred_DEXJPUS.csv` | FRED `DEXJPUS` | 2026-09-19 16:59 ET | as downloaded | `0ea1de1993e69827ccfdddc390af8f8f5abf15c566f4c4cd5a6072495b773965` |
| `data/raw/fred_DFII10.csv` | FRED `DFII10` | 2026-09-23 23:49 ET | as downloaded | `d87b209d9a81cf7acd1ad5e57a82549b508c5b438221b2dfd4f886659921f9e9` |
| `data/raw/fred_DGS1.csv` | FRED `DGS1` | 2026-09-23 17:27 ET | as downloaded | `629932a71511bbc09bfc8ff7145278aed9280660d9eb4cc36cf1b403f826efdd` |
| `data/raw/fred_DGS10.csv` | FRED `DGS10` | 2026-09-23 17:27 ET | as downloaded | `1216e7715e7a8a31a23109e0806303b58cdd1d591d73649ff812d36c5fa7e8c2` |
| `data/raw/fred_DGS1MO.csv` | FRED `DGS1MO` | 2026-09-23 17:27 ET | as downloaded | `4e1a0ce1a916c7c4fd774792c8d3a666bb8bb88f32e640d0834adcf4caad8835` |
| `data/raw/fred_DGS2.csv` | FRED `DGS2` | 2026-09-23 17:27 ET | as downloaded | `42ac29fbbd6a215d3d2bb1e2e4d8410cd0f13bcb41b08c87fe8cbf001c78a8e7` |
| `data/raw/fred_DGS20.csv` | FRED `DGS20` | 2026-09-23 17:27 ET | as downloaded | `23c9549b77db577742f62913b982d70c9b481576fd41ff40813c7fdd933579ec` |
| `data/raw/fred_DGS3.csv` | FRED `DGS3` | 2026-09-23 17:27 ET | as downloaded | `0791bf3c37c4ffaf1e7e4d221b1911c4532b169c979d0e90db9360766bc5095a` |
| `data/raw/fred_DGS30.csv` | FRED `DGS30` | 2026-09-23 17:27 ET | as downloaded | `2d7c5b191e3577dbec3ae5a1609337e8d1227fc44a8b8d9df32d78a888b6b38d` |
| `data/raw/fred_DGS3MO.csv` | FRED `DGS3MO` | 2026-09-23 17:27 ET | as downloaded | `e5b1e895403017ba74bcfcc4e592da130989784eca5f6c2197c6e7168e9d9155` |
| `data/raw/fred_DGS5.csv` | FRED `DGS5` | 2026-09-23 17:27 ET | as downloaded | `7b6013097c1874f53f60fbfaab4eb5dd4b685cb652c4fb212cdfcbf8de90dfef` |
| `data/raw/fred_DGS6MO.csv` | FRED `DGS6MO` | 2026-09-23 17:27 ET | as downloaded | `764451a85b226f65f07583b7f9b90f63b521d73da2b1512281e389ab9d154eec` |
| `data/raw/fred_DGS7.csv` | FRED `DGS7` | 2026-09-23 17:27 ET | as downloaded | `2562fd13ca12d8e63b441f99d9be91c964f296b7ecb270d922b239692121fd96` |
| `data/raw/fred_DTB3.csv` | FRED `DTB3` | 2026-09-19 16:59 ET | as downloaded | `68c3692a8bf044b95bde0ab86344edff75e10402dca25821f1dd1227ddf0a89a` |
| `data/raw/fred_IR3TIB01JPM156N.csv` | FRED `IR3TIB01JPM156N` | 2026-09-19 16:59 ET | as downloaded | `cf59cf5ebc469237a03721a27fe08d261fb770d06df49fc1c269848634d92fea` |
| `data/raw/fred_IRLTLT01JPM156N.csv` | FRED `IRLTLT01JPM156N` | 2026-09-19 16:59 ET | as downloaded | `12ae6267ae2ae67135bdb2ad17696d91c07e8142a5d3615f182e1626b640128c` |
| `data/raw/fred_T10YIE.csv` | FRED `T10YIE` | 2026-09-23 17:27 ET | as downloaded | `dc1be0f45ccb2b4215d1b5cf1213842c9b060e73a0f659b9ca432611fa69b6fa` |
| `data/raw/fred_T5YIE.csv` | FRED `T5YIE` | 2026-09-23 17:27 ET | as downloaded | `c04bc345b0649676fdf9c2d28ecb156ec58b52dd1ebcfea5cfc5eeff456f0e15` |
| `data/raw/fred_VIXCLS.csv` | FRED `VIXCLS` | 2026-09-23 17:27 ET | as downloaded | `675f9bcb86ee88799f8f7a8b7ee9c30f7a0be26a26df8f9549bddf9e84c4a598` |
| `data/processed/fred_extra.csv` | merged by `src/data_pull.py fred_extra()`; used only through `SAMPLE_END` | 2026-10-13 16:36 ET | runs past `SAMPLE_END`; cut in code | `22802333934cf25cd809f90bc2cbfb9617e262e5329d99aae2549f2f45459a59` |
| `data/raw/fred_THREEFYTP10.csv` | FRED `THREEFYTP10` | 2026-10-13 16:36 ET | runs past `SAMPLE_END`; cut in code | `63935c995156c181028cc56fa71f62b1a32c0e720012964231425fc112d54565` |
| `data/raw/fred_WSHOMCB.csv` | FRED `WSHOMCB` | 2026-10-13 16:36 ET | runs past `SAMPLE_END`; cut in code | `b904c87cfcdf813fdeaeb27463c7f0de8470f5c7e5dbb87a9eef4e2eaf1d57fd` |
| `data/raw/fred_BAA10Y.csv` | FRED `BAA10Y` | 2026-10-13 16:36 ET | runs past `SAMPLE_END`; cut in code | `d68146535f8f2951a29f2854a1bd5eeac1bc67c4d92f4a471eaa9ba8dff68aed` |

The dependent variable is `ACMTP10` from `acm.csv`. A comparison against a
2026-09-17 download found no revisions to overlapping dates
(`research/09_ADVERSARIAL_REVIEW.md`).

The auction file runs two days past `SAMPLE_END`. Everything that uses it is cut at
`SAMPLE_END` (2026-09-22) in code, including the coupon duration shares in
`output/tables/headline.json`.
