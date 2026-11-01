# Asymmetric Uncertainty Around Earnings Announcements, recreated for NSE stock options

This study recreates the reproducible part of Saurav, Agarwalla and Varma (2024), *Asymmetric Uncertainty Around Earnings Announcements: Evidence from Options Markets*, American Business Review 27(2), 459-487, [doi:10.37625/abr.27.2.459-487](https://doi.org/10.37625/abr.27.2.459-487). The paper looks at how implied volatility, the options skew (the risk reversal, RR-IV) and options volume ratios (options to stock, options to futures, puts to calls) move around the quarterly earnings announcements of NSE stocks with derivatives from January 2015 to December 2019. It also asks whether the skew and the put-call ratio predict the sign of the earnings surprise the day before the announcement.

**In one line:** work in progress; the study is at the Intake stage, and there are no results yet.

## Scope

- **Main sample:** January 2015 to December 2019, as in the paper. Later years may follow as an extension.
- **Surprise measure:** the standardised unexpected earnings (SUE) only. The paper's analyst-based surprise needs IBES, which is not available, so the analyst coverage and dispersion controls are dropped too.
- **To reproduce:** Table 1, Table 5, Figure 1, Figure 4, panel (b) of Figures 2, 3 and 5, and the SUE columns of Tables 6 to 9.
- **Volatility smile:** fitted to NSE's daily F&O bhavcopy rather than the paper's time-matched tick data, so the RR-IV here is an approximation of the paper's.

## Citation

See [CITATION.cff](CITATION.cff). Please cite the original paper as well.

## Licence

The code is under the MIT licence. The paper's PDF in `paper/` is (c) its authors and is published under CC BY-NC 4.0.
