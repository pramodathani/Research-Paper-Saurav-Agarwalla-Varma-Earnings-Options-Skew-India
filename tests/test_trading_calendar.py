"""Tests for the day-0 mapping and trading-day arithmetic."""

import datetime
import unittest

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    trading_calendar,
)


class TradingCalendarTest(unittest.TestCase):
    """Uses a week with a weekend and a holiday on Monday 2017-07-17."""

    def setUp(self) -> None:
        """Builds a calendar of Wed 12 to Fri 14, Tue 18 and Wed 19 July.

        Raises:
            AssertionError: Never.
        """
        days = [12, 13, 14, 18, 19]
        dates = [datetime.date(2017, 7, day) for day in days]
        self.calendar = trading_calendar.TradingCalendar(dates)

    def day_zero(self, day: int, hour: int, minute: int) -> str:
        """Returns day 0 as text for a broadcast on a July 2017 day.

        Args:
            day: Day of July 2017.
            hour: Hour of the broadcast.
            minute: Minute of the broadcast.

        Returns:
            The ISO date of day 0, or 'none'.
        """
        stamp = datetime.datetime(2017, 7, day, hour, minute)
        result = self.calendar.day_zero(stamp)
        return 'none' if result is None else result.isoformat()

    def test_during_market_is_same_day(self) -> None:
        """Checks 10:51 on Thursday is Thursday.

        Raises:
            AssertionError: If day 0 is wrong.
        """
        self.assertEqual(self.day_zero(13, 10, 51), '2017-07-13')

    def test_after_close_is_next_trading_day(self) -> None:
        """Checks 18:34 on Thursday is Friday.

        Raises:
            AssertionError: If day 0 is wrong.
        """
        self.assertEqual(self.day_zero(13, 18, 34), '2017-07-14')

    def test_exactly_at_close_is_next_day(self) -> None:
        """Checks 15:30 is already after the market.

        Raises:
            AssertionError: If day 0 is wrong.
        """
        self.assertEqual(self.day_zero(13, 15, 30), '2017-07-14')
        self.assertEqual(self.day_zero(13, 15, 29), '2017-07-13')

    def test_before_open_is_same_day(self) -> None:
        """Checks 08:00 on Thursday is Thursday.

        Raises:
            AssertionError: If day 0 is wrong.
        """
        self.assertEqual(self.day_zero(13, 8, 0), '2017-07-13')

    def test_friday_evening_goes_past_weekend_and_holiday(self) -> None:
        """Checks Friday 19:00 goes to Tuesday, past a weekend and holiday.

        Raises:
            AssertionError: If day 0 is wrong.
        """
        self.assertEqual(self.day_zero(14, 19, 0), '2017-07-18')

    def test_holiday_morning_goes_to_next_trading_day(self) -> None:
        """Checks a Monday holiday announcement goes to Tuesday.

        Raises:
            AssertionError: If day 0 is wrong.
        """
        self.assertEqual(self.day_zero(17, 11, 0), '2017-07-18')

    def test_after_the_last_date_is_none(self) -> None:
        """Checks an announcement after the calendar ends gives None.

        Raises:
            AssertionError: If a date is returned.
        """
        self.assertEqual(self.day_zero(19, 20, 0), 'none')

    def test_shift_and_days_between(self) -> None:
        """Checks trading-day arithmetic across the holiday.

        Raises:
            AssertionError: If an offset is wrong.
        """
        friday = datetime.date(2017, 7, 14)
        tuesday = datetime.date(2017, 7, 18)
        self.assertEqual(self.calendar.shift(friday, 1), tuesday)
        self.assertEqual(
            self.calendar.shift(tuesday, -2), datetime.date(2017, 7, 13)
        )
        self.assertIsNone(self.calendar.shift(friday, -10))
        self.assertIsNone(self.calendar.shift(datetime.date(2017, 7, 15), 1))
        self.assertEqual(self.calendar.days_between(friday, tuesday), 1)
        self.assertEqual(
            self.calendar.days_between(datetime.date(2017, 7, 12), tuesday),
            3,
        )


if __name__ == '__main__':
    unittest.main()
