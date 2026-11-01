# Plan: recreating Saurav, Agarwalla and Varma (2024) from free NSE data

Written 2026-11-01 for the Adapt to India gate. Page numbers refer to the journal's pages 459-487. paper/summary.md has the method and every target number.

## In short

The paper is already an Indian study, so "adapting to India" here means swapping paid data for free data.

- **Smile:** fitted from the daily F&O bhavcopy instead of tick data.
- **Fundamentals:** from NSE results filings instead of Prowess.
- **Surprise:** SUE only, because IBES is not available.

The scope is the agreed one: Table 1, Table 5, Figure 1, Figure 4, panel (b) of Figures 2, 3 and 5, and the SUE columns of Tables 6 to 9, plus the non-IBES rows of Tables 3 and 4.

The main sample is January 2015 to December 2019. An extension to March 2025 follows once the main result is done, ending there because NSE's results API thins out after March 2025 (gap 25).

**Verdict: not tradeable as it stands** (section 9). An optional test could change that.

## 1. What changes and why

| Item | Paper | This study | Why |
|---|---|---|---|
| Universe | NSE firms with stock derivatives, 2015-2019; 191 firms, 2,081 firm-quarters (page 468) | Every symbol with a stock future (FUTSTK) on the event date, from the F&O bhavcopy, point in time and including firms that later left F&O or were delisted | UBI has no point-in-time F&O list (gap 30) and no expired contracts (gap 36) |
| Dates | Jan 2015 to Dec 2019 | Same. Extension: Jan 2020 to Mar 2025 | Results dates are usable only to Mar 2025 (gap 25) |
| Option and futures prices | Time-matched trades from the NSE trade book, five-minute filter (page 463) | Daily F&O bhavcopy: option CLOSE (the same as SETTLE_PR for options), with the futures CLOSE of the same expiry as the forward | Tick data is paid. **This is the main compromise:** option and futures closes are not synchronous |
| Liquidity filter | Traded for at least five minutes | At least N contracts traded in the day (main N = 5; sensitivity N = 1 and 20) | No intraday data |
| Risk-free rate | RBI 91-day T-bill | IIMA's monthly RF series (based on the 91-day T-bill), to Dec 2025 | Not in UBI (gaps 15 and 34). Its effect on one-month IVs is negligible |
| Announcement time | NSE announcement pages, cross-checked with IBES | `broadCastDate` from NSE's financial-results API, already downloaded by the Jegadeesh and Titman study for 2007-2026 | Same source as the paper, minus the IBES cross-check |
| EPS for SUE | Prowess: EPS before extraordinary items | NSE results filings. HTML pages to mid-2018 give "EPS before extraordinary items, basic". XBRL from 2018 gives `BasicEarningsLossPerShareFromContinuingOperations`. Both were checked on real filings (RELIANCE Q1 FY20 consolidated: ₹17.05) | Free source. Standalone EPS throughout, because consolidated quarterly results were optional before April 2019 |
| IBES surprise, analyst coverage and dispersion | IBES | Dropped | No free source |
| Stock returns, volume, beta, momentum, BHAR | CMIE Prowess | NSE equity bhavcopy, adjusted with NSE's corporate-action list, as in the two earlier studies | Same as their method. UBI starts only in Dec 2019 and its adjustments have errors (gap 32) |
| Size | Prowess market capitalisation | Shares outstanding = paid-up equity capital / face value, from the latest results filing, times the bhavcopy close; log of the average in the month before the EA month, in ₹ million | No market capitalisation in UBI (gap 10) |
| Institutional holding | Prowess | **Not available for 2015-2019 so far.** NSE's shareholding API starts at Sep 2021, and BSE's old pages redirect (gap 38). The Data stage tries BSE's JSON API once more; failing that, this control is dropped | See section 7 |
| Benchmark for beta and BHAR | Not named ("the market") | NIFTY 500 total-return index (already downloaded) | Broadest free total-return index |

Trading hours, costs, settlement and short selling barely matter for the main study, because it is an event study with regressions and has no portfolio. Where they do matter:

