"""Fits the paper's quadratic volatility smile IV = a*D^2 + b*D + c."""

import dataclasses

import numpy
from scipy import optimize

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    black76,
)


@dataclasses.dataclass
class SmileFit:
    """A fitted smile on call delta between 0 and 1.

    Attributes:
        curvature: The coefficient a, never negative.
        slope: The coefficient b.
        level: The coefficient c after the paper's shift, never negative.
        error: The weighted sum of squared errors at the optimum.
    """

    curvature: float
    slope: float
    level: float
    error: float

    def volatility(self, delta: float | numpy.ndarray) -> numpy.ndarray:
        """Evaluates the smile at one or more call deltas.

        Args:
            delta: Call deltas between 0 and 1.

        Returns:
            The fitted implied volatilities.
        """
        delta = numpy.asarray(delta, dtype=float)
        return self.curvature * delta**2 + self.slope * delta + self.level

    @property
    def at_the_money(self) -> float:
        """The implied volatility at call delta 0.5.

        Returns:
            ATM-IV.
        """
        return float(self.volatility(0.5))

    @property
    def risk_reversal(self) -> float:
        """The IV at delta 0.25 minus the IV at delta 0.75.

        Returns:
            RR-IV.
        """
        return float(self.volatility(0.25) - self.volatility(0.75))


class SmileFitter:
    """Fits one stock-day's smile with the paper's constraints."""

    def __init__(self, model: black76.Black76 | None = None) -> None:
        """Stores the pricing model used by the price-error objective.

        Args:
            model: The Black model, or None for a zero-rate model.
        """
        self.model = model or black76.Black76(0.0)

    def effective_level(
        self,
        curvature: float,
        slope: float,
        level: float,
    ) -> float:
        """Adds the paper's shift so the smile stays above zero on [0, 1].

        The raw level is shifted up by b^2 / 4a when the vertex -b / 2a lies
        in [0, 1], and otherwise by the amount that keeps the IV at delta 1
        from going below zero, which is the paper's min(0, a + b) term.

        Args:
            curvature: The coefficient a, at least zero.
            slope: The coefficient b.
            level: The raw level, at least zero.

        Returns:
            The level c used in the smile.
        """
        if curvature > 1e-12:
            vertex = -slope / (2.0 * curvature)
            if 0.0 <= vertex <= 1.0:
                return level + slope * slope / (4.0 * curvature)
        return level - min(0.0, curvature + slope)

    def starting_point(
        self,
        delta: numpy.ndarray,
        volatility: numpy.ndarray,
        weights: numpy.ndarray,
    ) -> numpy.ndarray:
        """Starts from a weighted least squares quadratic.

        Args:
            delta: Call deltas.
            volatility: Observed implied volatilities.
            weights: Weights for each observation.

        Returns:
            The raw parameters a, b and c, with a and c clipped at zero.
        """
        design = numpy.column_stack([delta**2, delta, numpy.ones_like(delta)])
        root = numpy.sqrt(weights)
        solution, *_ = numpy.linalg.lstsq(
            design * root[:, None],
            volatility * root,
            rcond=None,
        )
        return numpy.array(
            [max(solution[0], 0.0), solution[1], max(solution[2], 0.0)]
        )

    def fit(
        self,
        delta: numpy.ndarray,
        volatility: numpy.ndarray,
        weights: numpy.ndarray,
        price_terms: dict[str, numpy.ndarray] | None = None,
    ) -> SmileFit:
        """Fits a, b and c by Nelder-Mead on weighted squared errors.

        Args:
            delta: Call deltas of the contracts, between 0 and 1.
            volatility: Observed implied volatilities.
            weights: Weights, the log of traded value in the paper.
            price_terms: If given, errors are in premium and not in IV. It
                holds forward, strike, years, is_call and premium arrays.

        Returns:
            The fitted smile.

        Raises:
            ValueError: If fewer than three contracts are given.
        """
        delta = numpy.asarray(delta, dtype=float)
        volatility = numpy.asarray(volatility, dtype=float)
        weights = numpy.asarray(weights, dtype=float)
        if len(delta) < 3:
            raise ValueError('A smile needs at least three contracts.')

        def objective(raw: numpy.ndarray) -> float:
            """Returns the weighted squared error for raw parameters.

            Args:
                raw: The raw a, b and c.

            Returns:
                The weighted sum of squared errors.
            """
            curvature = abs(raw[0])
            level = self.effective_level(curvature, raw[1], abs(raw[2]))
            fitted = curvature * delta**2 + raw[1] * delta + level
            if price_terms is None:
                residual = fitted - volatility
            else:
                fitted = numpy.maximum(fitted, 1e-4)
                model_price = self.model.price(
                    price_terms['forward'],
                    price_terms['strike'],
                    price_terms['years'],
                    fitted,
                    price_terms['is_call'],
                )
                residual = model_price - price_terms['premium']
            return float(numpy.sum(weights * residual * residual))

        start = self.starting_point(delta, volatility, weights)
        result = optimize.minimize(
            objective,
            start,
            method='Nelder-Mead',
            options={'xatol': 1e-8, 'fatol': 1e-14, 'maxiter': 4000},
        )
        curvature = abs(result.x[0])
        level = self.effective_level(curvature, result.x[1], abs(result.x[2]))
        return SmileFit(
            curvature=float(curvature),
            slope=float(result.x[1]),
            level=float(level),
            error=float(result.fun),
        )
