"""Tests for the event-level regression table, with a stub for controls."""

import datetime
import math
import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    regression_dataset_builder,
    trading_calendar,
)


class StubControls:
    """Controls that return fixed numbers and record what was asked."""

    def __init__(self) -> None:
        """Starts with no recorded calls."""
        self.bhar_dates = []

    def beta(self, symbol, event_month):
        """Returns a beta of 1.2.

        Args:
            symbol: The share.
            event_month: The month.

        Returns:
            1.2.
        """
        return 1.2

    def momentum(self, symbol, event_month):
        """Returns a momentum of 0.3.

        Args:
            symbol: The share.
            event_month: The month.

        Returns:
            0.3.
        """
        return 0.3

    def average_close(self, symbol, month):
        """Returns a price of 100 in every month.

        Args:
            symbol: The share.
            month: The month.

        Returns:
            100.0.
        """
        return 100.0

    def buy_and_hold(self, symbol, dates):
        """Records the dates and returns 0.05.

        Args:
            symbol: The share.
            dates: The dates asked for.

        Returns:
            0.05.
        """
        self.bhar_dates = list(dates)
        return 0.05


class RegressionDatasetBuilderTest(unittest.TestCase):
    """One event on 16 June 2017 over a 60-day calendar."""

    def setUp(self) -> None:
        """Builds windows, a calendar and share counts.

        Raises:
            AssertionError: Never.
        """
        days = pandas.bdate_range('2017-04-01', periods=70)
        self.calendar = trading_calendar.TradingCalendar(
            [day.date() for day in days],
        )
        self.day0 = pandas.Timestamp('2017-06-16')
        rows = []
        for offset in range(-3, 1):
            rows.append(
                {
                    'event_id': 0,
                    'offset': offset,
                    'rr_iv': -0.01 * abs(offset),
                    'atm_iv': 0.30 + offset * 0.01,
                    'pc_contracts': 0.4,
                    'pc_value': 0.35,
                    'alt_rr_iv': -0.02,
                    'alt_atm_iv': 0.3,
                },
            )
        self.windows = pandas.DataFrame(rows)
        self.shares = pandas.DataFrame(
            {
                'symbol': ['AAA', 'AAA', 'AAA'],
                'broadcast': pandas.to_datetime(
                    ['2017-02-01', '2017-04-20', '2017-05-20'],
                ),
                'shares': [1.0e7, 2.0e7, 9.9e9],
            },
        )
        self.events = pandas.DataFrame(
            {
                'symbol': ['AAA'],
                'day0': [self.day0],
                'sue': [0.8],
                'sue_alternative': [0.7],
            },
        )
        self.controls = StubControls()
        self.builder = regression_dataset_builder.RegressionDatasetBuilder(
            self.windows,
            self.controls,
            self.calendar,
            self.shares,
        )

    def test_lagged_variables(self) -> None:
        """Checks day -1, -2 and -3 values go into the right columns.

        Raises:
            AssertionError: If a lag is wrong.
        """
        row = self.builder.build(self.events).iloc[0]
        self.assertAlmostEqual(row['rr_iv_1'], -0.01)
        self.assertAlmostEqual(row['rr_iv_3'], -0.03)
        self.assertAlmostEqual(row['atm_iv_2'], 0.28)
        self.assertEqual(row['pc_contracts_1'], 0.4)

    def test_size_uses_only_filings_before_the_pre_event_month(self) -> None:
        """Checks May starts on 1 May, so the 20 May filing is not used.

        The June event's pre-EA month is May, and the last filing before
        1 May is the one of 20 April with 2e7 shares at a price of 100,
        which is 2000 million rupees.

        Raises:
            AssertionError: If the wrong filing is used.
        """
        row = self.builder.build(self.events).iloc[0]
        self.assertAlmostEqual(row['size'], math.log(2000.0))

    def test_size_is_missing_without_an_earlier_filing(self) -> None:
        """Checks a share with no filing before the month gets NaN.

        Raises:
            AssertionError: If a size is returned.
        """
        events = self.events.assign(symbol='ZZZ')
        row = self.builder.build(events).iloc[0]
        self.assertTrue(math.isnan(row['size']))

    def test_bhar_covers_days_minus_ten_to_minus_two(self) -> None:
        """Checks the nine trading days asked for.

        Raises:
            AssertionError: If the days are wrong.
        """
        row = self.builder.build(self.events).iloc[0]
        dates = self.controls.bhar_dates
        self.assertEqual(len(dates), 9)
        self.assertEqual(dates[0], pandas.Timestamp('2017-06-02'))
        self.assertEqual(dates[-1], pandas.Timestamp('2017-06-14'))
        self.assertEqual(row['bhar'], 0.05)

    def test_controls_and_labels(self) -> None:
        """Checks beta, momentum and the year-quarter label.

        Raises:
            AssertionError: If a value is wrong.
        """
        row = self.builder.build(self.events).iloc[0]
        self.assertEqual(row['beta'], 1.2)
        self.assertEqual(row['momentum'], 0.3)
        self.assertEqual(row['year_quarter'], '2017Q2')

    def test_event_too_early_for_bhar_gives_nan(self) -> None:
        """Checks day 0 within ten days of the calendar start gives NaN.

        Raises:
            AssertionError: If a return is returned.
        """
        events = self.events.assign(day0=[pandas.Timestamp('2017-04-05')])
        row = self.builder.build(events).iloc[0]
        self.assertTrue(numpy.isnan(row['bhar']))
        self.assertIsInstance(datetime.date(2017, 1, 1), datetime.date)


if __name__ == '__main__':
    unittest.main()
