"""Tests for Tables 6 to 9 on a made-up event dataset with a known signal."""

import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    descriptive_statistics,
    regression_tables,
)


class RegressionTablesTest(unittest.TestCase):
    """SUE depends positively on RR-IV and negatively on P/C at day -1."""

    def setUp(self) -> None:
        """Builds 600 events over 40 firms and 12 quarters.

        Raises:
            AssertionError: Never.
        """
        generator = numpy.random.default_rng(7)
        rows = []
        for index in range(600):
            firm = index % 40
            quarter = (index // 40) % 12
            rr = generator.normal(0.0, 0.03)
            pc = abs(generator.normal(0.4, 0.15))
            row = {
                'symbol': f'F{firm}',
                'year_quarter': f'201{5 + quarter // 4}Q{quarter % 4 + 1}',
                'sue': 20.0 * rr - 2.0 * pc + generator.normal(0.0, 0.3),
                'beta': generator.normal(1.0, 0.3),
                'momentum': generator.normal(0.0, 0.3),
                'size': generator.normal(12.0, 1.0),
                'bhar': generator.normal(0.0, 0.05),
            }
            for lag in (1, 2, 3):
                row[f'rr_iv_{lag}'] = (
                    rr if lag == 1 else generator.normal(0.0, 0.03)
                )
                row[f'alt_rr_iv_{lag}'] = row[
                    f'rr_iv_{lag}'
                ] + generator.normal(0.0, 0.002)
                row[f'pc_contracts_{lag}'] = (
                    pc if lag == 1 else abs(generator.normal(0.4, 0.15))
                )
                row[f'pc_value_{lag}'] = row[f'pc_contracts_{lag}']
                row[f'atm_iv_{lag}'] = generator.normal(0.4, 0.1)
                row[f'alt_atm_iv_{lag}'] = row[f'atm_iv_{lag}']
            rows.append(row)
        self.dataset = pandas.DataFrame(rows)
        self.dataset['sue_alternative'] = -self.dataset['sue']
        self.tables = regression_tables.RegressionTables(self.dataset)

    def test_day_minus_one_signs_and_significance(self) -> None:
        """Checks RR-IV is positive, P/C negative, both significant.

        Raises:
            AssertionError: If a sign or t-statistic is wrong.
        """
        result = self.tables.run_one(
            'Table 6',
            '(2)',
            1,
            'rr_iv',
            'atm_iv',
            'pc_contracts',
            True,
        ).set_index('variable')
        self.assertGreater(result.loc['RR-IV', 'coefficient'], 0.0)
        self.assertLess(result.loc['P/C', 'coefficient'], 0.0)
        self.assertGreater(result.loc['RR-IV', 't_statistic'], 3.0)
        self.assertLess(result.loc['P/C', 't_statistic'], -3.0)

    def test_later_lags_are_insignificant(self) -> None:
        """Checks days -2 and -3 carry no signal, as in the paper's Table 7.

        Raises:
            AssertionError: If a lag looks significant.
        """
        for lag in (2, 3):
            result = self.tables.run_one(
                'Table 7',
                f'n={lag}',
                lag,
                'rr_iv',
                'atm_iv',
                'pc_contracts',
                True,
            ).set_index('variable')
            self.assertLess(abs(result.loc['RR-IV', 't_statistic']), 3.0)

    def test_all_tables_has_every_column(self) -> None:
        """Checks the ten columns of Tables 6 to 9 are produced.

        Raises:
            AssertionError: If a column is missing.
        """
        table = self.tables.all_tables()
        labels = set(zip(table['table'], table['column'], strict=True))
        expected = {
            ('Table 6', '(1)'),
            ('Table 6', '(2)'),
            ('Table 8', '(1)'),
            ('Table 8', '(2)'),
            ('Table 7', 'n=2'),
            ('Table 7', 'n=3'),
            ('Table 9', 'n=2'),
            ('Table 9', 'n=3'),
        }
        self.assertEqual(labels, expected)
        self.assertEqual(len(table[table['table'] == 'Table 6']), 14)
        self.assertEqual(
            set(table['variable']),
            {
                'RR-IV',
                'P/C',
                'ATM-IV',
                'Alt RR-IV',
                'Alt ATM-IV',
                'beta',
                'momentum',
                'size',
                'bhar',
            },
        )

    def test_alternative_surprise_flips_every_coefficient(self) -> None:
        """Checks all eight columns use the alternative surprise.

        With the alternative surprise equal to minus SUE, every coefficient
        must be exactly the negative of the SUE one.

        Raises:
            AssertionError: If any column still uses SUE.
        """
        main = self.tables.all_tables().set_index(
            ['table', 'column', 'variable']
        )
        other = self.tables.all_tables('pc_contracts', 'sue_alternative')
        other = other.set_index(['table', 'column', 'variable'])
        for key in main.index:
            self.assertAlmostEqual(
                main.loc[key, 'coefficient'],
                -other.loc[key, 'coefficient'],
                places=8,
            )

    def test_descriptive_tables(self) -> None:
        """Checks Table 3 counts and Table 4 symmetry and diagonal.

        Raises:
            AssertionError: If the tables are wrong.
        """
        stats = descriptive_statistics.DescriptiveStatistics()
        summary = stats.summary(self.dataset).set_index('variable')
        self.assertEqual(summary.loc['sue', 'N'], 600)
        self.assertAlmostEqual(summary.loc['size', 'mean'], 12.0, delta=0.2)
        correlations = stats.correlations(self.dataset)
        self.assertAlmostEqual(correlations.loc['sue', 'sue'], 1.0)
        self.assertAlmostEqual(
            correlations.loc['sue', 'rr_iv_1'],
            correlations.loc['rr_iv_1', 'sue'],
        )
        self.assertGreater(correlations.loc['sue', 'rr_iv_1'], 0.5)


if __name__ == '__main__':
    unittest.main()
