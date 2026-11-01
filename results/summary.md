# Results: Saurav, Agarwalla and Varma (2024) recreated from free NSE data

Every number here comes from `scripts/run_study.py`, `scripts/run_trading_test.py` and `scripts/run_sensitivities.py`, run on 2026-11-01. The full tables, with the paper's numbers beside ours, are in `results/main/comparison.md` (2015-2019) and `results/extension_2020_2025/comparison.md`. Page numbers refer to the journal's pages 459-487.

## In plain words

The paper's story holds up on free daily data.

- **Implied volatility rises into earnings and falls after them.** At-the-money implied volatility (ATM-IV) builds up steadily before the announcement, peaks the day before, and drops sharply when the news comes out. In the announcement month it is 0.026 higher than in the month before, which is almost exactly the paper's 0.028.
- **Option trading rises too.** Options volume, measured against stock volume and against futures volume, rises and peaks on the announcement day, as in the paper.
- **The skew and the put-to-call ratio predict the surprise.** The day before the announcement, RR-IV correlates 0.163 with the earnings surprise, against the paper's 0.162. In the paper's regression (equation 5), RR-IV is positive and P/C negative, both at the 1% level, and ATM-IV is not significant. That is the paper's result.

The recreation differs from the paper in three ways:

1. **Days -2 and -3 are less clear-cut.** In the main run RR-IV is significant on those days too, where the paper finds nothing. But it does not survive the stricter or looser liquidity filters in the sensitivity table, so the paper's finding that only day -1 matters is not overturned.
2. **The years 2020 to March 2025 are different.** IV still builds up into earnings, but RR-IV no longer predicts the surprise and P/C only weakly.
3. **The signal cannot be traded.** Going long or short the stock future from the day -1 close to the day 0 close on these signals loses money even before costs. The market has already priced what the options know.

## The sample

| | This study | Paper (page 468) |
|---|---|---|
| Events, 2015-2019 | 2,072 | 2,081 |
| Firms | 184 | 191 |
| Events with SUE | 1,275 | 1,831 |
| Firms with SUE | 134 | not given |

**Events** are first results announcements by NSE shares that had stock futures and traded options on day 0.
- An event is dropped if it falls within three trading days of the near-month expiry.
- It is kept only if the options series expiring after the announcement has a fitted smile on day -1.

**Day 0** follows the paper's rule: an announcement at or after 15:30 belongs to the next trading day. Times come from NSE's announcement feed. A check of day 0: absolute stock returns average 3.5% on day 0, against about 1.8% on the days around it.

**Why fewer events have SUE.** SUE needs 20 quarters of EPS history before the quarter. NSE has no filing file for many 2018 quarters (340 filings have no link), and each gap removes SUE for the next 20 quarters.

## Table 1: the worked example (page 465)

The recreation reproduces every printed cell: strikes, premiums and implied volatilities. RR-IV is 0.00, +1.08 and -1.23 points.

The paper's text writes the strike of the out-of-the-money option in column 3 with 0.3137 instead of 0.3178. The table itself is right.

## Table 5: smile levels by month (page 471)

| Level | Pre-EA month | EA month | Post-EA month | EA − pre (Welch t) | EA − post (Welch t) |
|---|---|---|---|---|---|
| ATM-IV, this study | 0.356 | 0.382 | 0.357 | +0.026 (6.44) | +0.026 (5.99) |
| ATM-IV, paper | 0.383 | 0.411 | 0.372 | +0.028 (6.70) | +0.038 (10.84) |
| IV(Δ=0.75), this study | 0.396 | 0.430 | 0.404 | +0.034 (6.98) | +0.027 (4.95) |
| IV(Δ=0.75), paper | 0.397 | 0.427 | 0.391 | +0.030 (6.42) | +0.036 (9.13) |
| IV(Δ=0.25), this study | 0.393 | 0.424 | 0.397 | +0.031 (6.73) | +0.027 (5.59) |
| IV(Δ=0.25), paper | 0.397 | 0.422 | 0.388 | +0.024 (5.59) | +0.034 (9.21) |

The table covers 1,878 events with at least five fitted days in each of the three months.

The paired t-statistics, which compare the months within each event, are 10 to 16.

## Figures 1 to 5 (pages 472-478)

The charts are in `results/main/figures/`.

