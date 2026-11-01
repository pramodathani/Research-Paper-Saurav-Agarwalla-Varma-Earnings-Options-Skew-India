# Summary: Saurav, Agarwalla and Varma (2024)

Sumit Saurav, Sobhesh Kumar Agarwalla and Jayanth R. Varma, "Asymmetric Uncertainty Around Earnings Announcements: Evidence from Options Markets", *American Business Review* 27(2), November 2024, pages 459-487, doi:10.37625/abr.27.2.459-487. Open access under CC BY-NC (page 459). Page numbers below are the journal's (459-487); the PDF page is the journal page minus 458.

## The question in plain words

Before a company announces quarterly results, nobody knows the number. Option prices carry two kinds of information about that unknown:

- **How much the price may move:** at-the-money implied volatility (ATM-IV).
- **Which way it is more likely to move:** the slope of the smile, measured as a risk reversal (RR-IV).

The paper asks four questions about Indian single-stock options:

1. Do both measures rise into the announcement and fall after it?
2. Does option trading pick up relative to the stock and to stock futures?
3. Does the put-to-call volume ratio (P/C) rise?
4. One to three days before the announcement, do RR-IV and P/C predict whether the surprise will be good or bad?

## Hypotheses (pages 460-462, 466)

1. Uncertainty, measured by IV at Δ = 0.25, 0.5 and 0.75, builds up before the announcement (EA) and is resolved after it.
2. Asymmetric uncertainty shows up in the slope of the smile. RR-IV is more negative before bad surprises.
3. If informed traders prefer options, three volume ratios rise into the EA:
   - O/S: options volume to stock volume.
   - O/F: options volume to futures volume.
   - P/C: put volume to call volume. P/C should rise most before bad surprises.
4. In a regression with controls, RR-IV and P/C at day -n predict the sign of the surprise, and ATM-IV does not.

## Data (pages 467-469)

- **Sample:** every quarterly EA from January 2015 to December 2019 by NSE firms with stock derivatives. The sample ends in 2019 to keep COVID out (page 467). After filters it holds 2,081 firm-quarters from 191 firms (page 468).
- **Event time:**
  - The broadcast time comes from the NSE corporate-announcement pages and is cross-checked with IBES dates.
  - An announcement after market hours moves to the next trading day, which becomes day 0 (Berkman and Truong 2009; page 468).
- **Options and futures:** NSE trade books (tick data) for the smile, and the NSE bhavcopy for the volume ratios (Table 2, pages 468-469).
- **Contracts and dates used:**
  - Only the near-month series that expires after the EA.
  - EAs made less than three days before near-month expiry are dropped, because of expiry-day effects (page 468).
- **Spot returns and volume, institutional holding, market capitalisation:** CMIE Prowess.
- **Analyst data:** IBES.
- **Risk-free rate:** RBI 91-day T-bill (page 463).
- **Winsorising:** all variables at the 5th and 95th percentiles (page 468).

## Method

### Volatility smile per stock-day (page 463)

1. Implied volatility (IV) comes from Black (1976) on time-matched option and futures trades. This avoids estimating dividends and cost of carry.
2. Filters:
   - Drop option contracts traded for less than five minutes in the day.
   - Drop prices outside Black's arbitrage bounds.
   - Keep stock-days with at least seven contracts, including at least one call and one put.
3. Fit IV = aΔ² + bΔ + c on call delta Δ ∈ [0, 1], with put deltas converted to call deltas.
   - a and c must be non-negative. c is shifted by b²/4a when -b/2a ∈ [0, 1], otherwise by min(0, a + b).
   - The fit minimises squared pricing errors weighted by log traded value, solved "recursively" with Nelder-Mead. The text says errors between "the options market price and the estimated prices". Whether the errors are in price or in IV is ambiguous.
4. Smile parameters:
   - ATM-IV = IV(Δ = 0.5).
   - IV(Δ = 0.75) and IV(Δ = 0.25).
   - RR-IV = IV(0.25) - IV(0.75). RR-IV is negative when OTM puts are dearer than OTM calls.

### Surprise (pages 463-464)

- **IBES surprise** = (actual EPS - mean estimate) / mean estimate (eq. 1).
- **SUE** = (X_q - E[X_q]) / σ (eq. 2).
  - X is EPS before extraordinary items.
  - E[X_q] = X_{q-4} + μ, where μ is the mean of the last eight year-on-year changes, X_{q-n} - X_{q-n-4} for n = 1 to 8 (eqs. 3-4).
  - σ is the standard deviation of the surprises over the previous eight quarters.
  - So each SUE needs about 16 to 20 quarters of EPS history before it.

