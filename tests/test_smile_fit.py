"""Tests for the quadratic smile fit."""

import unittest

import numpy

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    black76,
    smile_fit,
)


class SmileFitTest(unittest.TestCase):
    """Fits made-up smiles whose coefficients are known."""

    def setUp(self) -> None:
        """Creates a fitter and a grid of deltas.

        Raises:
            AssertionError: Never.
        """
        self.fitter = smile_fit.SmileFitter()
        self.delta = numpy.linspace(0.1, 0.9, 9)
        self.weights = numpy.ones(9)

    def test_recovers_known_coefficients(self) -> None:
        """Checks that a noiseless smile is recovered.

        Raises:
            AssertionError: If the coefficients are not recovered.
        """
        volatility = 0.30 - 0.10 * self.delta + 0.20 * self.delta**2
        fit = self.fitter.fit(self.delta, volatility, self.weights)
        self.assertAlmostEqual(fit.curvature, 0.20, places=4)
        self.assertAlmostEqual(fit.slope, -0.10, places=4)
        self.assertAlmostEqual(fit.level, 0.30, places=4)

    def test_risk_reversal_and_at_the_money(self) -> None:
        """Checks ATM-IV and RR-IV against hand calculations.

        Raises:
            AssertionError: If a parameter differs from the hand value.
        """
        volatility = 0.30 - 0.10 * self.delta + 0.20 * self.delta**2
        fit = self.fitter.fit(self.delta, volatility, self.weights)
        self.assertAlmostEqual(fit.at_the_money, 0.30 - 0.05 + 0.05, places=4)
        expected = (0.30 - 0.025 + 0.20 * 0.0625) - (
            0.30 - 0.075 + 0.20 * 0.5625
        )
        self.assertAlmostEqual(fit.risk_reversal, expected, places=4)

    def test_curvature_is_never_negative(self) -> None:
        """Checks that a frowning cloud gives a curvature of zero or more.

        Raises:
            AssertionError: If the curvature is negative.
        """
        volatility = 0.40 + 0.30 * self.delta - 0.50 * self.delta**2
        fit = self.fitter.fit(self.delta, volatility, self.weights)
        self.assertGreaterEqual(fit.curvature, 0.0)

    def test_smile_stays_positive_on_zero_to_one(self) -> None:
        """Checks the fitted IV is not negative anywhere on the delta range.

        Raises:
            AssertionError: If the fit goes below zero.
        """
        volatility = numpy.array(
            [0.02, 0.03, 0.05, 0.08, 0.13, 0.2, 0.3, 0.42, 0.56],
        )
        fit = self.fitter.fit(self.delta, volatility, self.weights)
        grid = numpy.linspace(0.0, 1.0, 101)
        self.assertGreaterEqual(float(fit.volatility(grid).min()), -1e-9)

    def test_weights_pull_the_fit_to_heavy_points(self) -> None:
        """Checks a heavily weighted outlier moves the fit towards itself.

        Raises:
            AssertionError: If the heavy weight has no effect.
        """
        volatility = 0.30 - 0.10 * self.delta + 0.20 * self.delta**2
        volatility[4] += 0.20
        light = self.fitter.fit(self.delta, volatility, self.weights)
        heavy_weights = self.weights.copy()
        heavy_weights[4] = 100.0
        heavy = self.fitter.fit(self.delta, volatility, heavy_weights)
        self.assertGreater(heavy.at_the_money, light.at_the_money)

    def test_too_few_contracts_raises(self) -> None:
        """Checks that two contracts are refused.

        Raises:
            AssertionError: If no error is raised.
        """
        with self.assertRaises(ValueError):
            self.fitter.fit(
                numpy.array([0.4, 0.6]), numpy.array([0.3, 0.3]), numpy.ones(2)
            )

    def test_price_objective_recovers_smile(self) -> None:
        """Checks the price-error fit recovers a smile from option premiums.

        Raises:
            AssertionError: If the fit is far from the truth.
        """
        model = black76.Black76(0.0)
        strikes = numpy.linspace(85.0, 115.0, 9)
        is_call = strikes >= 100.0
        true_volatility = 0.30 + 0.15 * (strikes / 100.0 - 1.0) ** 2
        premium = model.price(100.0, strikes, 0.1, true_volatility, is_call)
        delta = model.call_delta(100.0, strikes, 0.1, true_volatility)
        terms = {
            'forward': numpy.full(9, 100.0),
            'strike': strikes,
            'years': numpy.full(9, 0.1),
            'is_call': is_call,
            'premium': premium,
        }
        fit = self.fitter.fit(
            delta,
            true_volatility,
            numpy.ones(9),
            price_terms=terms,
        )
        fitted = fit.volatility(delta)
        numpy.testing.assert_allclose(fitted, true_volatility, atol=0.01)


if __name__ == '__main__':
    unittest.main()