**Figure 1.** ATM-IV, divided by its mean in the month before the EA month, follows this path:

| Day | -10 | -5 | -1 | 0 | +1 | +10 |
|---|---|---|---|---|---|---|
| Normalised ATM-IV | 1.06 | 1.14 | 1.26 | 1.13 | 1.06 | 1.03 |

IV at deltas 0.25 and 0.75 follow the same path. The shape is the paper's.

**Figure 2(b).** ATM-IV rises in the same way in every SUE tercile: 1.27 to 1.28 on day -1 in all three. As the paper says (page 472), the rise does not depend on the surprise.

**Figure 3(b).** RR-IV for the large-negative SUE tercile falls from -0.007 on day -2 to -0.017 on day -1 and -0.022 on day 0. The paper's dip is about -0.013. The other two terciles stay near zero.

**Figure 4.** Volume ratios, with the paper's values read off its charts:

| Series | Day -10 | Day -2 | Day -1 | Day 0 | Day +1 |
|---|---|---|---|---|---|
| O/S, this study | 1.21 | 1.28 | 1.74 | 1.97 | 1.67 |
| O/S, paper | 1.05 | 1.22 | 1.52 | 1.63 | 1.46 |
| O/F, this study | 0.43 | 0.46 | 0.65 | 0.80 | 0.72 |
| O/F, paper | 0.46 | 0.51 | 0.64 | 0.71 | 0.68 |

Options volume is notional rupees, which is what NSE's bhavcopy reports.

**Figure 5(b).** P/C in contracts, from day -10 to day 0:

| SUE tercile | Day -10 | Day 0 |
|---|---|---|
| Large negative | 0.46 | 0.60 |
| Middle | 0.47 | 0.53 |
| Large positive | 0.44 | 0.47 |

The paper's peaks are about 0.56, 0.50 and 0.475.

## Tables 3 and 4: descriptive statistics (pages 469-470)

Both tables use the winsorised data that the regressions use.

| Variable | This study: N, mean (st. dev.) | Paper: N, mean (st. dev.) |
|---|---|---|
| SUE | 1,275, -0.018 (1.245) | 1,831, 0.052 (1.089) |
| RR-IV, day -1 | 2,072, -0.010 (0.039) | 2,081, -0.011 (0.060) |
| ATM-IV, day -1 | 2,072, 0.435 (0.112) | 2,081, 0.455 (0.142) |
| P/C, day -1 | 2,072, 0.509 (0.227) | 2,081, 0.124 (0.184) |
| Beta | 2,023, 1.288 (0.605) | 1,971, 1.265 (0.595) |
| Momentum | 2,059, 0.123 (0.359) | 2,080, 0.028 (0.393) |
| Size, log ₹ million | 2,068, 12.473 (1.230) | 2,081, 12.493 (1.269) |

**Correlation with SUE, by day before the announcement.** This study first, the paper second:

| | Day -1 | Day -2 | Day -3 |
|---|---|---|---|
| RR-IV | 0.163 / 0.162 | 0.116 / 0.091 | 0.089 / 0.078 |
| P/C | -0.169 / -0.110 | -0.110 / -0.082 | -0.085 / -0.056 |
| ATM-IV | -0.108 / -0.061 | | |

**The P/C level disagrees.** The paper's Table 3 has a P/C mean of 0.124, but its own Figure 5 shows levels of 0.44 to 0.56. Our P/C in contracts matches the figure, so the paper's Table 3 probably measures P/C differently. Its correlations still agree with ours in sign and roughly in size.

## Tables 6 to 9: does the day -n option market predict SUE? (pages 479-482)

These are the SUE columns of equation 5. Firm fixed effects are always included, and year-quarter effects in column (2) and in Tables 7 and 9.

The controls are beta, momentum, size and BHAR(-10,-2). Analyst coverage, analyst dispersion and institutional holding are dropped: there is no free source for them over 2015-2019.

Stars use classical standard errors, which the paper appears to use, at 1% (\*\*\*), 5% (\*\*) and 10% (\*). The second figure in each cell is the t-statistic with standard errors clustered by firm.

