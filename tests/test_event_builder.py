"""Tests for the event rules on a made-up week with one expiry."""

import datetime
import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    event_builder,
    trading_calendar,
)


class EventBuilderTest(unittest.TestCase):
    """Trading days are 3 to 7 and 10 to 14 July 2017, expiry on the 12th."""

    def setUp(self) -> None:
        """Builds a calendar, expiries and the days options traded.

        Raises:
            AssertionError: Never.
        """
        days = [3, 4, 5, 6, 7, 10, 11, 12, 13, 14]
        dates = [datetime.date(2017, 7, day) for day in days]
        calendar = trading_calendar.TradingCalendar(dates)
        expiries = pandas.DataFrame(
            {
                'symbol': ['AAA', 'AAA'],
                'expiry': pandas.to_datetime(['2017-07-12', '2017-08-31']),
            },
        )
        active = pandas.DataFrame(
            {
                'date': pandas.to_datetime(
                    [f'2017-07-{day:02d}' for day in days],
                ),
                'symbol': 'AAA',
            },
        )
        self.builder = event_builder.EventBuilder(calendar, expiries, active)

    def panel(self, symbol: str, broadcast: str) -> pandas.DataFrame:
        """Builds a one-row EPS panel.

        Args:
            symbol: The share.
            broadcast: The broadcast time.

        Returns:
            The panel.
        """
        return pandas.DataFrame(
            {
                'symbol': [symbol],
                'period_end': [pandas.Timestamp('2017-06-30')],
                'broadcast': [pandas.Timestamp(broadcast)],
                'eps': [1.0],
                'shares': [1.0e7],
                'sue': [0.5],
                'sue_alternative': [0.4],
            },
        )

    def test_early_announcement_is_kept(self) -> None:
        """Checks an announcement five trading days before expiry is kept.

        Raises:
            AssertionError: If the event is dropped.
        """
        events = self.builder.build(self.panel('AAA', '2017-07-05 11:00'))
        row = events.iloc[0]
        self.assertTrue(row['keep'])
        self.assertEqual(row['day0'], pandas.Timestamp('2017-07-05'))
        self.assertEqual(row['expiry'], pandas.Timestamp('2017-07-12'))
        self.assertEqual(row['trading_days_to_expiry'], 5)

    def test_after_hours_moves_day_zero_and_can_drop_the_event(self) -> None:
        """Checks Friday 7 July after the close gives Monday 10 July, two days
        from expiry, and is dropped.

        Raises:
            AssertionError: If the event is kept.
        """
        events = self.builder.build(self.panel('AAA', '2017-07-07 19:00'))
        row = events.iloc[0]
        self.assertEqual(row['day0'], pandas.Timestamp('2017-07-10'))
        self.assertFalse(row['keep'])
        self.assertEqual(row['reason'], 'within three trading days of expiry')

    def test_exactly_three_trading_days_is_kept(self) -> None:
        """Checks day 0 on the 7th, three trading days before the 12th.

        Raises:
            AssertionError: If the event is dropped.
        """
        events = self.builder.build(self.panel('AAA', '2017-07-07 10:00'))
        self.assertEqual(events.iloc[0]['trading_days_to_expiry'], 3)
        self.assertTrue(events.iloc[0]['keep'])

    def test_share_without_options_is_dropped(self) -> None:
        """Checks a share with no options on day 0 is dropped.

        Raises:
            AssertionError: If the event is kept.
        """
        events = self.builder.build(self.panel('BBB', '2017-07-05 11:00'))
        self.assertEqual(events.iloc[0]['reason'], 'no options traded on day 0')

    def test_announcement_after_the_calendar_is_dropped(self) -> None:
        """Checks an announcement after the last trading date is dropped.

        Raises:
            AssertionError: If the event is kept.
        """
        events = self.builder.build(self.panel('AAA', '2017-07-14 20:00'))
        self.assertEqual(events.iloc[0]['reason'], 'no day 0')


if __name__ == '__main__':
    unittest.main()
