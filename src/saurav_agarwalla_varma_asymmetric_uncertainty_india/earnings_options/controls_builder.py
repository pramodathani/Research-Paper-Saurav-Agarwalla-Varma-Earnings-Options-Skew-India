"""Builds the regression controls: beta, momentum, size and BHAR."""

import numpy
import pandas


class ControlsBuilder:
    """Computes the paper's controls for each earnings event."""

    BETA_MONTHS = 60
    BETA_MINIMUM_MONTHS = 36
    MOMENTUM_FIRST_LAG = 12
    MOMENTUM_LAST_LAG = 1

    def __init__(
        self,
        daily_returns: pandas.DataFrame,
        market_levels: pandas.Series,
    ) -> None:
        """Stores the stock and market series.

        Args:
            daily_returns: Rows with date, symbol, close and ret.
            market_levels: Daily total-return index levels by date.
        """
        self.daily_returns = daily_returns
        self.market_levels = market_levels
        self.stock_returns = {
            name: group.set_index('date')['ret']
            for name, group in daily_returns.groupby('symbol')
        }
        self.stock_closes = {
            name: group.set_index('date')['close']
            for name, group in daily_returns.groupby('symbol')
        }
        self.monthly = self.build_monthly_returns()
        self.market_monthly = self.build_market_monthly()
        self.beta_table = self.build_beta_table()

    def build_monthly_returns(self) -> pandas.DataFrame:
        """Compounds daily returns into monthly returns.

        Returns:
            A table of months by symbols, NaN where a share did not trade.
        """
        frame = self.daily_returns.dropna(subset=['ret']).copy()
        frame['month'] = frame['date'].dt.to_period('M')
        frame['log'] = numpy.log1p(frame['ret'])
        grouped = frame.groupby(['month', 'symbol'])['log'].sum()
        return numpy.expm1(grouped).unstack('symbol')

    def build_market_monthly(self) -> pandas.Series:
        """Turns daily index levels into monthly returns.

        Returns:
            Monthly returns indexed by month, from month-end levels.
        """
        levels = self.market_levels.sort_index()
        month_end = levels.groupby(levels.index.to_period('M')).last()
        return month_end.pct_change()

    def build_beta_table(self) -> pandas.DataFrame:
        """Estimates a rolling market-model beta for every share.

        Each beta uses the stock's last 60 monthly returns, at least 36 of
        them, ending in the month shown.

        Returns:
            A table of months by symbols holding the beta.
        """
        betas = {}
        for symbol in self.monthly.columns:
            pair = pandas.DataFrame(
                {
                    'stock': self.monthly[symbol],
                    'market': self.market_monthly,
                },
            ).dropna()
            if len(pair) < self.BETA_MINIMUM_MONTHS:
                continue
            window = pair.rolling(
                self.BETA_MONTHS,
                min_periods=self.BETA_MINIMUM_MONTHS,
            )
            covariance = window['stock'].cov(pair['market'])
            variance = window['market'].var()
            betas[symbol] = covariance / variance
        return pandas.DataFrame(betas)

    def beta(self, symbol: str, event_month: pandas.Period) -> float:
        """Returns the beta known at the end of the month before the event.

        Args:
            symbol: The share.
            event_month: The month of the announcement.

        Returns:
            The beta, or NaN if it cannot be estimated.
        """
        previous = event_month - 1
        if symbol not in self.beta_table.columns:
            return float('nan')
        if previous not in self.beta_table.index:
            return float('nan')
        return float(self.beta_table.loc[previous, symbol])

    def momentum(self, symbol: str, event_month: pandas.Period) -> float:
        """Compounds the monthly returns from t-12 to t-1.

        Args:
            symbol: The share.
            event_month: The month t of the announcement.

        Returns:
            The compounded return, or NaN if any of the months is missing.
        """
        if symbol not in self.monthly.columns:
            return float('nan')
        first = event_month - self.MOMENTUM_FIRST_LAG
        last = event_month - self.MOMENTUM_LAST_LAG
        months = pandas.period_range(first, last, freq='M')
        values = self.monthly[symbol].reindex(months)
        if values.isna().any():
            return float('nan')
        return float((1.0 + values).prod() - 1.0)

    def buy_and_hold(
        self,
        symbol: str,
        dates: list[pandas.Timestamp],
    ) -> float:
        """Compounds a share's daily returns over given trading dates.

        Args:
            symbol: The share.
            dates: The trading dates to compound over.

        Returns:
            The buy-and-hold return, or NaN if any day has no return.
        """
        series = self.stock_returns.get(symbol, pandas.Series(dtype=float))
        values = series.reindex(dates)
        if len(values) == 0 or values.isna().any():
            return float('nan')
        return float((1.0 + values).prod() - 1.0)

    def average_close(
        self,
        symbol: str,
        month: pandas.Period,
    ) -> float:
        """Averages a share's unadjusted daily close over a month.

        Args:
            symbol: The share.
            month: The calendar month.

        Returns:
            The mean close, or NaN if the share did not trade.
        """
        closes = self.stock_closes.get(symbol)
        if closes is None:
            return float('nan')
        in_month = closes[closes.index.to_period('M') == month]
        return float(in_month.mean()) if len(in_month) else float('nan')
