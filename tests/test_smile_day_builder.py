"""Tests for the one-stock-day smile builder on a made-up option chain."""

import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    black76,
    smile_day_builder,
)


class SmileDayBuilderTest(unittest.TestCase):
    """Builds chains from a known smile and checks filters and measures."""

    FORWARD = 100.0
    YEARS = 30.0 / 365.0

    def chain(self, contracts: int = 50) -> pandas.DataFrame:
        """Builds a chain priced from a downward-sloping smile.

        Args:
            contracts: Contracts traded in every option.

        Returns:
            Puts below the forward and calls above it, with columns strike,
            option_type, price, contracts and value_rupees.
        """
        model = black76.Black76(0.0)
        strikes = numpy.arange(80.0, 120.1, 2.5)
        moneyness = strikes / self.FORWARD - 1.0
        volatility = 0.30 - 0.20 * moneyness + 0.5 * moneyness**2
        is_call = strikes >= self.FORWARD
        price = model.price(
            self.FORWARD,
            strikes,
            self.YEARS,
            volatility,
            is_call,
        )
        return pandas.DataFrame(
            {
                'strike': strikes,
                'option_type': numpy.where(is_call, 'CE', 'PE'),
                'price': price,
                'contracts': contracts,
                'value_rupees': contracts * 500.0 * (strikes + price),
            },
        )

    def build(self, options: pandas.DataFrame, **settings) -> dict | None:
        """Runs the builder with a zero rate.

        Args:
            options: The day's chain.
            **settings: Settings for the builder.

        Returns:
            The builder's result.
        """
        builder = smile_day_builder.SmileDayBuilder(**settings)
        return builder.build(options, self.FORWARD, self.YEARS, 0.0)

    def test_recovers_level_and_negative_skew(self) -> None:
        """Checks ATM-IV is near 0.30 and RR-IV is negative.

        Raises:
            AssertionError: If the smile is not recovered.
        """
        result = self.build(self.chain())
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['atm_iv'], 0.30, delta=0.01)
        self.assertLess(result['rr_iv'], -0.01)
        self.assertGreater(result['iv_75'], result['iv_25'])

    def test_flat_smile_has_no_skew(self) -> None:
        """Checks a flat 25 percent smile gives RR-IV near zero.

        Raises:
            AssertionError: If skew is found in a flat smile.
        """
        options = self.chain()
        model = black76.Black76(0.0)
        options['price'] = model.price(
            self.FORWARD,
            options['strike'].to_numpy(),
            self.YEARS,
            0.25,
            (options['option_type'] == 'CE').to_numpy(),
        )
        result = self.build(options)
        self.assertAlmostEqual(result['atm_iv'], 0.25, places=3)
        self.assertAlmostEqual(result['rr_iv'], 0.0, places=3)

    def test_liquidity_filter_drops_thin_contracts(self) -> None:
        """Checks a chain below the contracts filter gives no smile.

        Raises:
            AssertionError: If a smile is returned.
        """
        self.assertIsNone(self.build(self.chain(contracts=4)))
        self.assertIsNotNone(
            self.build(self.chain(contracts=4), min_traded_contracts=1)
        )

    def test_fewer_than_seven_contracts_gives_none(self) -> None:
        """Checks six valid contracts are refused and seven accepted.

        Raises:
            AssertionError: If the count rule is wrong.
        """
        options = self.chain()
        self.assertIsNone(self.build(options.iloc[[0, 2, 4, 9, 11, 14]]))
        self.assertIsNotNone(self.build(options.iloc[[0, 2, 4, 9, 11, 14, 16]]))

    def test_needs_a_call_and_a_put(self) -> None:
        """Checks a chain of only calls is refused.

        Raises:
            AssertionError: If a smile is returned.
        """
        options = self.chain()
        calls = options[options['option_type'] == 'CE']
        self.assertGreaterEqual(len(calls), 7)
        self.assertIsNone(self.build(calls))

    def test_arbitrage_violating_price_is_dropped(self) -> None:
        """Checks a call priced below intrinsic value is removed.

        Raises:
            AssertionError: If the bad contract is kept.
        """
        options = self.chain()
        clean = self.build(options)
        broken = options.copy()
        broken.loc[broken['strike'] == 100.0, 'price'] = -1.0
        result = self.build(broken)
        self.assertEqual(
            result['contracts_used'],
            clean['contracts_used'] - 1.0,
        )

    def test_alternative_buckets(self) -> None:
        """Checks the moneyness buckets pick the right strikes.

        With a forward of 100, out-of-the-money puts have strikes of 83.4
        to 95.2, which here are 85 to 95, and out-of-the-money calls have
        strikes of 105 to 120. The at-the-money bucket holds the calls at
        100 and 102.5 and the put at 97.5.

        Raises:
            AssertionError: If a bucket count is wrong.
        """
        result = self.build(self.chain())
        self.assertEqual(result['otm_puts'], 5.0)
        self.assertEqual(result['otm_calls'], 7.0)
        self.assertTrue(numpy.isfinite(result['alt_atm_iv']))
        self.assertLess(result['alt_rr_iv'], 0.0)

    def test_empty_bucket_gives_nan(self) -> None:
        """Checks a chain with no strikes above 104 has no alternative RR.

        Raises:
            AssertionError: If a number is returned.
        """
        options = self.chain()
        options = options[options['strike'] < 105.0]
        result = self.build(options)
        self.assertEqual(result['otm_calls'], 0.0)
        self.assertTrue(numpy.isnan(result['alt_rr_iv']))

    def test_price_error_objective_runs(self) -> None:
        """Checks the premium-error fit gives a similar smile.

        Raises:
            AssertionError: If the two fits disagree a lot.
        """
        main = self.build(self.chain())
        other = self.build(self.chain(), price_error=True)
        self.assertAlmostEqual(main['atm_iv'], other['atm_iv'], delta=0.02)


if __name__ == '__main__':
    unittest.main()
