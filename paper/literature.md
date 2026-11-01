# The work around the paper

Gathered on 2026-11-01 by the literature_scout subagent and checked against the paper's own reference list (pages 484-486).

**How complete this is:** coverage is partial. Several search sources blocked downloads, and no citations of the paper were found. Entries marked "not verified" come only from the paper's references.

## 1. Versions and citations of the paper

- **Saurav, Agarwalla and Varma (2024)**: the paper itself, [doi:10.37625/abr.27.2.459-487](https://doi.org/10.37625/abr.27.2.459-487).
- **SSRN version**: listed with the authors as Agarwalla, Saurav and Varma, SSRN 4277255, [doi:10.2139/ssrn.4277255](https://doi.org/10.2139/ssrn.4277255), apparently from late 2022. It could not be opened.
- **Doctoral work**: Sumit Saurav's IIMA (2022) and IIMB (2023) CVs list it as a working paper and appear to place it in his doctoral work.
- **Citations**: none found.

## 2. The US work it builds on

- **Patell and Wolfson (1979, 1981)**: implied volatility rises before earnings and falls after (not verified).
- **Donders and Vorst (1996)**: the same rise and fall around firm-specific news (not verified).
- **Pan and Poteshman (2006, RFS)**: put-call volume predicts stock returns (not verified).
- **Roll, Schwartz and Subrahmanyam (2010, JFE)**: the O/S ratio rises around earnings. Their US O/S is below 1, against above 1 in India (page 460).
- **Xing, Zhang and Zhao (2010, JFQA)**, [doi:10.1017/S0022109010000220](https://doi.org/10.1017/S0022109010000220): stocks with the steepest smirks underperform by 10.9% a year after risk adjustment, and the effect lasts at least six months. Its moneyness buckets are used in Tables 8 and 9.
- **Jin, Livnat and Zhang (2012, JAR)**, [doi:10.1111/J.1475-679X.2012.00439.X](https://doi.org/10.1111/J.1475-679X.2012.00439.X): skew and call-put volatility spreads lead returns around earnings and other events. Option traders appear to have an information advantage.
- **Johnson and So (2012, JFE)**, [doi:10.1016/J.JFINECO.2012.05.008](https://doi.org/10.1016/J.JFINECO.2012.05.008): a low O/S beats a high O/S by 0.34% a week, which they attribute to short-sale costs.
- **Diavatopoulos, Doran, Fodor and Peterson (2012, JBF)**: changes in implied skewness and kurtosis before earnings relate to the stock's reaction.
- **Truong, Corrado and Chen (2012)**: the options market's response to earnings, with the IV build-up depending on good or bad news.
- **Ge, Lin and Pearson (2016, JFE)**: on why O/S predicts returns. Seen only in reference lists.
- **Blau, Nguyen and Whitby (2014, JBF)**: compares the information in P/C and O/S.
- **Leung and Santoli (2014)**, [arXiv:1412.8414](http://arxiv.org/abs/1412.8414): a theory model of the earnings jump and the pre-announcement IV surface.

## 3. Replications, critiques and decay

- **No direct replication** of "skew predicts the earnings surprise" was found, and no study showing the effect weakened after publication.
- **de Silva, Smith and So (2022)**, *Losing is Optional*: retail investors crowd into options before earnings and overpay for volatility. Pre-earnings put and call flow may therefore be partly noise, which is a caveat for P/C in India's retail-heavy options market after 2020.

## 4. Indian studies

- **Jain, Agarwalla, Varma and Pandey (2019a, JFM 39(5))**: from 2008 to 2015, futures, not options, dominate informed trading before Indian earnings. This sits in tension with this paper's claim that options are preferred. Report O/F beside O/S.
- **Jain, Varma and Agarwalla (2019b, JFM 39(2))**: the smile method this paper follows, with liquidity filters, the Black model on futures, and quadratic smiles. Indian single-stock options are micro-efficient.
- **Agarwalla, Saurav and Varma (2021a, JFM)**: Indian option skew mostly reflects risk premia and buying pressure tied to lottery-like and bubble stocks. Skew is therefore not purely information. Control for its usual drivers, or at least note this.
- **Saurav, Agarwalla and Varma (2023, JFM 43)**: the skew and OTM volume shift near the 52-week high and low, consistent with anchoring.
- **Kumar, Agarwalla, Varma and Virmani (2023, JFM 43)**: dynamic Nelson-Siegel fitting of the NSE smile beats static fits.
- **Shukla et al. (2026, IMFI)**, [doi:10.21511/imfi.23(2).2026.28](https://doi.org/10.21511/imfi.23(2).2026.28): the 25-delta skew widens three to five days before rating downgrades of Nifty 500 F&O stocks in 2024-25. The sample has only 42 events.
- **Banerjee and Banerjee (2019)**, NSE-NYU WP 217: algorithmic traders and volatility information in Indian stock options ([PDF](https://nsearchives.nseindia.com/s3fs-public/inline-files/Algorithmic_Traders_and_Volatility_Information_Banerjee_Banerjee.pdf)). Not read.
- **Data:** no study was found on bhavcopy settle versus close prices for options, or on a free source of Indian earnings dates and EPS. The study must settle these itself.

## What this means for the recreation

1. Show O/F beside O/S, because the authors' own 2019 paper found futures preferred.
2. Treat RR-IV as partly a pressure measure, not only an information measure. The extension past 2019 is worth doing, because retail option volume has grown sharply.
3. The price-source and strike-filter choices for a bhavcopy smile have no published precedent. Report how sensitive the results are to them.
