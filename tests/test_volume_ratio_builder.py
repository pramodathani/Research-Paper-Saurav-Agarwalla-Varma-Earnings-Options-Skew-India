"""Tests for the volume ratios on a tiny market with known sums."""

import math
import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    volume_ratio_builder,
)


class VolumeRatioBuilderTest(unittest.TestCase):
    """Two stocks on one day, worked out by hand."""

    def setUp(self) -> None:
        """Builds the F&O and cash tables.

        Raises:
            AssertionError: Never.
        """
        day = pandas.Timestamp('2017-07-14')
        expiry = pandas.Timestamp('2017-07-27')
        later = pandas.Timestamp('2017-08-31')
        rows = [
            ('AAA', 'FUT', expiry, '', 10, 1000.0),
            ('AAA', 'FUT', later, '', 5, 500.0),
            ('AAA', 'OPT', expiry, 'CE', 30, 600.0),
            ('AAA', 'OPT', expiry, 'CE', 10, 200.0),
            ('AAA', 'OPT', later, 'PE', 20, 400.0),
            ('BBB', 'OPT', expiry, 'PE', 7, 70.0),
        ]
        self.derivatives = pandas.DataFrame(
            [
                {
                    'date': day,
                    'symbol': symbol,
                    'kind': kind,
                    'expiry': expiry_date,
                    'option_type': option_type,
                    'contracts': contracts,
                    'value_rupees': value,
                }
                for symbol, kind, expiry_date, option_type, contracts, value in rows
            ],
        )
        self.cash = pandas.DataFrame(
            {
                'date': [day, day, day],
                'symbol': ['AAA', 'AAA', 'BBB'],
                'series': ['BE', 'EQ', 'EQ'],
                'value_rupees': [9999.0, 4000.0, 700.0],
            },
        )
        builder = volume_ratio_builder.VolumeRatioBuilder()
        table = builder.build_frame(self.derivatives, self.cash)
        self.table = table.set_index('symbol')

    def test_sums_over_all_expiries(self) -> None:
        """Checks option and future totals add every expiry.

        Raises:
            AssertionError: If a sum is wrong.
        """
        row = self.table.loc['AAA']
        self.assertEqual(row['option_notional'], 1200.0)
        self.assertEqual(row['future_notional'], 1500.0)
        self.assertEqual(row['call_contracts'], 40)
        self.assertEqual(row['put_contracts'], 20)

    def test_ratios(self) -> None:
        """Checks O/S, O/F and P/C against hand values.

        Raises:
            AssertionError: If a ratio is wrong.
        """
        row = self.table.loc['AAA']
        self.assertAlmostEqual(row['os_ratio'], 1200.0 / 4000.0)
        self.assertAlmostEqual(row['of_ratio'], 1200.0 / 1500.0)
        self.assertAlmostEqual(row['pc_contracts'], 20.0 / 40.0)
        self.assertAlmostEqual(row['pc_value'], 400.0 / 800.0)

    def test_series_eq_is_preferred(self) -> None:
        """Checks the BE row is ignored when an EQ row exists.

        Raises:
            AssertionError: If the BE turnover is used.
        """
        self.assertEqual(self.table.loc['AAA', 'stock_value'], 4000.0)

    def test_no_calls_or_futures_gives_nan_not_infinity(self) -> None:
        """Checks a stock with only puts and no futures has NaN ratios.

        Raises:
            AssertionError: If a ratio is finite or infinite.
        """
        row = self.table.loc['BBB']
        self.assertTrue(math.isnan(row['pc_contracts']))
        self.assertTrue(math.isnan(row['pc_value']))
        self.assertTrue(math.isnan(row['of_ratio']))
        self.assertAlmostEqual(row['os_ratio'], 0.1)


if __name__ == '__main__':
    unittest.main()
