"""Tests for daily returns adjusted for splits, bonuses and dividends."""

import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    adjusted_return_builder,
)


class AdjustedReturnBuilderTest(unittest.TestCase):
    """Uses a share whose raw closes are made up with known answers."""

    DATES = pandas.to_datetime(
        ['2017-07-10', '2017-07-11', '2017-07-12', '2017-07-14', '2017-07-17'],
    )

    def cash(self, closes: list[float], series: str = 'EQ') -> pandas.DataFrame:
        """Builds cash rows for one share on the five test days.

        Args:
            closes: The five closes; each previous close is the day before.
            series: The series label.

        Returns:
            A table in the cash reader's layout.
        """
        previous = [closes[0]] + closes[:-1]
        return pandas.DataFrame(
            {
                'date': self.DATES,
                'symbol': 'AAA',
                'series': series,
                'close': closes,
                'previous_close': previous,
            },
        )

    def actions(self, rows: list[tuple[str, str, float]]) -> pandas.DataFrame:
        """Builds an action table.

        Args:
            rows: Tuples of ex-date, kind and value.

        Returns:
            The table.
        """
        return pandas.DataFrame(
            [
                {
                    'symbol': 'AAA',
                    'ex_date': pandas.Timestamp(date),
                    'kind': kind,
                    'value': value,
                }
                for date, kind, value in rows
            ],
            columns=['symbol', 'ex_date', 'kind', 'value'],
        )

    def build(self, closes, rows) -> pandas.DataFrame:
        """Runs the builder.

        Args:
            closes: The five closes.
            rows: The corporate actions.

        Returns:
            The return table.
        """
        builder = adjusted_return_builder.AdjustedReturnBuilder()
        return builder.build(self.cash(closes), self.actions(rows))

    def test_no_actions_is_the_simple_return(self) -> None:
        """Checks a plain return is close over previous close minus one.

        Raises:
            AssertionError: If a return is wrong.
        """
        table = self.build([100.0, 110.0, 99.0, 99.0, 108.9], [])
        self.assertAlmostEqual(table['ret'].iloc[1], 0.10)
        self.assertAlmostEqual(table['ret'].iloc[2], -0.10)
        self.assertAlmostEqual(table['ret'].iloc[4], 0.10)

    def test_bonus_is_not_a_loss(self) -> None:
        """Checks a 1:1 bonus that halves the price gives a 0 percent return.

        Raises:
            AssertionError: If a return is wrong.
        """
        table = self.build(
            [100.0, 100.0, 50.0, 55.0, 55.0],
            [('2017-07-12', 'factor', 0.5)],
        )
        self.assertAlmostEqual(table['ret'].iloc[2], 0.0)
        self.assertAlmostEqual(table['ret'].iloc[3], 0.10)
        self.assertFalse(table['extreme'].any())

    def test_dividend_is_added_back(self) -> None:
        """Checks a 5 rupee dividend turns a 5 percent drop into zero.

        Raises:
            AssertionError: If the return is wrong.
        """
        table = self.build(
            [100.0, 100.0, 95.0, 95.0, 95.0],
            [('2017-07-12', 'dividend', 5.0)],
        )
        self.assertAlmostEqual(table['ret'].iloc[2], 0.0)

    def test_ex_date_on_a_holiday_moves_to_the_next_trading_day(self) -> None:
        """Checks an ex-date of 13 July is applied on 14 July.

        Raises:
            AssertionError: If the action is applied on the wrong day.
        """
        table = self.build(
            [100.0, 100.0, 100.0, 50.0, 50.0],
            [('2017-07-13', 'factor', 0.5)],
        )
        self.assertAlmostEqual(table['ret'].iloc[3], 0.0)
        self.assertAlmostEqual(table['ret'].iloc[2], 0.0)

    def test_action_before_the_first_day_is_ignored(self) -> None:
        """Checks an old action does not hit the first day of data.

        Raises:
            AssertionError: If the first day is adjusted.
        """
        table = self.build(
            [100.0, 110.0, 110.0, 110.0, 110.0],
            [('2017-01-01', 'factor', 0.5)],
        )
        self.assertAlmostEqual(table['ret'].iloc[0], 0.0)
        self.assertAlmostEqual(table['ret'].iloc[1], 0.10)

    def test_missed_split_is_flagged_and_zeroed(self) -> None:
        """Checks a 90 percent one-day drop is flagged and set to zero.

        Raises:
            AssertionError: If it is not flagged.
        """
        table = self.build([100.0, 100.0, 10.0, 10.0, 10.0], [])
        self.assertTrue(table['extreme'].iloc[2])
        self.assertAlmostEqual(table['ret'].iloc[2], 0.0)

    def test_series_eq_is_preferred_over_be(self) -> None:
        """Checks one row per day with the EQ close kept.

        Raises:
            AssertionError: If the BE row is used.
        """
        cash = pandas.concat(
            [
                self.cash([100.0, 110.0, 110.0, 110.0, 110.0], 'EQ'),
                self.cash([1.0, 1.0, 1.0, 1.0, 1.0], 'BE'),
            ],
        )
        builder = adjusted_return_builder.AdjustedReturnBuilder()
        table = builder.build(cash, self.actions([]))
        self.assertEqual(len(table), 5)
        self.assertAlmostEqual(table['ret'].iloc[1], 0.10)


if __name__ == '__main__':
    unittest.main()
