"""Tests for the event-day table on a small made-up market."""

import math
import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    event_window_builder,
    trading_calendar,
)


class EventWindowBuilderTest(unittest.TestCase):
    """Sixty weekdays, one share, an event on the fortieth."""

    def setUp(self) -> None:
        """Builds a calendar, a smile panel and a ratio table.

        Raises:
            AssertionError: Never.
        """
        days = pandas.bdate_range('2017-05-01', periods=60)
        self.calendar = trading_calendar.TradingCalendar(
            [day.date() for day in days],
        )
        rows = []
        for day in days:
            level = 0.30 if day.month == 5 else 0.36
            if day == days[39]:
                level = 0.45
            rows.append(
                {
                    'date': day,
                    'symbol': 'AAA',
                    'expiry': pandas.Timestamp('2017-07-27'),
                    'atm_iv': level,
                    'iv_75': level + 0.01,
                    'iv_25': level - 0.01,
                    'rr_iv': -0.02,
                    'alt_atm_iv': level,
                    'alt_rr_iv': -0.01,
                },
            )
        self.smile = pandas.DataFrame(rows)
        self.ratios = pandas.DataFrame(
            {
                'date': days,
                'symbol': 'AAA',
                'os_ratio': 1.0,
                'of_ratio': 0.5,
                'pc_contracts': 0.4,
                'pc_value': 0.4,
            },
        )
        self.day0 = days[39]
        self.events = pandas.DataFrame(
            {
                'symbol': ['AAA'],
                'day0': [self.day0],
                'expiry': [pandas.Timestamp('2017-07-27')],
                'sue': [0.7],
                'sue_alternative': [0.6],
            },
        )

    def build(self) -> pandas.DataFrame:
        """Builds the table.

        Returns:
            The event-day table.
        """
        builder = event_window_builder.EventWindowBuilder(
            self.calendar,
            self.smile,
            self.ratios,
        )
        return builder.build(self.events)

    def test_has_twenty_one_offsets_with_day_zero_at_zero(self) -> None:
        """Checks offsets run -10 to 10 and offset 0 is day 0.

        Raises:
            AssertionError: If the offsets or day 0 are wrong.
        """
        table = self.build()
        self.assertEqual(list(table['offset']), list(range(-10, 11)))
        row = table[table['offset'] == 0].iloc[0]
        self.assertEqual(row['date'], self.day0)
        self.assertAlmostEqual(row['atm_iv'], 0.45)

    def test_offsets_count_trading_days(self) -> None:
        """Checks offset -1 is the previous trading day.

        Raises:
            AssertionError: If the date is wrong.
        """
        table = self.build()
        previous = table[table['offset'] == -1].iloc[0]['date']
        self.assertEqual(previous, self.day0 - pandas.offsets.BDay(1))

    def test_normalisation_uses_the_month_before_the_event_month(self) -> None:
        """Checks day 0 is divided by May's mean of 0.30, not June's.

        Raises:
            AssertionError: If the base month is wrong.
        """
        table = self.build()
        self.assertEqual(self.day0.month, 6)
        row = table[table['offset'] == 0].iloc[0]
        self.assertAlmostEqual(row['atm_iv_normalised'], 0.45 / 0.30)
        row = table[table['offset'] == -1].iloc[0]
        self.assertAlmostEqual(row['atm_iv_normalised'], 0.36 / 0.30)

    def test_thin_base_month_gives_nan(self) -> None:
        """Checks fewer than five base days leave the normalised level empty.

        Raises:
            AssertionError: If a value is returned.
        """
        self.smile = self.smile[
            (self.smile['date'].dt.month != 5)
            | (self.smile['date'] < '2017-05-05')
        ]
        table = self.build()
        value = table[table['offset'] == 0].iloc[0]['atm_iv_normalised']
        self.assertTrue(math.isnan(value))

    def test_window_clipped_at_the_calendar_end(self) -> None:
        """Checks days after the last trading date are dropped.

        Raises:
            AssertionError: If offsets beyond the calendar remain.
        """
        self.events = self.events.assign(day0=[self.calendar.dates[-3]])
        self.events['day0'] = pandas.to_datetime(self.events['day0'])
        table = self.build()
        self.assertEqual(table['offset'].max(), 2)

    def test_event_series_is_preferred_over_the_near_month(self) -> None:
        """Checks the event's own series is used while it trades.

        A second, near-month series with a different level is added for the
        day before the event. The event's series (expiring 27 July) must be
        used, and the near month on the day the event-series row is missing.

        Raises:
            AssertionError: If the wrong series is used.
        """
        before = self.day0 - pandas.offsets.BDay(1)
        self.smile['series_rank'] = 2
        near = self.smile.copy()
        near['expiry'] = pandas.Timestamp('2017-06-29')
        near['series_rank'] = 1
        near['atm_iv'] = 0.99
        near = near[near['date'] <= pandas.Timestamp('2017-06-29')]
        own = self.smile[
            self.smile['date'] != self.day0 + pandas.offsets.BDay(3)
        ]
        self.smile = pandas.concat([own, near], ignore_index=True)
        table = self.build().set_index('offset')
        self.assertAlmostEqual(table.loc[-1, 'atm_iv'], 0.36)
        self.assertEqual(table.loc[-1, 'smile_series'], 'event')
        self.assertEqual(before, table.loc[-1, 'date'])
        self.assertEqual(table.loc[3, 'smile_series'], 'near')
        self.assertAlmostEqual(table.loc[3, 'atm_iv'], 0.99)

    def test_ratios_and_surprise_are_carried(self) -> None:
        """Checks volume ratios and SUE are on every row.

        Raises:
            AssertionError: If a column is missing or wrong.
        """
        table = self.build()
        self.assertTrue((table['os_ratio'] == 1.0).all())
        self.assertTrue((table['sue'] == 0.7).all())


if __name__ == '__main__':
    unittest.main()