| Table, column | Variable | This study (clustered t) | Paper |
|---|---|---|---|
| 6 (1), n = 1 | RR-IV | 3.259*** (2.41) | 2.168*** |
| | P/C | -0.832*** (-3.47) | -1.078*** |
| | ATM-IV | -0.313 (-0.53) | 0.649* |
| 6 (2), n = 1 | RR-IV | 3.234*** (2.29) | 2.514*** |
| | P/C | -0.805*** (-3.41) | -1.149*** |
| | ATM-IV | -0.391 (-0.61) | 0.416 |
| 7, n = 2 | RR-IV | 3.337*** (2.32) | 0.673 |
| | P/C | -0.409* (-1.76) | -0.700 |
| 7, n = 3 | RR-IV | 2.660** (1.77) | 1.809 |
| | P/C | -0.520** (-2.34) | -0.274 |
| 8 (1), n = 1 | Alt RR-IV | 4.124*** (2.81) | 1.844*** |
| | P/C | -0.801*** (-3.17) | -0.635*** |
| 8 (2), n = 1 | Alt RR-IV | 4.019*** (2.59) | 2.386*** |
| | P/C | -0.776*** (-3.07) | -0.620*** |
| 9, n = 2 | Alt RR-IV | 2.947** (1.74) | 3.010*** |
| 9, n = 3 | Alt RR-IV | 2.522* (1.50) | 2.314* |

**Sample sizes.** Table 6 uses 1,275 events here against 1,729 in the paper. Table 7 uses 1,200 and 1,164 against 1,474 and 1,320.

**Adjusted R².** It is 0.10 to 0.13 with all fixed-effect dummies, and 0.05 to 0.09 within firms. The paper reports 0.014 to 0.043; it does not say which kind it reports.

**Controls that differ from the paper.**
- Momentum is strongly positive here (t 4 to 5), while in the paper it is small or negative. Momentum predicting the earnings surprise is a known effect; the paper's momentum may be defined differently.
- Size and BHAR are not significant here, while the paper finds them significant in some columns.

## Optional trading test: is the signal tradeable?

The paper does not test trading. The approved plan added this test to settle whether the study could become a strategy.

**The rule.**
- At the close of day -1, rank the announcing share's RR-IV, minus its P/C, or the average of the two, against all events of the previous 365 days. Nothing later is used.
- Go long the share's future if the rank is in the top third, and short it if in the bottom third.
- Close at the day 0 close, using the same contract on both days.
- Each trade is 2% of capital.
- The backtest runs on the shared engine with NSE futures costs: brokerage 0.03%, exchange, SEBI and GST charges, stamp duty, and 0.10% market impact a side.

**2015-2019** (1,231 trading days; the daily series counts days without a trade as zero):

| Signal | Trades | Per trade, gross | Hit rate | Gross annual (NW t) | Net annual, STT 0.01% (NW t) | Worst drawdown, net |
|---|---|---|---|---|---|---|
| RR-IV | 1,402 | -0.21% | 46.7% | -1.2% (-1.33) | -2.8% (-3.04) | -13.8% |
| -P/C | 1,407 | -0.17% | 48.6% | -1.0% (-1.42) | -2.6% (-3.67) | -13.7% |
| Both | 1,155 | -0.29% | 46.9% | -1.4% (-1.82) | -2.7% (-3.44) | -14.0% |

**2020 to March 2025** (1,298 trading days):

| Signal | Trades | Per trade, gross | Gross annual (NW t) | Net annual, STT 0.01% (NW t) | Worst drawdown, net |
|---|---|---|---|---|---|
| RR-IV | 1,938 | -0.30% | -2.2% (-2.77) | -4.3% (-5.01) | -20.7% |
| -P/C | 1,911 | -0.12% | -0.9% (-1.29) | -2.9% (-4.09) | -14.3% |
| Both | 1,584 | -0.29% | -1.7% (-2.71) | -3.5% (-4.95) | -16.9% |

**Costs.** A round trip costs 0.29% at the STT of 0.01% in force until September 2024. At the library's 2026 STT of 0.05% it costs 0.33%, and the net losses grow a little (`results/trading_test.csv`).

**Why the signal predicts the surprise but cannot be traded.** On 2015-2019 events, the day -1 RR-IV has a rank correlation of +0.16 with SUE, and SUE has +0.16 with the day-0 futures return. But RR-IV has -0.05 with that return. Shares whose options look bullish have already moved, so the price at the day -1 close has absorbed what the options know. The reviewer's rank regression puts it this way: for a given surprise, shares with a high RR-IV react worse on day 0.

