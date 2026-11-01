"""Tests for winsorising."""

import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    winsoriser,
)


class WinsoriserTest(unittest.TestCase):
    """Checks clipping at the 5th and 95th percentiles."""

    def test_clips_the_tails(self) -> None:
        """Checks values 1 to 101 are clipped to 6 and 96.

        Raises:
            AssertionError: If the clipping is wrong.
        """
        data = pandas.DataFrame({'x': list(range(1, 102)), 'y': 1.0})
        result = winsoriser.Winsoriser().apply(data, ['x'])
        self.assertEqual(result['x'].min(), 6.0)
        self.assertEqual(result['x'].max(), 96.0)
        self.assertEqual(result['x'].iloc[49], 50.0)
        self.assertTrue((result['y'] == 1.0).all())

    def test_missing_values_are_kept_and_input_is_untouched(self) -> None:
        """Checks NaN stays NaN and the original table is not changed.

        Raises:
            AssertionError: If a value changed.
        """
        data = pandas.DataFrame(
            {'x': [float(v) for v in range(1, 41)] + [float('nan')] * 10},
        )
        result = winsoriser.Winsoriser().apply(data, ['x'])
        self.assertEqual(int(result['x'].isna().sum()), 10)
        self.assertEqual(data['x'].max(), 40.0)
        self.assertLess(result['x'].max(), 40.0)


if __name__ == '__main__':
    unittest.main()
