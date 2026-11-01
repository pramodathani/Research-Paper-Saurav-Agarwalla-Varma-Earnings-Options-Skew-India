# Review: event futures trading test (results/trading_test.csv)

Reviewer: backtest_reviewer, 2026-11-01. Scratch scripts are in /tmp/rev (build.py, check1-4.py, variants.py, panel.py). Variant table: results/review/variants.csv.

## What was tested
This is an extension. Saurav, Agarwalla & Varma (2024) have no trading test. Universe: kept NSE F&O earnings events with a smile on day -1 (2015-19: 2,124; 2020-Mar 2025: 2,863+). Signal: trailing 365-day percentile (min 150 earlier events) of RR-IV(t-1), of -P/C(t-1) and of their mean. Long if >= 2/3, short if <= 1/3, 0.02 of capital per trade. Trade: day -1 close to day 0 close on the same futures expiry. FuturesCosts(impact 0.001), STT 0.01% or 0.05%.

## Reproduction
My own rebuild gives the same trade counts, means and hit rates as trading_test.csv on every row: RR-IV 2015-19 has 1,433 trades, mean -0.265%, hit 0.466. Net mean daily -0.000128392 matches the file. On the busiest day (2017-11-13, 15 trades) the hand-computed gross return of -0.2230% equals the engine's. Tests: 6/6 trading tests and 143/143 study tests pass.

## Look-ahead
- Day 0: no sample broadcast falls at or after 15:30 on day 0's own date, and none falls before the day -1 close. 1,991 events were announced during day 0's session, which is fine for a day -1 entry.
- Percentile: only events with day0 strictly earlier are used, and their signals date from day -2 or earlier. Same-day events are left out, which is conservative. In 2015, all 400 events have enough history.
- Sample screens: "options traded on day 0" drops 0 events that had a smile on day -1. The 3-day-to-expiry screen uses the expiry calendar, which is known in advance. Neither has an effect.
- Entering at day -2 while using the day -1 signal is look-ahead. P/C(t-1) is driven by the day -1 move (Spearman with ret(-2→-1) = -0.226), and a -2→-1 'trade' earns +0.54%/+0.80% with t 8.3/17.8. The honest day -2 signal with day -2 entry is below.

## Contract and dates
The same (symbol, expiry) is used on both days, and the expiry is strictly after day 0. 401 events (142 in 2015-19) have a near-month series that expires on day 0. For those, the RR-IV signal comes from a 1-day-to-expiry smile while the trade uses the next month. Dropping them gives -0.229% (t -1.56). Settle versus close: the largest difference on any event key is 0.018%, so the settle variant is not an independent test. Futures versus spot day-0 returns correlate at 0.966. There is one unadjusted corporate action, IGL on 2017-11-09 (futures -80.3%, spot -1.1%). It was not traded (direction 0), but nothing in the code guards against such cases.

## Costs
Round trip = 0.2871% at STT 0.01% (0.1396% buy + 0.1476% sell), so both legs are charged. A double-impact (0.002) rerun with run_backtest (results/review/rriv_2015_2019_impact_0.002) gives a round trip of 0.487-0.527%, net cumulative -0.215 (STT 0.01%) versus -0.158 at base, and periods_with_unpriced_weight = 0. STT and the exchange charge are flagged as unverified. Oct 2024-Mar 2025 should use STT 0.02%, not 0.01%; this is minor. The last day's exit is not charged (close_at_end False); this is negligible. Gap 35 (no roll cost) does not apply because no position is held past one day.

## Fragility (mean % per trade, iid t / day-clustered t)
See variants.csv. RR-IV 2015-19 / 2020-25:
- base: -0.265 (-1.91/-2.00) / -0.311 (-2.94/-1.98)
- exit +1: -0.330 (-2.01/-2.55) / -0.415 (-2.66/-1.72)
- day -2 signal and entry: -0.104 (t -0.64) / -0.084 (t -0.71)
- raw sign of RR-IV: -0.097 (-0.85) / -0.255 (-2.99)
- spot returns: -0.263 (-1.93) / -0.294 (-2.94); winsorised 1/99: -0.245 / -0.309; in-sample terciles 2015-19: -0.253 (-1.80)
- by year: negative in 10 of 11 years (2022: +0.04)
- P/C day-clustered t: -0.93 / +0.65; combined signal: -1.21 / -0.79

## Interpretation
The SUE correlations are reproduced: RR-IV with SUE +0.162, with ret0 -0.050, and SUE with ret0 +0.163. A rank regression for 2015-19, ret0 = rr_rank + sue_rank, gives a coefficient of -1.22% (t -2.4) on RR-IV with SUE held fixed and +2.82% (t 5.6) on SUE. A high RR-IV means a worse reaction for a given surprise, which fits the information being priced by the day -1 close. Leg means in 2015-19: longs -0.97% and shorts -0.31% on day 0. The average over all events is -0.505%.

## Verdict: sound with caveats
