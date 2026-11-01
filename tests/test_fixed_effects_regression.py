"""Tests for the fixed-effects regression on data with known answers."""

import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    fixed_effects_regression,
)


class FixedEffectsRegressionTest(unittest.TestCase):
    """Builds panels from y = 2 * x1 - 1 * x2 plus fixed effects."""

    def panel(self, noise: float = 0.0, seed: int = 1) -> pandas.DataFrame:
        """Builds a panel of 30 firms and 8 year-quarters.

        Args:
            noise: The standard deviation of the error term.
            seed: The random seed.

        Returns:
            One row per firm and year-quarter.
        """
        generator = numpy.random.default_rng(seed)
        rows = []
        for firm in range(30):
            firm_effect = generator.normal(0.0, 3.0)
            for quarter in range(8):
                time_effect = 0.5 * quarter
                x_one = generator.normal() + 0.3 * firm_effect
                x_two = generator.normal()
                rows.append(
                    {
                        'symbol': f'F{firm}',
                        'quarter': f'2017Q{quarter}',
                        'x1': x_one,
                        'x2': x_two,
                        'y': (
                            2.0 * x_one
                            - 1.0 * x_two
                            + firm_effect
                            + time_effect
                            + generator.normal(0.0, noise)
                        ),
                    },
                )
        return pandas.DataFrame(rows)

    def test_recovers_coefficients_without_noise(self) -> None:
        """Checks exact recovery with firm and year-quarter effects.

        Raises:
            AssertionError: If a coefficient is wrong.
        """
        result = fixed_effects_regression.FixedEffectsRegression().fit(
            self.panel(),
            'y',
            ['x1', 'x2'],
            time_column='quarter',
        )
        self.assertAlmostEqual(
            result.coefficients.loc['x1', 'coefficient'], 2.0
        )
        self.assertAlmostEqual(
            result.coefficients.loc['x2', 'coefficient'], -1.0
        )
        self.assertEqual(result.observations, 240)
        self.assertEqual(result.firms, 30)
        self.assertAlmostEqual(result.within_r2, 1.0)

    def test_firm_effects_only_leaves_the_time_trend_in_the_error(self) -> None:
        """Checks the coefficients stay near the truth without time effects.

        Raises:
            AssertionError: If the estimate is far from 2.
        """
        result = fixed_effects_regression.FixedEffectsRegression().fit(
            self.panel(noise=0.5),
            'y',
            ['x1', 'x2'],
        )
        self.assertAlmostEqual(
            result.coefficients.loc['x1', 'coefficient'],
            2.0,
            delta=0.15,
        )
        self.assertLess(result.within_r2, 1.0)

    def test_standard_errors_and_t_statistics_agree(self) -> None:
        """Checks t equals coefficient over standard error, both ways.

        Raises:
            AssertionError: If a t-statistic is inconsistent.
        """
        result = fixed_effects_regression.FixedEffectsRegression().fit(
            self.panel(noise=1.0),
            'y',
            ['x1', 'x2'],
            time_column='quarter',
        )
        table = result.coefficients
        for name in ['x1', 'x2']:
            row = table.loc[name]
            self.assertAlmostEqual(
                row['coefficient'] / row['standard_error'],
                row['t_statistic'],
            )
            self.assertAlmostEqual(
                row['coefficient'] / row['clustered_standard_error'],
                row['clustered_t_statistic'],
            )
            self.assertGreater(row['clustered_standard_error'], 0.0)

    def test_rows_with_missing_values_are_dropped(self) -> None:
        """Checks only complete rows count as observations.

        Raises:
            AssertionError: If the count is wrong.
        """
        data = self.panel(noise=0.5)
        data.loc[[0, 5, 9], 'x2'] = float('nan')
        result = fixed_effects_regression.FixedEffectsRegression().fit(
            data,
            'y',
            ['x1', 'x2'],
        )
        self.assertEqual(result.observations, 237)

    def test_unrelated_regressor_is_insignificant(self) -> None:
        """Checks a pure-noise regressor has a small t-statistic.

        Raises:
            AssertionError: If the noise regressor looks significant.
        """
        data = self.panel(noise=1.0)
        generator = numpy.random.default_rng(99)
        data['noise'] = generator.normal(size=len(data))
        result = fixed_effects_regression.FixedEffectsRegression().fit(
            data,
            'y',
            ['x1', 'noise'],
            time_column='quarter',
        )
        self.assertLess(
            abs(result.coefficients.loc['noise', 't_statistic']), 3.0
        )


if __name__ == '__main__':
    unittest.main()