- **Trading hours** (09:15-15:30 IST) decide day 0. An announcement broadcast at or after 15:30 moves to the next trading day. One broadcast before 09:15 counts as that same day. One during the session is day 0 (Berkman and Truong 2009, as in the paper, page 468).
- **Settlement:** NSE stock options are European. They moved from cash to physical settlement in phases from July 2018 to October 2019, which can change expiry-week behaviour. Each stock's settlement type is recorded so 2018-2019 can be checked separately.
- **Costs and short selling** apply only to the optional trading test in section 9. Stock futures there avoid the cash-market short-sale problem.

## 2. Data sources and what is already on disk

| Data | Source | State |
|---|---|---|
| F&O bhavcopy 2005-2026 (5,387 files) | nsearchives `content/historical/DERIVATIVES/...` | Already downloaded by the Jegadeesh and Titman study. To be copied, as the BAB study did |
| Equity bhavcopy 1996-2026 | nsearchives | Already downloaded. To be copied |
| Corporate actions 2000-2026 | NSE API | Already downloaded. To be copied |
| Results announcements 2007-2026 (80 quarterly JSON files) with broadcast time, period, consolidated flag, HTML or XBRL link | NSE `corporates-financial-results` API | Already downloaded by the Jegadeesh and Titman study. To be copied |
| EPS, face value, paid-up capital per filing | The HTML or XBRL link in each results row | **New download:** about 30,000 standalone filings for F&O firms 2010-2025, one request each. Run as a resumable job |
| NIFTY 500 total-return index | niftyindices.com | Already downloaded by the BAB study |
| IIMA RF | IIMA | Already downloaded |
| Institutional holding | BSE API (to be tried) | Unknown |

UBI supplies none of the derivative data (gaps 36 and 37). It is used only to cross-check stock closes for 2020 onward in the extension.

## 3. How the measures are built

### 3.1 Events

1. Take the quarterly results rows. For each symbol and quarter end, use the earliest standalone broadcast as the event. Later rows are re-filings, such as INFY's March 2019 results re-filed on 4 Sep 2019.
2. Map the broadcast to day 0 by the rule in section 1.
3. Keep events where the symbol has a stock future on day 0 and a near-month series that expires after day 0.
4. Drop events within three trading days of that expiry (page 468).

### 3.2 SUE

1. EPS series per firm: standalone, quarterly, and adjusted for splits and bonuses with the corporate-action factors so that every quarter is per current share.
2. Expected EPS: E[X_q] = X_{q-4} + the mean of the last eight changes X_{q-n} - X_{q-n-4}, for n = 1 to 8.
3. SUE = (X_q - E[X_q]) / σ, with σ the standard deviation of the eight previous quarters' surprises. Each of those surprises is computed the same way, so each SUE needs 20 quarters of history; that is why EPS is fetched from 2010.
4. If that leaves too few events, a fallback σ is the standard deviation of the eight seasonal changes. The choice is reported.

### 3.3 Smile per stock-day

Only the event's near-month series is used.

1. The forward is that expiry's futures close.
2. Time to expiry is calendar days to expiry / 365.
3. Implied volatility is Black (1976) on each option's close.
4. Drop contracts:
   - below the contracts filter;
   - with a price outside Black's bounds;
   - with no solvable IV.
5. Keep a stock-day only if at least seven contracts remain, with at least one call and one put.
6. Convert put deltas to call deltas (Δ_call = Δ_put + 1 under Black on futures, ignoring discounting).
7. Fit IV = aΔ² + bΔ + c with Nelder-Mead, with weights equal to the log of premium traded value. Enforce a ≥ 0 and the paper's shift of c (page 463).
   - **Main fit:** squared errors in IV.
   - **Sensitivity:** squared errors in price.
   - The paper's wording is ambiguous between the two.
8. From the fit:
   - ATM-IV = IV(0.5).
   - IV(0.75) and IV(0.25).
   - RR-IV = IV(0.25) - IV(0.75).