### Event-window analyses (page 466)

- **Table 5:** mean smile levels in the pre-EA, EA and post-EA months, with difference-in-means t-tests.
- **Figure 1:** daily means over days -10 to +10, each parameter divided by its average over the previous trading month.
- **Figures 2, 3 and 5:**
  - Same window, split into three quantiles of the surprise: large negative, small, and large positive.
  - Figure 2 plots ATM-IV, Figure 3 RR-IV and Figure 5 P/C.
- **Figure 4:** O/S and O/F over days -10 to +10.

### Regression, equation 5 (pages 466-467)

Surprise_{i,q} = β1·RR-IV_{t-n} + β2·P/C_{t-n} + β3·ATM-IV_{t-n} + λ·X_{i,q} + firm FE (+ year-quarter FE) + ε, for n = 1, 2 and 3.

The controls X are:
- Analyst coverage, log(1 + number of analysts).
- Analyst dispersion, the standard deviation of forecasts over their mean.
- Beta, from a 60-month rolling market model, lagged one month.
- Institutional holding %, lagged one quarter.
- Momentum, the return over months t-12 to t-1. The text on page 467 calls it "the last 11 months".
- Size, the log of average market capitalisation in the month before the EA month.
- BHAR from day -10 to -2.

### Robustness, Tables 8 and 9 (pages 476-480)

Moneyness buckets after Xing, Zhang and Zhao (2010):
- **OTM:** K/F between 1.05 and 1.20 for calls, F/K between 1.05 and 1.20 for puts.
- **ATM:** the ratio between 0.95 and 1.05.
- IV is volume-weighted within each bucket.
- Alt RR-IV = IV(OTM call) - IV(OTM put). Alt ATM-IV is the ATM bucket's IV.

## Results we will reproduce

### Table 1: worked example (page 465)

The forward is a mixture of three lognormals with forwards 100, 110 and 90, each with 25% annual volatility. Options have one week to expiry, and the rates and dividend yield are zero. ITM and OTM strikes are S/(1 + ATM-IV/52) and S × (1 + ATM-IV/52).

| | No surprise | 10% chance of +10% | 10% chance of -10% |
|---|---|---|---|
| Spot | 100.00 | 101.00 | 99.00 |
| ITM strike / premium / IV | 99.52 / 1.63 / 25.00% | 100.39 / 2.04 / 30.86% | 98.40 / 2.09 / 32.43% |
| ATM strike / premium / IV | 100.00 / 1.38 / 25.00% | 101.00 / 1.75 / 31.37% | 99.00 / 1.74 / 31.78% |
| OTM strike / premium / IV | 100.48 / 1.16 / 25.00% | 101.61 / 1.50 / 31.94% | 99.61 / 1.43 / 31.20% |
| RR-IV (OTM - ITM), percentage points | 0.00 | 1.08 | -1.23 |

On 2026-11-01 a 30-line check that prices calls on this mixture reproduced every IV, strike and RR-IV in the table exactly. Page 465's text writes column 3's OTM strike as 99 × (1 + 0.3137/52), but the table's 99.61 needs 0.3178. The text has a typo and the table is right.

### Table 5: smile levels by month (page 471)

| | Pre-EA month | EA month | Post-EA month | EA - pre (t) | EA - post (t) |
|---|---|---|---|---|---|
| ATM-IV | 0.383 | 0.411 | 0.372 | 0.028 (6.70) | 0.038 (10.84) |
| IV(Δ=0.75) | 0.397 | 0.427 | 0.391 | 0.030 (6.42) | 0.036 (9.13) |
| IV(Δ=0.25) | 0.397 | 0.422 | 0.388 | 0.024 (5.59) | 0.034 (9.21) |

These are raw IV levels, not the normalised ones that Table 2 defines.

### Figure 1: normalised smile levels, days -10 to +10 (page 472)

- All three levels rise steadily from day -10 to a peak at day -1. They drop sharply on day 0 and drift lower to day +10, ending below their day -10 level.
- The axis labels in the PDF are too blurred to read even at 260 dpi.
- Figure 2's comparable scale runs from about 1.10 at day -10 to about 1.24 at day -1, and about 1.12 at day 0.

### Figure 2(b): ATM-IV by SUE tercile (page 473)

