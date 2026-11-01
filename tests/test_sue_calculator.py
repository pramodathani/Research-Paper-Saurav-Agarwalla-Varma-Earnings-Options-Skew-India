"""Tests for SUE on small series worked out by hand."""

import math
import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    sue_calculator,
)


class SueCalculatorTest(unittest.TestCase):
    """Uses EPS equal to the quarter number, with one shock."""

    def setUp(self) -> None:
        """Creates a calculator.

        Raises:
            AssertionError: Never.
        """
        self.calculator = sue_calculator.SueCalculator()

    def shocked_series(self) -> pandas.Series:
        """Builds EPS = quarter number for quarters 0 to 23, but 25 at 22.

        Returns:
            The EPS series indexed by quarter number.
        """
        values = {quarter: float(quarter) for quarter in range(24)}
        values[22] = 25.0
        return pandas.Series(values)

    def test_hand_worked_sue(self) -> None:
        """Checks quarter 23: expected 23.375, surprise -0.375, SUE -0.3536.

        Raises:
            AssertionError: If a figure differs from the hand calculation.
        """
        table = self.calculator.compute(self.shocked_series())
        row = table.loc[23]
        self.assertAlmostEqual(row['expected'], 23.375)
        self.assertAlmostEqual(row['surprise'], -0.375)
        self.assertAlmostEqual(row['sigma'], math.sqrt(1.125))
        self.assertAlmostEqual(row['sue'], -0.375 / math.sqrt(1.125))

    def test_shock_quarter_surprise(self) -> None:
        """Checks the shocked quarter itself has a surprise of 3.

        Raises:
            AssertionError: If the surprise is wrong.
        """
        table = self.calculator.compute(self.shocked_series())
        self.assertAlmostEqual(table.loc[22, 'surprise'], 3.0)

    def test_perfectly_predictable_series_has_no_sue(self) -> None:
        """Checks zero standard deviation gives NaN rather than infinity.

        Raises:
            AssertionError: If SUE is not NaN.
        """
        series = pandas.Series({q: float(q) for q in range(24)})
        table = self.calculator.compute(series)
        self.assertTrue(math.isnan(table.loc[23, 'sue']))

    def test_needs_twenty_quarters_of_history(self) -> None:
        """Checks the first SUE appears at the twenty-first quarter.

        Raises:
            AssertionError: If SUE appears too early or late.
        """
        values = {q: float(q * q % 7) + q for q in range(30)}
        table = self.calculator.compute(pandas.Series(values))
        first = table['sue'].first_valid_index()
        self.assertEqual(first, 20)

    def test_missing_quarter_blocks_sue(self) -> None:
        """Checks a gap in the history gives NaN for the quarters it touches.

        Raises:
            AssertionError: If a value is returned across the gap.
        """
        values = {q: float(q * q % 7) + q for q in range(30)}
        complete = self.calculator.compute(pandas.Series(values))
        self.assertFalse(math.isnan(complete.loc[29, 'sue']))
        del values[12]
        table = self.calculator.compute(pandas.Series(values))
        self.assertTrue(table.loc[20:29, 'sue'].isna().all())

    def test_quarter_index_is_consecutive(self) -> None:
        """Checks adjacent quarter ends differ by one, across a year end.

        Raises:
            AssertionError: If the index is not consecutive.
        """
        dates = pandas.Series(
            pandas.to_datetime(['2015-09-30', '2015-12-31', '2016-03-31']),
        )
        index = self.calculator.quarter_index(dates)
        self.assertEqual(list(index.diff().dropna()), [1, 1])


if __name__ == '__main__':
    unittest.main()
