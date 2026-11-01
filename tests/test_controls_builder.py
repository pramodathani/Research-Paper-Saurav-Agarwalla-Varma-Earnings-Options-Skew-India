"""Tests for the controls on a small made-up market."""

import math
import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    controls_builder,
)


class ControlsBuilderTest(unittest.TestCase):
    """Seventy-two months of one market and two stocks with known betas."""

    def setUp(self) -> None:
        """Builds daily returns for 2012 to 2017 from monthly shocks.

        The market return in each month is a repeating pattern. Stock AAA
        earns exactly twice the market return and BBB trades only in the
        last 24 months.

        Raises:
            AssertionError: Never.
        """
        months = pandas.period_range('2012-01', '2017-12', freq='M')
        pattern = numpy.array([0.04, -0.03, 0.02, 0.05, -0.04, 0.01, 0.03])
        market_returns = pandas.Series(
            [pattern[i % 7] for i in range(len(months))],
            index=months,
        )
        level = 100.0
        rows = []
        market_rows = []
        for month in months:
            first = month.start_time
            last = month.end_time.normalize()
            market_rows.append((first, level))
            level *= 1.0 + market_returns[month]
            market_rows.append((last, level))
            for symbol, scale, start in [
                ('AAA', 2.0, '2012-01'),
                ('BBB', 1.0, '2016-01'),
            ]:
                if month < pandas.Period(start):
                    continue
                rows.append(
                    {
                        'date': last,
                        'symbol': symbol,
                        'close': 50.0 + len(rows),
                        'ret': scale * market_returns[month],
                    },
                )
        self.market = pandas.Series(
            dict(market_rows),
        ).sort_index()
        self.market = self.market[~self.market.index.duplicated(keep='last')]
        self.returns = pandas.DataFrame(rows)
        self.builder = controls_builder.ControlsBuilder(
            self.returns,
            self.market,
        )

    def test_beta_of_a_double_market_stock_is_two(self) -> None:
        """Checks beta is 2 for a stock that earns twice the market.

        Raises:
            AssertionError: If beta is not 2.
        """
        beta = self.builder.beta('AAA', pandas.Period('2017-06'))
        self.assertAlmostEqual(beta, 2.0, places=6)

    def test_beta_needs_enough_history(self) -> None:
        """Checks a stock with 24 months has no beta and an unknown one too.

        Raises:
            AssertionError: If a beta is returned.
        """
        self.assertTrue(
            math.isnan(self.builder.beta('BBB', pandas.Period('2017-06'))),
        )
        self.assertTrue(
            math.isnan(self.builder.beta('ZZZ', pandas.Period('2017-06'))),
        )

    def test_beta_uses_only_months_before_the_event_month(self) -> None:
        """Checks that the event month's own return does not enter the beta.

        Raises:
            AssertionError: If the beta changes when the event month does.
        """
        month = pandas.Period('2016-03')
        before = self.builder.beta_table.loc[month - 1, 'AAA']
        self.assertEqual(self.builder.beta('AAA', month), before)

    def test_momentum_compounds_twelve_months(self) -> None:
        """Checks momentum is the product of months t-12 to t-1 minus one.

        Raises:
            AssertionError: If the value is wrong.
        """
        event_month = pandas.Period('2017-06')
        months = pandas.period_range('2016-06', '2017-05', freq='M')
        expected = (1.0 + self.builder.monthly.loc[months, 'AAA']).prod() - 1.0
        value = self.builder.momentum('AAA', event_month)
        self.assertAlmostEqual(value, expected)
        self.assertTrue(
            math.isnan(self.builder.momentum('BBB', pandas.Period('2016-06'))),
        )

    def test_buy_and_hold(self) -> None:
        """Checks BHAR compounds the given days and fails on a missing day.

        Raises:
            AssertionError: If the value is wrong.
        """
        dates = list(self.returns[self.returns['symbol'] == 'AAA']['date'][:3])
        values = self.returns[self.returns['symbol'] == 'AAA']['ret'][:3]
        expected = float((1.0 + values).prod() - 1.0)
        self.assertAlmostEqual(
            self.builder.buy_and_hold('AAA', dates),
            expected,
        )
        dates.append(pandas.Timestamp('1999-01-01'))
        self.assertTrue(math.isnan(self.builder.buy_and_hold('AAA', dates)))

    def test_average_close(self) -> None:
        """Checks the monthly mean close and an unknown symbol.

        Raises:
            AssertionError: If a value is wrong.
        """
        month = pandas.Period('2017-06')
        closes = self.returns[
            (self.returns['symbol'] == 'AAA')
            & (self.returns['date'].dt.to_period('M') == month)
        ]['close']
        self.assertAlmostEqual(
            self.builder.average_close('AAA', month),
            closes.mean(),
        )
        self.assertTrue(
            math.isnan(self.builder.average_close('ZZZ', month)),
        )


if __name__ == '__main__':
    unittest.main()