- The three terciles move together, from about 1.09-1.10 at day -10 to about 1.23-1.25 at day -1. They fall to about 1.12-1.13 at day 0 and to about 1.02-1.05 by day +10.
- The rise does not depend on the surprise (page 472).

### Figure 3(b): RR-IV by SUE tercile (page 474)

- **Small and large-positive terciles:** hover between about -0.002 and -0.005.
- **Large-negative tercile:**
  - Drops from about -0.005 at day -2 to about -0.013 at day -1 and -0.0125 at day 0.
  - Recovers to about -0.01 by days +1 and +2.
  - Rises to about +0.006 at day +8.
- **Panel (a), with IBES (not reproduced):** the large-negative dip is deeper, about -0.018 at day 0.

### Figure 4: O/S and O/F (page 477)

- **O/S:** about 1.05 at day -10, 1.22 at day -2, 1.52 at day -1 and a peak of about 1.63 at day 0. Then 1.46 at day +1, and it settles near 1.30 by day +4.
- **O/F:** about 0.46 at day -10, 0.51 at day -2, 0.64 at day -1 and a peak of about 0.71 at day 0. Then 0.68 at day +1, and it drifts to about 0.58 by day +10.

### Figure 5(b): P/C by SUE tercile (page 478)

- All three terciles sit near 0.43-0.45 from day -10 to day -2, then rise to a peak on day 0:
  - Large negative: about 0.52 at day -1 and 0.56 at day 0.
  - Small: about 0.49 at day -1 and 0.50 at day 0.
  - Large positive: about 0.47 at day -1 and 0.475 at day 0.
- All three fall back to about 0.43-0.44 by day +10.

### Table 6: regression at n = 1 (page 479). SUE columns; standard errors in brackets

| | (1) firm FE | (2) firm + year-quarter FE |
|---|---|---|
| RR-IV(t-1) | 2.168*** (0.594) | 2.514*** (0.634) |
| P/C(t-1) | -1.078*** (0.388) | -1.149*** (0.397) |
| ATM-IV(t-1) | 0.649* (0.336) | 0.416 (0.362) |
| Analyst coverage | -0.272** (0.107) | -0.204* (0.113) |
| Beta | 0.144 (0.142) | 0.185 (0.148) |
| Institutional % | 0.016* (0.009) | 0.011 (0.009) |
| Analyst dispersion | -0.396 (0.398) | -0.361 (0.402) |
| Momentum | -0.140* (0.085) | -0.039 (0.094) |
| Size | 0.305*** (0.110) | 0.190 (0.121) |
| BHAR(-10,-2) | 1.074* (0.547) | 0.760 (0.552) |
| Observations | 1,729 | 1,729 |
| Adjusted R² | 0.028 | 0.038 |

IBES columns (3) and (4), which are not reproduced:
- RR-IV: 0.750*** and 0.824***.
- P/C: -0.575*** and -0.570***.
- ATM-IV: -0.069 and -0.135.

On page 479 the n = 1 P/C row places -0.575 in column 3 and -0.570 in column 4.

### Table 7: n = 2 and 3, both with firm and year-quarter FE (page 480). SUE columns

| | (1) n = 2 | (2) n = 3 |
|---|---|---|
| RR-IV | 0.673 (1.026) | 1.809 (1.240) |
| P/C | -0.700 (0.590) | -0.274 (0.669) |
| ATM-IV | 0.107 (0.464) | 0.575 (0.532) |
| BHAR(-10,-2) | 1.257** (0.612) | 1.337** (0.666) |
| Observations | 1,474 | 1,320 |
| Adjusted R² | 0.014 | 0.014 |

None of the option variables is significant at n = 2 or 3.

### Table 8: moneyness-bucket smile, n = 1 (page 481). SUE columns

| | (1) firm FE | (2) firm + year-quarter FE |
|---|---|---|
| Alt RR-IV(t-1) | 1.844*** (0.656) | 2.386*** (0.699) |
| P/C(t-1) | -0.635*** (0.142) | -0.620*** (0.145) |
| Alt ATM-IV(t-1) | 0.718** (0.337) | 0.432 (0.362) |
| Size | 0.343*** (0.110) | 0.229* (0.122) |
| BHAR(-10,-2) | 1.107** (0.548) | 0.863 (0.553) |
| Observations | 1,672 | 1,672 |
| Adjusted R² | 0.034 | 0.043 |

P/C is the same variable as in Table 6, but its coefficient and standard error differ a lot: -0.635 (0.142) here against -1.078 (0.388). The paper does not explain why.

