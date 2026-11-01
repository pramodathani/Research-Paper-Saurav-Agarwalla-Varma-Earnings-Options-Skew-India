"""Tests that Table 1 is reproduced to the paper's printed digits."""

import unittest

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    table_one_example,
)


class TableOneExampleTest(unittest.TestCase):
    """Compares each printed cell of Table 1 on page 465."""

    def setUp(self) -> None:
        """Builds the three columns.

        Raises:
            AssertionError: Never.
        """
        self.columns = table_one_example.TableOneExample().build()

    def test_spots(self) -> None:
        """Checks the spot prices 100, 101 and 99.

        Raises:
            AssertionError: If a spot differs.
        """
        spots = [column.spot for column in self.columns]
        self.assertEqual([round(spot, 6) for spot in spots], [100, 101, 99])

    def test_strikes(self) -> None:
        """Checks the in, at and out of the money strikes to two places.

        Raises:
            AssertionError: If a strike differs from the paper.
        """
        expected = [
            (99.52, 100.00, 100.48),
            (100.39, 101.00, 101.61),
            (98.40, 99.00, 99.61),
        ]
        for column, strikes in zip(self.columns, expected, strict=True):
            for value, printed in zip(column.strikes, strikes, strict=True):
                self.assertAlmostEqual(value, printed, places=2)

    def test_premiums(self) -> None:
        """Checks the premiums to two places.

        Raises:
            AssertionError: If a premium differs from the paper.
        """
        expected = [
            (1.63, 1.38, 1.16),
            (2.04, 1.75, 1.50),
            (2.09, 1.74, 1.43),
        ]
        for column, premiums in zip(self.columns, expected, strict=True):
            for value, printed in zip(column.premiums, premiums, strict=True):
                self.assertAlmostEqual(value, printed, places=2)

    def test_implied_volatilities(self) -> None:
        """Checks the volatilities, in percent, to two places.

        Raises:
            AssertionError: If a volatility differs from the paper.
        """
        expected = [
            (25.00, 25.00, 25.00),
            (30.86, 31.37, 31.94),
            (32.43, 31.78, 31.20),
        ]
        for column, printed in zip(self.columns, expected, strict=True):
            for value, cell in zip(column.volatilities, printed, strict=True):
                self.assertAlmostEqual(100.0 * value, cell, places=2)

    def test_risk_reversals(self) -> None:
        """Checks RR-IV is 0.00, +1.08 and -1.23 percentage points.

        Raises:
            AssertionError: If a risk reversal differs from the paper.
        """
        risk_reversals = [column.risk_reversal for column in self.columns]
        for value, printed in zip(
            risk_reversals,
            [0.00, 1.08, -1.23],
            strict=True,
        ):
            self.assertAlmostEqual(value, printed, places=2)


if __name__ == '__main__':
    unittest.main()
