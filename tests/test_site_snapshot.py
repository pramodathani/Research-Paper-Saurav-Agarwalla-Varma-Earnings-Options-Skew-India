"""Tests for the companion page's snapshot builder."""

import math
import pathlib
import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    site_snapshot,
)


class SiteSnapshotTest(unittest.TestCase):
    """Checks rounding, the event-study lines and Table 1."""

    def setUp(self) -> None:
        """Creates a builder for a folder that is not read here.

        Raises:
            AssertionError: Never.
        """
        self.builder = site_snapshot.SiteSnapshot(pathlib.Path('.'))

    def test_clean_rounds_and_removes_nan(self) -> None:
        """Checks floats are rounded, NaN becomes None and numpy is unwrapped.

        Raises:
            AssertionError: If a value is wrong.
        """
        self.assertEqual(self.builder.clean(0.123456789), 0.1235)
        self.assertIsNone(self.builder.clean(float('nan')))
        self.assertIsNone(self.builder.clean(math.inf))
        self.assertEqual(self.builder.clean(numpy.int64(7)), 7)
        self.assertEqual(self.builder.clean('text'), 'text')

    def test_series_by_tercile(self) -> None:
        """Checks lines are keyed by tercile and ordered by offset.

        Raises:
            AssertionError: If a line is wrong.
        """
        table = pandas.DataFrame(
            {
                'tercile': [1, 1, 3, 3],
                'offset': [0, -1, -1, 0],
                'mean': [0.5, 0.25, 1.0, 2.0],
            },
        )
        lines = self.builder.series(table, 'tercile')
        self.assertEqual(lines['offsets'], [-1, 0])
        self.assertEqual(lines['1'], [0.25, 0.5])
        self.assertEqual(lines['3'], [1.0, 2.0])

    def test_table_one_and_paper(self) -> None:
        """Checks Table 1's risk reversals and that the paper values load.

        Raises:
            AssertionError: If a value is wrong.
        """
        columns = self.builder.table_one()
        self.assertEqual(
            [c['risk_reversal'] for c in columns], [0.0, 1.08, -1.23]
        )
        paper = self.builder.paper()
        self.assertEqual(paper['table_4']['rr_iv_1'], 0.162)
        self.assertTrue(
            any(
                row['variable'] == 'RR-IV' and row['coefficient'] == 2.514
                for row in paper['regressions']
            ),
        )


if __name__ == '__main__':
    unittest.main()
