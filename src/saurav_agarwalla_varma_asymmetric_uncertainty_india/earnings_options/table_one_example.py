"""Recomputes the paper's Table 1: a skewed surprise tilts the smile."""

import dataclasses

import numpy

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    black76,
)


@dataclasses.dataclass
class TableOneColumn:
    """One scenario of Table 1.

    Attributes:
        name: The scenario's name.
        spot: The mixture's mean, which is the spot price.
        strikes: The in, at and out of the money strikes.
        premiums: The premiums at those strikes.
        volatilities: The implied volatilities at those strikes.
        risk_reversal: Out of the money IV minus in the money IV, in points.
    """

    name: str
    spot: float
    strikes: tuple[float, float, float]
    premiums: tuple[float, float, float]
    volatilities: tuple[float, float, float]
    risk_reversal: float


class TableOneExample:
    """Builds the three columns of Table 1 on page 465."""

    MEANS = (100.0, 110.0, 90.0)
    COMPONENT_VOLATILITY = 0.25
    WEEKS_PER_YEAR = 52

    def __init__(self) -> None:
        """Creates the pricing model with zero rates, as the paper does."""
        self.model = black76.Black76(0.0)
        self.years = 1.0 / self.WEEKS_PER_YEAR

    def mixture_price(
        self,
        strike: float,
        weights: tuple[float, float, float],
    ) -> float:
        """Prices a call as the weighted price on the three components.

        Args:
            strike: The strike price.
            weights: The weights of the three lognormal components.

        Returns:
            The call premium.
        """
        total = 0.0
        for weight, mean in zip(weights, self.MEANS, strict=True):
            price = self.model.price(
                mean,
                strike,
                self.years,
                self.COMPONENT_VOLATILITY,
                True,
            )
            total += weight * float(price)
        return total

    def implied_volatility(
        self,
        spot: float,
        strike: float,
        weights: tuple[float, float, float],
    ) -> float:
        """Inverts the mixture premium at a strike with the spot as forward.

        Args:
            spot: The mixture's mean.
            strike: The strike price.
            weights: The weights of the three components.

        Returns:
            The implied volatility.
        """
        premium = self.mixture_price(strike, weights)
        result = self.model.implied_volatility(
            numpy.array([premium]),
            spot,
            strike,
            self.years,
            numpy.array([True]),
        )
        return float(result[0])

    def column(
        self,
        name: str,
        weights: tuple[float, float, float],
    ) -> TableOneColumn:
        """Computes one scenario.

        Args:
            name: The scenario's name.
            weights: The weights of the three components.

        Returns:
            The scenario's strikes, premiums and implied volatilities.
        """
        spot = sum(
            weight * mean
            for weight, mean in zip(weights, self.MEANS, strict=True)
        )
        at_volatility = self.implied_volatility(spot, spot, weights)
        step = at_volatility / self.WEEKS_PER_YEAR
        strikes = (spot / (1.0 + step), spot, spot * (1.0 + step))
        premiums = tuple(
            self.mixture_price(strike, weights) for strike in strikes
        )
        volatilities = tuple(
            self.implied_volatility(spot, strike, weights) for strike in strikes
        )
        return TableOneColumn(
            name=name,
            spot=spot,
            strikes=strikes,
            premiums=premiums,
            volatilities=volatilities,
            risk_reversal=100.0 * (volatilities[2] - volatilities[0]),
        )

    def build(self) -> list[TableOneColumn]:
        """Computes the three scenarios of the paper.

        Returns:
            The no-surprise, positive-surprise and negative-surprise columns.
        """
        return [
            self.column('No surprise', (1.0, 0.0, 0.0)),
            self.column('10% chance of +10%', (0.9, 0.1, 0.0)),
            self.column('10% chance of -10%', (0.9, 0.0, 0.1)),
        ]
