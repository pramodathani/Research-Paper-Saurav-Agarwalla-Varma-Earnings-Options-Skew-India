"""Tests for the Black (1976) pricing class."""

import math
import unittest

import numpy

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    black76,
)


class Black76Test(unittest.TestCase):
    """Checks prices, parity, deltas, bounds and implied volatility."""

    def setUp(self) -> None:
        """Creates a model without discounting.

        Raises:
            AssertionError: Never.
        """
        self.model = black76.Black76(0.0)

    def test_at_the_money_call_price(self) -> None:
        """Checks the at-the-money price against 0.4 * F * sigma * sqrt(T).

        Raises:
            AssertionError: If the price is not the known value.
        """
        price = self.model.price(100.0, 100.0, 1.0, 0.2, True)
        expected = 7.9655674554
        self.assertAlmostEqual(float(price), expected, places=4)

    def test_put_call_parity(self) -> None:
        """Checks call minus put equals forward minus strike.

        Raises:
            AssertionError: If parity fails.
        """
        call = self.model.price(105.0, 100.0, 0.25, 0.3, True)
        put = self.model.price(105.0, 100.0, 0.25, 0.3, False)
        self.assertAlmostEqual(float(call - put), 5.0, places=8)

    def test_discounting_scales_the_price(self) -> None:
        """Checks the premium is multiplied by exp(-rT).

        Raises:
            AssertionError: If the discount is wrong.
        """
        discounted = black76.Black76(0.06)
        plain = self.model.price(100.0, 95.0, 0.5, 0.25, True)
        value = discounted.price(100.0, 95.0, 0.5, 0.25, True)
        self.assertAlmostEqual(
            float(value),
            float(plain) * math.exp(-0.03),
            places=10,
        )

    def test_call_delta_is_half_at_the_money_with_tiny_variance(self) -> None:
        """Checks the delta is near one half when the forward is the strike.

        Raises:
            AssertionError: If the delta is far from 0.5.
        """
        delta = self.model.call_delta(100.0, 100.0, 0.0001, 0.2)
        self.assertAlmostEqual(float(delta), 0.5, places=3)

    def test_put_delta_converts_to_call_delta(self) -> None:
        """Checks that put delta plus one equals the call delta.

        Raises:
            AssertionError: If the conversion fails.
        """
        call_delta = float(self.model.call_delta(100.0, 110.0, 0.5, 0.3))
        eps = 1e-6
        up = float(self.model.price(100.0 + eps, 110.0, 0.5, 0.3, False))
        down = float(self.model.price(100.0 - eps, 110.0, 0.5, 0.3, False))
        put_delta = (up - down) / (2.0 * eps)
        self.assertAlmostEqual(put_delta + 1.0, call_delta, places=5)

    def test_implied_volatility_round_trip(self) -> None:
        """Checks that pricing then inverting returns the volatility.

        Raises:
            AssertionError: If the volatility is not recovered.
        """
        strikes = numpy.array([80.0, 100.0, 120.0, 100.0])
        calls = numpy.array([True, True, False, False])
        price = self.model.price(100.0, strikes, 0.1, 0.35, calls)
        recovered = self.model.implied_volatility(
            price,
            100.0,
            strikes,
            0.1,
            calls,
        )
        numpy.testing.assert_allclose(recovered, 0.35, atol=1e-6)

    def test_price_below_intrinsic_has_no_volatility(self) -> None:
        """Checks that a price below intrinsic value gives NaN.

        Raises:
            AssertionError: If a volatility is returned.
        """
        result = self.model.implied_volatility(
            numpy.array([19.0]),
            100.0,
            80.0,
            0.1,
            numpy.array([True]),
        )
        self.assertTrue(numpy.isnan(result[0]))

    def test_price_above_forward_has_no_volatility(self) -> None:
        """Checks that a call dearer than the forward gives NaN.

        Raises:
            AssertionError: If a volatility is returned.
        """
        result = self.model.implied_volatility(
            numpy.array([101.0]),
            100.0,
            80.0,
            0.1,
            numpy.array([True]),
        )
        self.assertTrue(numpy.isnan(result[0]))

    def test_zero_price_has_no_volatility(self) -> None:
        """Checks that a worthless out-of-the-money put gives NaN.

        Raises:
            AssertionError: If a volatility is returned.
        """
        result = self.model.implied_volatility(
            numpy.array([0.0]),
            100.0,
            50.0,
            0.1,
            numpy.array([False]),
        )
        self.assertTrue(numpy.isnan(result[0]))


if __name__ == '__main__':
    unittest.main()
