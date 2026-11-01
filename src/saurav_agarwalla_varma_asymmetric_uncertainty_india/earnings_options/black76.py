"""Black (1976) option prices, call deltas and implied volatility."""

import numpy
from scipy import stats


class Black76:
    """Prices European options on a forward and inverts prices to IV."""

    LOWEST_VOLATILITY = 1e-4
    HIGHEST_VOLATILITY = 5.0
    BISECTION_STEPS = 60

    def __init__(self, risk_free_rate: float = 0.0) -> None:
        """Stores the continuously compounded risk-free rate.

        Args:
            risk_free_rate: The annual rate used to discount the premium.
        """
        self.risk_free_rate = risk_free_rate

    def discount(self, years: numpy.ndarray) -> numpy.ndarray:
        """Returns the discount factor for each time to expiry.

        Args:
            years: Times to expiry in years.

        Returns:
            exp(-rate * years) for each time.
        """
        return numpy.exp(-self.risk_free_rate * years)

    def d_one(
        self,
        forward: numpy.ndarray,
        strike: numpy.ndarray,
        years: numpy.ndarray,
        volatility: numpy.ndarray,
    ) -> numpy.ndarray:
        """Computes d1 of the Black formula.

        Args:
            forward: Forward prices.
            strike: Strike prices.
            years: Times to expiry in years.
            volatility: Annual volatilities.

        Returns:
            d1 for each contract.
        """
        spread = volatility * numpy.sqrt(years)
        return (numpy.log(forward / strike) + 0.5 * spread * spread) / spread

    def price(
        self,
        forward: numpy.ndarray,
        strike: numpy.ndarray,
        years: numpy.ndarray,
        volatility: numpy.ndarray,
        is_call: numpy.ndarray,
    ) -> numpy.ndarray:
        """Prices calls and puts on a forward.

        Args:
            forward: Forward prices.
            strike: Strike prices.
            years: Times to expiry in years.
            volatility: Annual volatilities.
            is_call: True for a call and False for a put.

        Returns:
            The option premiums.
        """
        forward = numpy.asarray(forward, dtype=float)
        strike = numpy.asarray(strike, dtype=float)
        years = numpy.asarray(years, dtype=float)
        volatility = numpy.asarray(volatility, dtype=float)
        is_call = numpy.asarray(is_call, dtype=bool)
        d_one = self.d_one(forward, strike, years, volatility)
        d_two = d_one - volatility * numpy.sqrt(years)
        call = forward * stats.norm.cdf(d_one) - strike * stats.norm.cdf(d_two)
        put = call - forward + strike
        return self.discount(years) * numpy.where(is_call, call, put)

    def call_delta(
        self,
        forward: numpy.ndarray,
        strike: numpy.ndarray,
        years: numpy.ndarray,
        volatility: numpy.ndarray,
    ) -> numpy.ndarray:
        """Returns the call delta, which is also a put's delta plus one.

        Args:
            forward: Forward prices.
            strike: Strike prices.
            years: Times to expiry in years.
            volatility: Annual volatilities.

        Returns:
            N(d1) for each contract, without the discount factor.
        """
        d_one = self.d_one(
            numpy.asarray(forward, dtype=float),
            numpy.asarray(strike, dtype=float),
            numpy.asarray(years, dtype=float),
            numpy.asarray(volatility, dtype=float),
        )
        return stats.norm.cdf(d_one)

    def inside_bounds(
        self,
        premium: numpy.ndarray,
        forward: numpy.ndarray,
        strike: numpy.ndarray,
        years: numpy.ndarray,
        is_call: numpy.ndarray,
    ) -> numpy.ndarray:
        """Says whether each premium lies strictly inside Black's bounds.

        Args:
            premium: Observed option premiums.
            forward: Forward prices.
            strike: Strike prices.
            years: Times to expiry in years.
            is_call: True for a call and False for a put.

        Returns:
            True where the premium has a volatility that reproduces it.
        """
        premium = numpy.asarray(premium, dtype=float)
        forward = numpy.asarray(forward, dtype=float)
        strike = numpy.asarray(strike, dtype=float)
        years = numpy.asarray(years, dtype=float)
        is_call = numpy.asarray(is_call, dtype=bool)
        discount = self.discount(years)
        call_floor = numpy.maximum(forward - strike, 0.0)
        put_floor = numpy.maximum(strike - forward, 0.0)
        floor = discount * numpy.where(is_call, call_floor, put_floor)
        cap = discount * numpy.where(is_call, forward, strike)
        return (premium > floor) & (premium < cap)

    def implied_volatility(
        self,
        premium: numpy.ndarray,
        forward: numpy.ndarray,
        strike: numpy.ndarray,
        years: numpy.ndarray,
        is_call: numpy.ndarray,
    ) -> numpy.ndarray:
        """Inverts premiums to volatilities by bisection.

        Args:
            premium: Observed option premiums.
            forward: Forward prices.
            strike: Strike prices.
            years: Times to expiry in years.
            is_call: True for a call and False for a put.

        Returns:
            The implied volatilities, NaN where the premium is outside
            Black's bounds or the price cannot be matched.
        """
        premium = numpy.asarray(premium, dtype=float)
        forward = numpy.asarray(forward, dtype=float)
        strike = numpy.asarray(strike, dtype=float)
        years = numpy.asarray(years, dtype=float)
        is_call = numpy.asarray(is_call, dtype=bool)
        low = numpy.full(premium.shape, self.LOWEST_VOLATILITY)
        high = numpy.full(premium.shape, self.HIGHEST_VOLATILITY)
        for _ in range(self.BISECTION_STEPS):
            middle = 0.5 * (low + high)
            value = self.price(forward, strike, years, middle, is_call)
            too_high = value > premium
            high = numpy.where(too_high, middle, high)
            low = numpy.where(too_high, low, middle)
        result = 0.5 * (low + high)
        valid = self.inside_bounds(premium, forward, strike, years, is_call)
        edge = (result <= self.LOWEST_VOLATILITY * 1.01) | (
            result >= self.HIGHEST_VOLATILITY * 0.99
        )
        return numpy.where(valid & ~edge, result, numpy.nan)
