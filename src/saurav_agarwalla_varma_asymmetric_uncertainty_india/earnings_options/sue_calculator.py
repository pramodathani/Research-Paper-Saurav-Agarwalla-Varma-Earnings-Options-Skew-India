"""Standardised unexpected earnings, equations 2 to 4 of the paper."""

import pandas


class SueCalculator:
    """Computes SUE from a firm's consecutive quarterly EPS."""

    WINDOW = 8
    SEASONAL_LAG = 4

    def quarter_index(self, period_end: pandas.Series) -> pandas.Series:
        """Turns period-end dates into consecutive quarter numbers.

        Args:
            period_end: Quarter-end dates.

        Returns:
            year * 4 + quarter number minus one, so adjacent quarters differ
            by one.
        """
        dates = pandas.to_datetime(period_end)
        return dates.dt.year * 4 + (dates.dt.month - 1) // 3

    def compute(self, eps: pandas.Series) -> pandas.DataFrame:
        """Computes the expected EPS, the surprise and SUE for every quarter.

        The expected EPS is the EPS four quarters earlier plus the mean of
        the last eight year-on-year changes. SUE divides the surprise by the
        sample standard deviation of the previous eight quarters' surprises.
        A quarter gets a value only if every quarter it needs is present, so
        a gap in the history gives NaN, never a guess.

        Args:
            eps: EPS per share on one common share basis, indexed by the
                integer quarter number from quarter_index. Missing quarters
                may be absent.

        Returns:
            A table indexed by quarter number with the columns eps,
            expected, surprise, sigma, sue and sue_alternative. The
            alternative divides by the standard deviation of the previous
            eight year-on-year changes instead.
        """
        full = pandas.RangeIndex(int(eps.index.min()), int(eps.index.max()) + 1)
        series = eps.astype(float).reindex(full)
        change = series - series.shift(self.SEASONAL_LAG)
        drift = (
            change.shift(1).rolling(self.WINDOW, min_periods=self.WINDOW).mean()
        )
        expected = series.shift(self.SEASONAL_LAG) + drift
        surprise = series - expected
        sigma = (
            surprise.shift(1)
            .rolling(self.WINDOW, min_periods=self.WINDOW)
            .std()
        )
        alternative_sigma = (
            change.shift(1).rolling(self.WINDOW, min_periods=self.WINDOW).std()
        )
        return pandas.DataFrame(
            {
                'eps': series,
                'expected': expected,
                'surprise': surprise,
                'sigma': sigma,
                'sue': surprise / sigma.where(sigma > 0),
                'sue_alternative': surprise
                / alternative_sigma.where(alternative_sigma > 0),
            },
        )
