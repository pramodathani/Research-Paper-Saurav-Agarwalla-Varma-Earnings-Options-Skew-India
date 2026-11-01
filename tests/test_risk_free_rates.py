"""Tests for the risk-free rate lookup."""

import math
import pathlib
import tempfile
import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    risk_free_rates,
)

FILE = (
    'Date,SMB,HML,WML,MF,RF\n'
    '1993-10,1,1,1,NA,NA\n'
    '2015-01,1,1,1,1,0.5\n'
    '2015-02,1,1,1,1,0.6\n'
)


class RiskFreeRatesTest(unittest.TestCase):
    """Checks conversion, lookup and the ends of the series."""

    def setUp(self) -> None:
        """Writes a small IIMA file and reads it.

        Raises:
            AssertionError: Never.
        """
        folder = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory()))
        path = folder / 'iima.csv'
        path.write_text(FILE)
        self.rates = risk_free_rates.RiskFreeRates(path)

    def test_monthly_percent_becomes_annual_continuous(self) -> None:
        """Checks 0.5 percent a month is ln(1.005) * 12 a year.

        Raises:
            AssertionError: If the rate is wrong.
        """
        rate = self.rates.rate(pandas.Timestamp('2015-01-20'))
        self.assertAlmostEqual(rate, math.log(1.005) * 12.0)

    def test_dates_outside_the_series_use_the_nearest_month(self) -> None:
        """Checks dates after and before the file use its ends.

        Raises:
            AssertionError: If an end rate is wrong.
        """
        later = self.rates.rate(pandas.Timestamp('2030-01-01'))
        earlier = self.rates.rate(pandas.Timestamp('2000-01-01'))
        self.assertAlmostEqual(later, math.log(1.006) * 12.0)
        self.assertAlmostEqual(earlier, math.log(1.005) * 12.0)


if __name__ == '__main__':
    unittest.main()
