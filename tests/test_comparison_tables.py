"""Tests for the Markdown comparison tables."""

import pathlib
import unittest

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    comparison_tables,
)


class ComparisonTablesTest(unittest.TestCase):
    """Checks the stars and the recomputed Table 1."""

    def setUp(self) -> None:
        """Creates the writer for a folder that is not read here.

        Raises:
            AssertionError: Never.
        """
        self.tables = comparison_tables.ComparisonTables(pathlib.Path('.'))

    def test_stars(self) -> None:
        """Checks the 1, 5 and 10 percent cut-offs.

        Raises:
            AssertionError: If a star count is wrong.
        """
        self.assertEqual(self.tables.stars(2.60), '***')
        self.assertEqual(self.tables.stars(-2.0), '**')
        self.assertEqual(self.tables.stars(1.70), '*')
        self.assertEqual(self.tables.stars(1.5), '')

    def test_table_one_has_the_printed_risk_reversals(self) -> None:
        """Checks the Markdown carries +0.00, +1.08 and -1.23.

        Raises:
            AssertionError: If a value is missing.
        """
        text = self.tables.table_one()
        self.assertIn('+1.08', text)
        self.assertIn('-1.23', text)
        self.assertIn('99.52 / 1.63 / 25.00%', text)


if __name__ == '__main__':
    unittest.main()