9. **Alternative smile (Tables 8 and 9):** the Xing, Zhang and Zhao moneyness buckets with volume-weighted IV (page 479).

Days after the event series expires use the next month's series. The figures mark that day.

### 3.4 Volume ratios per stock-day, over all expiries

The old F&O bhavcopy's `VAL_INLAKH` for options is notional value, (strike + premium) × quantity. This was checked on INFY, 14 Jul 2017.

- **O/S:** options notional / stock traded value. Across 213 stocks on 14 Jul 2017: mean 1.23, median 0.90. The paper is about 1.05 at day -10.
- **O/F:** options notional / futures value. On the same day: mean 0.44. The paper is about 0.46.
- **P/C:** put contracts / call contracts. On the same day the mean was 0.36, and 0.33 in value.
  - The paper's Figure 5 is about 0.44 and Table 3 is 0.124, which disagree with each other.
  - Both the contracts and the value versions are computed, and the report says which one matches.

### 3.5 Controls

- **Beta:** 60-month rolling regression on the NIFTY 500 total-return index, lagged one month.
- **Momentum:** months t-12 to t-1.
- **Size:** as in section 1.
- **BHAR:** the stock's buy-and-hold return from day -10 to day -2. The main version is raw, as the paper's Table 2 reads. The market-adjusted version is a sensitivity check.
- **Institutional holding:** if found (section 7).
- **Winsorising:** every variable at the 5th and 95th percentiles (page 468).

## 4. What is reproduced, and how it is compared

| Paper item | Output | Comparison with the paper |
|---|---|---|
| Table 1 | Exact recomputation | Already matched in a quick check: RR-IV 0.00 / +1.08 / -1.23 |
| Table 5 | Raw IV levels in the pre-EA, EA and post-EA months; difference t-tests (Welch, plus paired by event) | Levels 0.37-0.43, differences +0.024 to +0.038, t = 5.6-10.8 |
| Figure 1 | Normalised ATM-IV, IV(0.75), IV(0.25), days -10 to +10, each divided by its mean over the calendar month before the EA month | Rise to day -1, sharp drop at day 0 |
| Figure 2(b), 3(b), 5(b) | The same window by pooled SUE tercile | Large-negative RR-IV dip of about -0.012 at days -1 and 0; P/C peak about 0.56 for large negative |
| Figure 4 | O/S and O/F, days -10 to +10 | Peak on day 0, about 1.63 and 0.71 |
| Tables 3 and 4 (non-IBES rows) | Summary statistics and correlations | N, means and correlations |
| Tables 6 and 7, columns (1)-(2) | Equation 5 at n = 1, 2, 3 with firm FE, and with firm plus year-quarter FE | RR-IV 2.168*** / 2.514*** and P/C -1.078*** / -1.149*** at n = 1; nothing significant at n = 2 or 3 |
| Tables 8 and 9, columns (1)-(2) | The same with Alt RR-IV and Alt ATM-IV | Alt RR-IV 1.844*** / 2.386*** at n = 1; 3.010*** and 2.314* at n = 2 and 3 |

The regressions use OLS with fixed effects and show two kinds of standard error:
- classical standard errors, which are what the paper appears to use, since no clustering is stated;
- firm-clustered standard errors, as a robustness check.

The specification drops analyst coverage and dispersion, and possibly institutional holding. One check of how stable the results are to that is to rerun on the paper's other controls one at a time.

**Not reproduced:** panel (a) of Figures 2, 3 and 5, columns (3)-(4) of Tables 6-9, and the IBES, coverage and dispersion rows of Tables 3 and 4. That is 8 of the 16 regression columns and 3 of the 6 surprise-split panels, all for lack of IBES. Figure A1 (from CEIC) is shown only from bhavcopy totals.

**Variants are counted.** The main specification is fixed now, as above. Each sensitivity run is listed with its count in the results:
- contracts filter: 3 values;
- fit objective: 2;
- P/C units: 2;
- BHAR definition: 2;
- standard errors: 2.

## 5. Tests (no network)

