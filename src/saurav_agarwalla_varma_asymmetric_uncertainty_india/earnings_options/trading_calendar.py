"""Maps announcement times to the paper's day 0 and counts trading days."""

import bisect
import datetime


class TradingCalendar:
    """A sorted list of trading dates with event-day helpers."""

    MARKET_CLOSE = datetime.time(15, 30)

    def __init__(self, trading_dates: list[datetime.date]) -> None:
        """Stores the sorted trading dates.

        Args:
            trading_dates: Every trading date, in any order.
        """
        self.dates = sorted(set(trading_dates))

    def day_zero(self, broadcast: datetime.datetime) -> datetime.date | None:
        """Finds day 0 for an announcement, as in the paper's page 468.

        An announcement at or after 15:30, or on a day the market is closed,
        belongs to the next trading day. One before the open or during the
        session belongs to its own day.

        Args:
            broadcast: The announcement's broadcast time in India.

        Returns:
            The trading date that is day 0, or None after the last date.
        """
        date = broadcast.date()
        position = bisect.bisect_left(self.dates, date)
        if position == len(self.dates):
            return None
        is_trading_day = self.dates[position] == date
        if is_trading_day and broadcast.time() >= self.MARKET_CLOSE:
            position += 1
        if position >= len(self.dates):
            return None
        return self.dates[position]

    def shift(self, date: datetime.date, offset: int) -> datetime.date | None:
        """Moves a trading date by a number of trading days.

        Args:
            date: A trading date.
            offset: How many trading days to move, negative for earlier.

        Returns:
            The trading date, or None when it falls outside the calendar or
            the date is not a trading date.
        """
        position = bisect.bisect_left(self.dates, date)
        if position == len(self.dates) or self.dates[position] != date:
            return None
        target = position + offset
        if target < 0 or target >= len(self.dates):
            return None
        return self.dates[target]

    def days_between(self, start: datetime.date, end: datetime.date) -> int:
        """Counts trading days after start up to and including end.

        Args:
            start: The earlier date.
            end: The later date.

        Returns:
            The number of trading dates in (start, end].
        """
        low = bisect.bisect_right(self.dates, start)
        high = bisect.bisect_right(self.dates, end)
        return high - low
