# controls_builder.py

- Beta is a 60-month rolling market-model slope on the NIFTY 500 total-return index, at least 36 months, ending in the month before the EA month.
- Momentum compounds months t-12 to t-1 (Table 2). Page 467 calls it the last 11 months. The study uses the Table 2 definition, which skips no month.
- BHAR is the raw buy-and-hold return from day -10 to day -2; a market-adjusted version is a possible sensitivity.