1. Black-76 price and IV inversion against hand-computed values, including the arbitrage-bound rejection.
2. Table 1 recomputed exactly, as an end-to-end check of the pricing code.
3. Put-to-call delta conversion, and the quadratic fit's constraint shift on made-up smiles with known a, b and c.
4. Day-0 mapping: in-session, after 15:30, before 09:15, and a broadcast on a Friday evening or the day before a holiday.
5. Near-month selection and the three-day expiry filter, including an EA on expiry day and one in expiry week.
6. SUE on a hand-made 24-quarter EPS series with a known answer; a missing quarter; a split in the middle of the history.
7. Earliest-broadcast de-duplication when a quarter has re-filings.
8. Normalisation base month across a year end; pooled tercile split with ties.
9. Volume ratios on a five-row bhavcopy sample; a stock with no futures that day.
10. Parsers for both the HTML and the XBRL results formats and both bhavcopy formats, run on saved sample files.
11. The regression on simulated data with a known β and fixed effects.
12. One end-to-end run on a tiny synthetic market (three stocks, two quarters) before the Results stage.

## 6. Where the Indian version cannot match the paper, and what that may do

1. **Asynchronous daily closes, not time-matched trades.** An option's last trade can be hours older than the futures close, so its IV carries noise from the futures move in between. That noise hits deep in- and out-of-the-money contracts hardest, which are exactly the ones that set RR-IV. Expect RR-IV to be noisier and its coefficient to shrink towards zero.
   - If the RR-IV result is weaker here, that can mean either that the data is worse or that the effect is weaker. The two cannot be fully told apart.
   - The contracts-filter sensitivity helps: if RR-IV strengthens as the filter tightens, noise is the likely cause.
2. **No IBES.** The analyst-expectations check of the informed-trading story is lost, and SUE and IBES surprise correlate at only 0.17 (page 469). The SUE results are the paper's weaker set: lower adjusted R², 0.028 against 0.140.
3. **Standalone EPS and filings-based events** may differ from Prowess's choices, so the event counts will not match 2,081 and 1,831 exactly.
4. **No institutional holding unless BSE works.** Its paper coefficient is small (0.016*), and firm fixed effects absorb level differences, so dropping it should matter little. The report will say so.
5. **Survivorship.** The NSE files include firms that were later delisted, so there is no survivorship bias from the data source. Events are lost only where results filings are missing.

## 7. Decisions for the user

1. **Institutional holding.** Drop it if BSE's API fails, rather than paying for Prowess. I recommend dropping it.
2. **Optional trading test** (section 9). I recommend running it after the main result.

## 8. Order of work after the gate

1. **Data:** copy the existing NSE files, download about 30,000 results filings as a resumable job, and try BSE for shareholding.
2. **Build and test:** pricing and smile, events and SUE, volume ratios, controls, regressions, each in its own commit with tests.
3. **Results:** in the order Table 1, 5, Figure 1, 4, 2(b), 3(b), 5(b), Tables 3-4, 6-9, then the sensitivity runs and the 2020-2025 extension.

## 9. Is it tradeable?

**Not as the paper stands.**

- The paper tests whether a market feature exists: whether the skew and P/C carry information about the coming surprise. It does not test a portfolio rule.
- Its regressions explain little of the surprise. Adjusted R² is 0.028-0.038 with SUE, including firm fixed effects, which a live trader cannot use for a new event.
- The signal is significant only one day before the announcement.
- It predicts the accounting surprise, not a tradeable return.

**A test that could change this verdict** (optional, after the main result):
- **Rule:** at the close of day -1, rank that day's announcing F&O stocks by RR-IV, or by P/C. Go long the stock future of the top group and short the bottom group, and close at the close of day 0 or day +1.
- **Costs:** run through the shared backtesting engine with futures costs. The result is reported before and after costs, with Newey-West t-statistics, the number of periods and the worst drawdown, as ResearchRules.md requires.
- **Review:** checked by the backtest_reviewer.

If the test survives costs out of sample (2020-2025), I would revise the verdict to tradeable at that point.
