"""Tests for the optional futures trading test on a tiny made-up market."""

import datetime
import unittest

import pandas
from data_and_analytics.backtesting.costs import futures_costs

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    event_trading_test,
    trading_calendar,
)


class SmallTest(event_trading_test.EventTradingTest):
    """The trading test with a short history requirement."""

    MINIMUM_HISTORY = 3


class EventTradingTestTest(unittest.TestCase):
    """Eight events on eight days, one share each."""

    def setUp(self) -> None:
        """Builds events, futures closes and a calendar.

        Raises:
            AssertionError: Never.
        """
        days = pandas.bdate_range('2017-03-01', periods=12)
        self.days = days
        self.calendar = trading_calendar.TradingCalendar(
            [day.date() for day in days],
        )
        expiry = pandas.Timestamp('2017-03-30')
        rows = []
        self.events = []
        for index in range(8):
            symbol = f'S{index}'
            day0 = days[index + 2]
            before = days[index + 1]
            rows.append(
                {
                    'symbol': symbol,
                    'expiry': expiry,
                    'date': before,
                    'close': 100.0,
                },
            )
            rows.append(
                {
                    'symbol': symbol,
                    'expiry': expiry,
                    'date': day0,
                    'close': 100.0 * (1.0 + 0.01 * (index - 3.5)),
                },
            )
            self.events.append(
                {
                    'symbol': symbol,
                    'day0': day0,
                    'expiry': expiry,
                    'rr_iv_1': 0.01 * index,
                    'pc_contracts_1': 0.5 - 0.01 * index,
                },
            )
        self.futures = pandas.DataFrame(rows)
        self.frame = pandas.DataFrame(self.events)
        self.test = SmallTest(self.frame, self.futures, self.calendar)

    def test_trade_returns_use_the_same_contract_on_both_days(self) -> None:
        """Checks returns are close over previous close minus one.

        Raises:
            AssertionError: If a return is wrong.
        """
        returns = self.test.trade_returns()
        self.assertAlmostEqual(returns[0], -0.035)
        self.assertAlmostEqual(returns[7], 0.035)

    def test_missing_price_gives_nan(self) -> None:
        """Checks an event with no day-0 close has no return.

        Raises:
            AssertionError: If a return is returned.
        """
        futures = self.futures.drop(index=[1])
        test = SmallTest(self.frame, futures, self.calendar)
        self.assertTrue(pandas.isna(test.trade_returns()[0]))

    def test_implausible_move_is_left_out(self) -> None:
        """Checks an 80 percent fall, a missed corporate action, gives NaN.

        Raises:
            AssertionError: If the move is kept.
        """
        futures = self.futures.copy()
        futures.loc[1, 'close'] = 20.0
        test = SmallTest(self.frame, futures, self.calendar)
        self.assertTrue(pandas.isna(test.trade_returns()[0]))

    def test_trailing_percentile_uses_only_earlier_events(self) -> None:
        """Checks event 4 ranks above the three earlier ones it can see.

        Raises:
            AssertionError: If the percentile or the history rule is wrong.
        """
        percentile = self.test.trailing_percentile(self.frame['rr_iv_1'])
        self.assertTrue(pandas.isna(percentile[0]))
        self.assertTrue(pandas.isna(percentile[2]))
        self.assertAlmostEqual(percentile[3], 1.0)
        self.assertAlmostEqual(percentile[5], 1.0)
        lower = self.test.trailing_percentile(-self.frame['rr_iv_1'])
        self.assertAlmostEqual(lower[4], 0.0)

    def test_percentile_ignores_events_of_the_same_day(self) -> None:
        """Checks events on the same day do not see each other.

        Raises:
            AssertionError: If a same-day event is used.
        """
        frame = self.frame.copy()
        frame.loc[7, 'day0'] = frame.loc[6, 'day0']
        test = SmallTest(frame, self.futures, self.calendar)
        percentile = test.trailing_percentile(frame['rr_iv_1'])
        self.assertAlmostEqual(percentile[6], percentile[7])
        self.assertTrue(pandas.notna(percentile[6]))

    def test_positions_from_percentiles(self) -> None:
        """Checks the thresholds at two thirds and one third.

        Raises:
            AssertionError: If a direction is wrong.
        """
        percentile = pandas.Series([0.9, 0.7, 0.5, 0.3, 0.1, float('nan')])
        direction = self.test.positions(percentile)
        self.assertEqual(list(direction), [1.0, 1.0, 0.0, -1.0, -1.0, 0.0])

    def test_backtest_gross_and_net(self) -> None:
        """Checks the mean trade return, hit rate and that costs reduce it.

        Raises:
            AssertionError: If a figure is wrong.
        """
        returns = self.test.trade_returns()
        direction = pandas.Series([-1.0, -1.0, 0, 0, 0, 0, 1.0, 1.0])
        costs = futures_costs.FuturesCosts(impact_cost=0.001)
        result = self.test.run_one(
            'toy',
            direction,
            returns,
            'costs',
            costs,
            '2017-03-01',
            '2017-03-31',
        )
        self.assertEqual(result.trades, 4)
        self.assertAlmostEqual(
            result.mean_trade_return, (0.035 + 0.025 + 0.025 + 0.035) / 4
        )
        self.assertEqual(result.hit_rate, 1.0)
        self.assertGreater(result.gross['mean'], result.net['mean'])
        self.assertGreater(result.round_trip_cost, 0.002)
        self.assertLess(result.round_trip_cost, 0.004)
        self.assertEqual(result.gross['periods'], 12)
        self.assertIsInstance(datetime.date(2017, 1, 1), datetime.date)


if __name__ == '__main__':
    unittest.main()