**Review.** The backtest_reviewer subagent checked the test (`results/review/review.md`, with variants in `results/review/variants.csv`). It reproduced every number and found no bug that changes the conclusion. It found one real issue: some events took the day -1 smile from a series expiring on day 0. The fix, using each event's own series, is applied to all the results above, and the numbers moved by a few hundredths of a percent per trade. It also asked for a guard against missed corporate actions in futures prices (IGL, 9 November 2017), which is now in place.

On the reviewer's version, the losses are robust to:
- exiting at day +1;
- using spot instead of futures;
- winsorising the returns;
- the raw sign of RR-IV instead of ranks;
- full-sample terciles.

Settle prices are not a separate check, because on these contracts they equal the close. Entering at day -2 on a day -2 signal earns nothing.

**Verdict.** There is no edge. The loss before costs is statistically clear only for RR-IV in 2020-2025. The study stays non-tradeable, as decided at the Adapt to India gate.

## Extension: January 2020 to March 2025

The extension has 2,844 events and 898 with SUE.

| | 2015-2019 | 2020-Mar 2025 |
|---|---|---|
| ATM-IV, EA month − pre-EA month (Welch t) | +0.026 (6.44) | +0.007 (1.90) |
| Normalised ATM-IV, day -1 → day 0 | 1.26 → 1.13 | 1.27 → 1.10 |
| O/S on day -10 → day 0 | 1.21 → 1.97 | 5.56 → 7.27 |
| O/F on day -10 → day 0 | 0.43 → 0.80 | 2.35 → 3.40 |
| Correlation of RR-IV(day -1) with SUE | 0.163 | 0.108 |
| Correlation of P/C(day -1) with SUE | -0.169 | -0.145 |
| Table 6 (2): RR-IV (t) | 3.234 (2.72) | 1.906 (1.03) |
| Table 6 (2): P/C (t) | -0.805 (-4.00) | -0.435 (-1.76) |

- **Volume.** Options volume grew several-fold after 2020: O/S is about five times its 2015-2019 level.
- **The smile.** IV still jumps into the announcement, but the month-level rise is much smaller.
- **Predicting the surprise.** RR-IV no longer predicts SUE in the regression. P/C does weakly: at the 5% level in column (1) and the 10% level in column (2).

With fewer SUE observations and a retail-heavy options market, the evidence for informed option trading before earnings is weaker after 2019.

## Sensitivity and the number of variants tried

**How many variants were tried.**
- The main specification was fixed in the plan before any result was seen.
- Six variants were run beside it, each changing one choice (`results/sensitivity.csv`):
  - the minimum contracts per option (1 and 20 instead of 5);
  - settle prices instead of closes;
  - a smile fitted to premium errors instead of IV errors;
  - P/C in notional value instead of contracts;
  - the alternative SUE, scaled by the standard deviation of year-on-year changes, which needs 12 quarters instead of 20.
- The trading test ran 3 signals × 2 periods × 2 cost settings.
- No variant was chosen for its result.

| Variant (2015-2019) | Events | SUE events | ATM-IV EA − pre (t) | Table 6 (2) RR-IV (t; clustered t) | Table 6 (2) P/C (t) | Table 6 (2) ATM-IV (t) | Table 7 RR-IV n=2 (t) | Table 7 RR-IV n=3 (t) | Table 8 (2) Alt RR-IV (t) |
|---|---|---|---|---|---|---|---|---|---|
| main (5 contracts, IV error, close) | 2,072 | 1,275 | +0.026 (6.44) | 3.23 (2.72; 2.29) | -0.80 (-4.01) | -0.39 (-0.73) | 3.34 (2.64) | 2.66 (2.03) | 4.02 (3.09) |
| main, P/C in value | 2,072 | 1,275 | +0.026 (6.44) | 3.27 (2.76; 2.32) | -0.88 (-4.00) | -0.44 (-0.81) | 3.37 (2.66) | 2.64 (2.02) | 4.07 (3.13) |
| main, alternative SUE | 2,072 | 1,555 | +0.026 (6.44) | 2.94 (2.52; 2.07) | -0.97 (-4.88) | -0.36 (-0.68) | 3.35 (2.63) | 2.06 (1.57) | 3.75 (2.87) |
| at least 1 contract | 2,361 | 1,422 | +0.025 (5.17) | 1.41 (1.57; 1.38) | -0.84 (-4.82) | -0.28 (-0.58) | 1.14 (1.17) | 1.53 (1.51) | 4.63 (4.15) |
| at least 20 contracts | 1,662 | 1,045 | +0.030 (6.18) | 4.74 (3.28; 2.68) | -0.87 (-3.66) | -0.50 (-0.82) | 4.05 (2.35) | 2.24 (1.29) | 6.07 (3.84) |
| premium-error fit | 2,072 | 1,275 | +0.030 | 4.05 (3.26; 2.79) | -0.77 (-3.81) | -0.93 | 2.90 | 2.61 | 3.09 |
| settle prices | 2,072 | 1,275 | +0.025 (5.90) | 3.40 (2.88; 2.38) | -0.79 (-3.94) | -0.40 (-0.75) | 3.01 (2.40) | 2.97 (2.28) | 4.49 (3.46) |