### Table 9: moneyness-bucket smile, n = 2 and 3 (page 482). SUE columns

| | (1) n = 2 | (2) n = 3 |
|---|---|---|
| Alt RR-IV | 3.010*** (1.037) | 2.314* (1.213) |
| P/C | -0.204 (0.190) | -0.302 (0.191) |
| Alt ATM-IV | 0.102 (0.471) | 0.416 (0.531) |
| Observations | 1,429 | 1,273 |
| Adjusted R² | 0.031 | 0.027 |

Unlike Table 7, Alt RR-IV stays significant at n = 2 and 3 with SUE. With IBES it does not.

### Tables 3 and 4: descriptive statistics and correlations (pages 469-470), for the non-IBES rows

- **SUE:** N 1,831, mean 0.052, standard deviation 1.089.
- **RR-IV(t-1):** N 2,081, mean -0.011, standard deviation 0.060.
- **ATM-IV(t-1):** mean 0.455.
- **P/C(t-1):** mean 0.124, median 0.060.
- **Correlations with SUE:**
  - RR-IV: 0.162 at t-1, 0.091 at t-2 and 0.078 at t-3.
  - P/C: -0.11 at t-1, -0.082 at t-2 and -0.056 at t-3.

## Conclusions (pages 481-483)

- The smile rises and steepens into the EA and falls after it. Option volume rises relative to stock and futures volume, with a peak on day 0.
- The options market can tell good surprises from bad ones only on the day before the announcement. The authors read this as informed trading, possibly by insiders, close to the event.
- They propose that exchanges and SEBI watch unusual moves in RR-IV as a surveillance metric.

## Inconsistencies and open questions to settle in the plan

1. **Normalisation.** Table 2 (page 468) defines the IV levels as divided by the previous month's mean. Table 5 and Table 3, however, show raw levels (0.38-0.46), while Figures 1 and 2 show normalised ones (1.0-1.25). Figure 1's base is "the previous trading month" (page 466) and Table 2's is "the month preceding the EA month". We take Table 5 as raw and Figures 1 and 2 as normalised by the mean over the calendar month before the EA month.
2. **P/C scale.** Table 3's P/C(t-1) has mean 0.124 and median 0.060 (page 469), but Figure 5 shows means of 0.43-0.56 (page 478). P/C may be measured in contracts in one place and in value in the other, or the figure may average a differently winsorised series. We will compute both and report which one matches.
3. **Winsorising.** Table 3's ranges (RR-IV(t-1) from -1.44 to 0.324; P/C(t-2) up to 7.38) do not look 5/95-winsorised, although page 468 says all variables are.
4. **Volume units.** O/S above 1 suggests notional value, or underlying shares for options, rather than contracts. Table 2 does not say which. We will test which definition gives O/S near 1.05-1.6 and O/F near 0.46-0.71.
5. **Post-EA days.** Only near-month series expiring after the EA are used, and EAs within three days of expiry are dropped. Days +1 to +10 can fall after that expiry. Whether the smile then rolls to the next month is not stated.
6. **Standard errors.** Tables 6-9 report "standard errors" with no clustering stated.
7. **Smile fit objective.** It is ambiguous whether the weighted errors are in option price or in IV, and "recursively" is not explained.
8. **Momentum window.** Table 2 says t-12 to t-1 and page 467 says the last 11 months. These are the same window if the most recent month is skipped.
9. **Typos.** Page 465's OTM strike for column 3 is noted above under Table 1. Table 9's BHAR in column 2, 1.565 (0.653), has no star although t ≈ 2.4.
10. **Tercile split.** Whether the terciles are pooled over the whole sample or formed per quarter is not stated. Pooled is the natural reading.

## What the Indian recreation cannot match

| Paper | Here | Effect |
|---|---|---|
| Time-matched tick trades and a five-minute filter | Daily F&O bhavcopy settle or close prices; option and futures prices are not synchronous | Noisier smile; RR-IV is an approximation and the effect may weaken |
| IBES surprise, coverage, dispersion | Not available | Panel (a) of Figures 2, 3 and 5 and columns (3)-(4) of Tables 6-9 are dropped; the SUE regressions lose two controls |
| CMIE Prowess (spot, institutional holding, size) | NSE equity bhavcopy, NSE shareholding-pattern filings | To be tested in the Data stage |
| RBI 91-day T-bill | IIMA's risk-free series, or RBI auction results | Little effect on short-dated IVs |
