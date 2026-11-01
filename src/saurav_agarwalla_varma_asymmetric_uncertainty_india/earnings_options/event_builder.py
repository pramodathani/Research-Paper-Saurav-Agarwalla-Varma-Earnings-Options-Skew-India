"""Turns first earnings broadcasts into events with day 0 and an expiry."""

import bisect

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    trading_calendar,
)


class EventBuilder:
    """Applies the paper's event rules to the EPS panel."""

    MIN_TRADING_DAYS_TO_EXPIRY = 3

    def __init__(
        self,
        calendar: trading_calendar.TradingCalendar,
        expiries: pandas.DataFrame,
        active_days: pandas.DataFrame,
    ) -> None:
        """Stores the calendar and the derivatives information.

        Args:
            calendar: The trading calendar.
            expiries: Rows with symbol and expiry, one per stock future
                expiry that ever traded.
            active_days: Rows with date and symbol, one per share-day on
                which the share's options traded.
        """
        self.calendar = calendar
        self.expiry_lists = {
            symbol: sorted(group['expiry'].dt.date.unique())
            for symbol, group in expiries.groupby('symbol')
        }
        self.active = set(
            zip(
                active_days['date'].dt.date,
                active_days['symbol'],
                strict=True,
            ),
        )

    def near_expiry(self, symbol: str, date) -> object | None:
        """Finds the nearest futures expiry strictly after a date.

        Args:
            symbol: The share.
            date: The trading date.

        Returns:
            The expiry date, or None if the share has no later expiry.
        """
        expiries = self.expiry_lists.get(symbol, [])
        position = bisect.bisect_right(expiries, date)
        if position == len(expiries):
            return None
        return expiries[position]

    def build(self, panel: pandas.DataFrame) -> pandas.DataFrame:
        """Builds the events and says why each dropped announcement dropped.

        An announcement becomes an event when it has a day 0, the share's
        options traded that day, a near-month series expires after day 0,
        and at least three trading days separate day 0 from that expiry.

        Args:
            panel: The EPS panel with symbol, period_end, broadcast, sue,
                sue_alternative, shares and eps.

        Returns:
            One row per announcement with day0, expiry, trading days to
            expiry, a keep flag and the reason it was dropped, if any.
        """
        rows = []
        for item in panel.itertuples():
            day_zero = self.calendar.day_zero(item.broadcast.to_pydatetime())
            reason = ''
            expiry = None
            days = None
            if day_zero is None:
                reason = 'no day 0'
            elif (day_zero, item.symbol) not in self.active:
                reason = 'no options traded on day 0'
            else:
                expiry = self.near_expiry(item.symbol, day_zero)
                if expiry is None:
                    reason = 'no later expiry'
                else:
                    days = self.calendar.days_between(day_zero, expiry)
                    if days < self.MIN_TRADING_DAYS_TO_EXPIRY:
                        reason = 'within three trading days of expiry'
            rows.append(
                {
                    'symbol': item.symbol,
                    'period_end': item.period_end,
                    'broadcast': item.broadcast,
                    'day0': None
                    if day_zero is None
                    else pandas.Timestamp(day_zero),
                    'expiry': None
                    if expiry is None
                    else pandas.Timestamp(expiry),
                    'trading_days_to_expiry': days,
                    'keep': reason == '',
                    'reason': reason,
                    'eps': item.eps,
                    'shares': item.shares,
                    'sue': item.sue,
                    'sue_alternative': item.sue_alternative,
                },
            )
        return pandas.DataFrame(rows)