**What the variants show.**
- **The main findings survive every variant:**
  - the IV build-up (Table 5);
  - P/C on day -1 (t -3.7 to -4.9);
  - ATM-IV is never significant.
- **The skew's strength depends on how liquid the options are,** which is the attenuation the plan expected from noisy daily closes.
  - Requiring at least 20 contracts a day raises the RR-IV coefficient from 3.2 to 4.7 (t 3.3).
  - Allowing single-contract options lowers it to 1.4 (t 1.6).
  - The moneyness-bucket Alt RR-IV is significant in every variant (t 2.9 to 4.2).
- **The signal on days -2 and -3 is not robust.** It weakens with the strict filter (n = 3: t 1.3) and with the loose one (n = 2: t 1.2). The paper's finding that only day -1 matters is therefore not contradicted with confidence.
- **Fitting premium errors keeps day -1 and raises it** (RR-IV 4.05, t 3.3), and it makes days -2 and -3 significant (t 2.9 and 2.6), as the main run does. So the day -2/-3 result depends on the filter, not on the fit.
- **Settle prices change almost nothing,** because for options in the old bhavcopy the settle price equals the close.

## What could not be reproduced, and why

| Paper item | Status | Why |
|---|---|---|
| Panel (a) of Figures 2, 3 and 5; columns (3)-(4) of Tables 6-9; IBES rows of Tables 3 and 4 | Not reproduced | IBES analyst forecasts are not available. That is 8 of the 16 regression columns and 3 of the 6 surprise-split panels |
| Analyst coverage and dispersion controls | Dropped | IBES |
| Institutional holding control | Dropped | No free shareholding history for 2015-2019: NSE's API starts in Sep 2021 and BSE's refuses scripted requests (gap 38) |
| Smile from time-matched tick trades | Approximated | Tick data is paid. Daily closes of options and futures are used instead, with a minimum-contracts filter in place of the five-minute filter |
| Figure A1 (CEIC turnover) | Not reproduced | Not in scope |

## Caveats

- **RR-IV is an approximation.** Option and futures closes are not synchronous. The stand-in filters (contracts traded per day) and the fit objective are tested in the sensitivity table.
- **SUE coverage is lower than the paper's.** It is 1,275 events against 1,831, because missing 2018 filings break the 20-quarter history. The alternative SUE, which needs only 12 quarters, is in the sensitivity table.
- **The paper is silent on several choices,** and the study had to pick one for each:
  - classical or clustered standard errors;
  - whether its R² is a within or a full-dummy figure;
  - whether the smile fit's errors are in price or in IV;
  - whether P/C is in contracts or value;
  - the base month for normalising IV.

  Each choice is documented in `.claude/notes/` and, where it matters, run both ways.
- **Survivorship.** The data are NSE's own files, which include shares that were later delisted, such as Yes Bank, DHFL, Jet Airways and RCOM. Survivorship bias comes only from missing filings.

## Gaps in tradingmachine found by this study

- **Gap 36:** UBI has no expired NSE option or futures contracts, so nothing before 2026.
- **Gap 37:** UBI's option bars are stitched across reused broker tokens.
- **Gap 38:** there is no shareholding-pattern history.

Gaps 25 (results dates) and 30 (no point-in-time F&O list) also applied. This study also found that NSE's results API time is the structured-filing time, a median of 1 day and up to 576 days after the real announcement. NSE's announcement feed gives the real time.
