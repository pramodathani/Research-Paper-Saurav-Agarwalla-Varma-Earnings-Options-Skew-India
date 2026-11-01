# Data

Everything here except this file is git-ignored. Raw files are exactly as the source served them. NSE files are never published; only derived results are. The study's downloaders are in `src/saurav_agarwalla_varma_asymmetric_uncertainty_india/data/` and run through `scripts/`; each skips files already on disk, so a stopped download is simply started again.

The bhavcopy, F&O, corporate action, results-announcement, IIMA, symbol-change and NIFTY 500 files were copied on 2026-11-01 from the Jegadeesh and Titman and Betting-Against-Beta studies' `data/` folders (fetched on 2026-10-31 with the same downloader code), so they were not downloaded twice. The results filings and the UBI exports are new for this study.

| Path | What | Source | Period | Count |
|---|---|---|---|---|
| `ubi/instruments_nse_equities.parquet` | UBI instrument master, NSE shares | `export_instruments` (nse, equities) | listed today | 3,490 instruments |
| `ubi/futures_symbols.csv` | Every symbol that had a stock future (FUTSTK or STF) on any day from 2009 | derived from the F&O bhavcopies | 2009 to 2026-10-30 | 523 symbols |
| `ubi/prices_futures_symbols_day_adjusted.parquet` | Daily candles adjusted for splits and bonuses, not dividends. Cross-check for the 2020 onward extension only (gap 32) | `export_prices` (nse, equities, day) | 2019-12-03 to 2026-10-30 | 589,564 candles, 378 symbols; 145 of 523 have none (delisted, renamed or not listed) |
| `nse/bhavcopy/` | Daily cash-market bhavcopy zips (old format to 2024-07-05, UDiFF after). Stock prices, volumes and returns | `nsearchives.nseindia.com/content/historical/EQUITIES/...`, `/content/cm/BhavCopy_NSE_CM_...` | 1996-01-01 to 2026-10-30 | 7,628 zips; weekdays without a file are in `not_available.txt` |
| `nse/fno/` | Daily F&O bhavcopy zips: every stock option and future, with open, high, low, close, settle price, contracts, notional value and open interest. The smile source | `.../historical/DERIVATIVES/...`, `/content/fo/BhavCopy_NSE_FO_...` | 2005-01-03 to 2026-10-30 | 5,387 zips (4,814 old format to 2024-07-05, 573 UDiFF) |
| `nse/corporate_actions/` | NSE corporate actions API, one JSON per year (splits, bonuses, dividends) | `nseindia.com/api/corporates-corporateActions` | 2000 to 2026 | 27 files |
| `nse/results_dates/` | NSE financial results API, one JSON per quarter: broadcast time, period, consolidated flag, link to the filing | `nseindia.com/api/corporates-financial-results` | 2007 Q1 to 2026 Q4 | 80 files |
| `nse/results_filings/` | The filings themselves, standalone quarterly results of the stock-futures shares, named `SYMBOL__period-end__NSE-file`. Source of EPS before extraordinary items, face value and paid-up capital | The HTML or XBRL link in each `results_dates` row, fetched 2026-11-01 | broadcasts 2010-01 to 2025-04 | 13,435 targets: 13,032 downloaded (7,157 HTML, 5,875 XBRL), 340 with no link, 60 not served, 3 duplicate file names (see below) |
| `nse/iima/` | IIMA four-factor monthly file with RF (risk-free, percent), survivorship-bias adjusted, release 2025-12 | `faculty.iima.ac.in/iffm/...` | 1993-10 to 2025-12 | 1 file, 387 months |
| `nse/symbol_changes/symbolchange.csv` | NSE list of symbol renames | `nsearchives.nseindia.com/content/equities/symbolchange.csv` | 2026-10-31 snapshot | 1,078 rows |
| `niftyindices/total_return/` | NIFTY 500 and other total-return index levels, five-year JSON chunks | niftyindices.com | 1995 to 2026-10-30 | 8 indices |

## Coverage

- **Stock futures universe:** 523 symbols had a stock future on at least one day since 2009. From the results rows, 3,650 candidate firm-quarter events in 2015 to 2019 (669, 713, 776, 789, 703 a year) for 214 firms, each the earliest standalone broadcast with futures trading that day. The paper's final sample is 2,081 events from 191 firms after its smile filters.
- **F&O files:** the stock-option count and the stock-futures count in a mid-year sample file: 2015, 145 symbols; 2016, 173; 2017, 175; 2018, 209; 2019, 200.
- **Results filings, EPS and capital:** of the 13,032 files on disk, 12,892 (98.9%) give EPS before extraordinary items and 12,938 give paid-up capital, by the patterns in `scratch/eps_coverage.py`. Counts by period-end year, files / with EPS:

| Year | Files | EPS | Year | Files | EPS |
|---|---|---|---|---|---|
| 2010 | 830 | 826 | 2018 | 688 | 688 |
| 2012 | 805 | 796 | 2019 | 748 | 748 |
| 2014 | 751 | 743 | 2021 | 772 | 772 |
| 2016 | 951 | 942 | 2023 | 998 | 998 |
| 2017 | 802 | 718 | 2024 | 1,064 | 1,064 |

## Known problems

1. **No derivatives history in UBI** (gaps 36 and 37). The smile uses NSE's daily F&O bhavcopy instead of time-matched trades, so option and futures closes are not synchronous.
2. **No institutional holding for 2015 to 2019.** NSE's shareholding API starts at Sep 2021 (gap 38) and BSE's API refuses plain requests (403 on every endpoint tried, and the old pages redirect to the home page). The control is dropped, as the plan allowed.
3. **Missing filings:** 340 targets have no link at all (211 in 2018 and 107 in 2019, mostly filed under a format NSE did not link), 60 return 404 or an empty page after a retry, and 3 targets share a file name with another (re-filings of the same quarter). The failures are in `nse/results_filings/failed.jsonl`.
4. **Standalone EPS only.** Consolidated quarterly results were optional before April 2019, so standalone is the only series that is complete across 2010 to 2025.
5. **Results announcements after March 2025 are thin** (gap 25), so the extension ends in March 2025.
6. **UBI prices are only a cross-check.** Daily history starts 2019-12-03 and has split and bonus errors (gap 32). Returns come from NSE bhavcopies adjusted with NSE's corporate action list.
7. **Delisted shares** are in the NSE files. Their final-trade losses are not recorded.
8. **Futures symbols and cash symbols can differ** after renames; `symbol_changes` links them in the Build stage.
