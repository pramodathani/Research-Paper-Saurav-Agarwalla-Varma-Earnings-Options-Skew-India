"""Builds the one-row-per-event table used by equation 5."""

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    controls_builder,
    trading_calendar,
)


class RegressionDatasetBuilder:
    """Joins day -n option variables, controls and the surprise."""

    LAGS = (1, 2, 3)
    OPTION_COLUMNS = (
        'rr_iv',
        'atm_iv',
        'pc_contracts',
        'pc_value',
        'alt_rr_iv',
        'alt_atm_iv',
    )
    CONTROL_COLUMNS = ('beta', 'momentum', 'size', 'bhar')
    BHAR_FIRST = -10
    BHAR_LAST = -2

    def __init__(
        self,
        windows: pandas.DataFrame,
        controls: controls_builder.ControlsBuilder,
        calendar: trading_calendar.TradingCalendar,
        shares: pandas.DataFrame,
    ) -> None:
        """Stores the inputs.

        Args:
            windows: The event-day table with event_id.
            controls: The controls builder.
            calendar: The trading calendar.
            shares: Rows with symbol, broadcast and shares, one per results
                filing, used for market capitalisation.
        """
        self.windows = windows
        self.controls = controls
        self.calendar = calendar
        self.shares = shares.dropna(subset=['shares']).sort_values('broadcast')

    def lagged_variables(self) -> pandas.DataFrame:
        """Takes each option variable on days -1, -2 and -3.

        Returns:
            One row per event with columns such as rr_iv_1 and pc_contracts_3.
        """
        pieces = []
        for lag in self.LAGS:
            day = self.windows[self.windows['offset'] == -lag]
            day = day.set_index('event_id')[list(self.OPTION_COLUMNS)]
            day.columns = [f'{name}_{lag}' for name in day.columns]
            pieces.append(day)
        return pandas.concat(pieces, axis=1)

    def market_capitalisation(
        self,
        symbol: str,
        day_zero: pandas.Timestamp,
    ) -> float:
        """Computes the log market cap in the month before the EA month.

        The share count is from the last results filing announced before
        that month began, so no information from the event is used. The
        price is the month's average unadjusted close, and the value is in
        millions of rupees.

        Args:
            symbol: The share.
            day_zero: The announcement's day 0.

        Returns:
            The natural log of the market capitalisation, or NaN.
        """
        month = day_zero.to_period('M') - 1
        history = self.shares[self.shares['symbol'] == symbol]
        known = history[history['broadcast'] < month.start_time]
        if known.empty:
            return float('nan')
        price = self.controls.average_close(symbol, month)
        value = price * known['shares'].iloc[-1] / 1.0e6
        if not value > 0:
            return float('nan')
        return float(numpy.log(value))

    def buy_and_hold(self, symbol: str, day_zero: pandas.Timestamp) -> float:
        """Compounds the share's return from day -10 to day -2.

        Args:
            symbol: The share.
            day_zero: The announcement's day 0.

        Returns:
            The buy-and-hold return, or NaN.
        """
        dates = []
        for offset in range(self.BHAR_FIRST, self.BHAR_LAST + 1):
            date = self.calendar.shift(day_zero.date(), offset)
            if date is None:
                return float('nan')
            dates.append(pandas.Timestamp(date))
        return self.controls.buy_and_hold(symbol, dates)

    def build(self, events: pandas.DataFrame) -> pandas.DataFrame:
        """Builds the table.

        Args:
            events: Kept events in the same order as used to build the
                windows, with symbol, day0, sue and sue_alternative. The row
                position is the event_id.

        Returns:
            One row per event with the surprise, the lagged option
            variables, the controls and the year-quarter.
        """
        events = events.reset_index(drop=True)
        table = events[['symbol', 'day0', 'sue', 'sue_alternative']].copy()
        table = table.join(self.lagged_variables())
        month = table['day0'].dt.to_period('M')
        betas = []
        momenta = []
        sizes = []
        returns = []
        for symbol, day_zero, event_month in zip(
            table['symbol'],
            table['day0'],
            month,
            strict=True,
        ):
            betas.append(self.controls.beta(symbol, event_month))
            momenta.append(self.controls.momentum(symbol, event_month))
            sizes.append(self.market_capitalisation(symbol, day_zero))
            returns.append(self.buy_and_hold(symbol, day_zero))
        table['beta'] = betas
        table['momentum'] = momenta
        table['size'] = sizes
        table['bhar'] = returns
        table['year_quarter'] = table['day0'].dt.to_period('Q').astype(str)
        return table
