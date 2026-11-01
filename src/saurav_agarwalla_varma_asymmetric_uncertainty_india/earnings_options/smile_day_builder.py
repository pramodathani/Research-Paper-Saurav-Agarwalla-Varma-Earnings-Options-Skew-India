"""Builds one stock-day's volatility smile from daily option prices."""

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    black76,
    smile_fit,
)


class SmileDayBuilder:
    """Applies the paper's filters and fits the quadratic smile."""

    MIN_CONTRACTS_PER_DAY = 7
    BUCKET_LOW = 0.95
    BUCKET_EDGE = 1.05
    BUCKET_HIGH = 1.20

    def __init__(
        self,
        min_traded_contracts: int = 5,
        price_error: bool = False,
    ) -> None:
        """Sets the liquidity filter and the fit objective.

        Args:
            min_traded_contracts: The least contracts an option must have
                traded in the day, standing in for the five-minute filter.
            price_error: Fit squared premium errors instead of squared
                implied volatility errors.
        """
        self.min_traded_contracts = min_traded_contracts
        self.price_error = price_error

    def build(
        self,
        options: pandas.DataFrame,
        forward: float,
        years: float,
        risk_free_rate: float,
    ) -> dict[str, float] | None:
        """Fits one stock-day.

        Args:
            options: The day's options of one expiry with columns strike,
                option_type (CE or PE), price, contracts and value_rupees.
            forward: The futures price of the same expiry.
            years: Time to expiry in years.
            risk_free_rate: The annual continuous rate.

        Returns:
            The smile parameters and the alternative moneyness-bucket
            measures, or None when the filters leave too few contracts.
        """
        model = black76.Black76(risk_free_rate)
        liquid = options[options['contracts'] >= self.min_traded_contracts]
        if liquid.empty or forward <= 0 or years <= 0:
            return None
        strike = liquid['strike'].to_numpy(dtype=float)
        premium = liquid['price'].to_numpy(dtype=float)
        is_call = (liquid['option_type'] == 'CE').to_numpy()
        volatility = model.implied_volatility(
            premium,
            forward,
            strike,
            years,
            is_call,
        )
        valid = ~numpy.isnan(volatility)
        if valid.sum() < self.MIN_CONTRACTS_PER_DAY:
            return None
        if is_call[valid].sum() < 1 or (~is_call[valid]).sum() < 1:
            return None
        strike = strike[valid]
        premium = premium[valid]
        is_call = is_call[valid]
        volatility = volatility[valid]
        contracts = liquid['contracts'].to_numpy(dtype=float)[valid]
        value = liquid['value_rupees'].to_numpy(dtype=float)[valid]
        delta = model.call_delta(forward, strike, years, volatility)
        weights = numpy.log(numpy.maximum(value, 3.0))
        terms = None
        if self.price_error:
            terms = {
                'forward': numpy.full(len(strike), forward),
                'strike': strike,
                'years': numpy.full(len(strike), years),
                'is_call': is_call,
                'premium': premium,
            }
        fit = smile_fit.SmileFitter(model).fit(
            delta,
            volatility,
            weights,
            price_terms=terms,
        )
        result = {
            'contracts_used': float(len(strike)),
            'calls_used': float(is_call.sum()),
            'puts_used': float((~is_call).sum()),
            'delta_min': float(delta.min()),
            'delta_max': float(delta.max()),
            'curvature': fit.curvature,
            'slope': fit.slope,
            'level': fit.level,
            'fit_error': fit.error,
            'atm_iv': fit.at_the_money,
            'iv_75': float(fit.volatility(0.75)),
            'iv_25': float(fit.volatility(0.25)),
            'rr_iv': fit.risk_reversal,
        }
        result.update(
            self.alternative(forward, strike, is_call, volatility, contracts),
        )
        return result

    def alternative(
        self,
        forward: float,
        strike: numpy.ndarray,
        is_call: numpy.ndarray,
        volatility: numpy.ndarray,
        contracts: numpy.ndarray,
    ) -> dict[str, float]:
        """Computes the Xing, Zhang and Zhao moneyness-bucket measures.

        An option is out of the money when strike / forward (call) or
        forward / strike (put) is between 1.05 and 1.20, and at the money
        when it is between 0.95 and 1.05. Each bucket's IV is weighted by
        contracts traded.

        Args:
            forward: The futures price.
            strike: Strikes of the valid contracts.
            is_call: True for calls.
            volatility: Implied volatilities.
            contracts: Contracts traded.

        Returns:
            alt_atm_iv, alt_rr_iv and the contract counts in the buckets,
            with NaN where a bucket is empty.
        """
        ratio = numpy.where(is_call, strike / forward, forward / strike)
        otm = (ratio >= self.BUCKET_EDGE) & (ratio <= self.BUCKET_HIGH)
        atm = (ratio >= self.BUCKET_LOW) & (ratio < self.BUCKET_EDGE)
        otm_call = self.weighted(volatility, contracts, otm & is_call)
        otm_put = self.weighted(volatility, contracts, otm & ~is_call)
        return {
            'alt_atm_iv': self.weighted(volatility, contracts, atm),
            'alt_rr_iv': otm_call - otm_put,
            'otm_calls': float((otm & is_call).sum()),
            'otm_puts': float((otm & ~is_call).sum()),
        }

    def weighted(
        self,
        volatility: numpy.ndarray,
        weights: numpy.ndarray,
        mask: numpy.ndarray,
    ) -> float:
        """Returns a weighted average over a mask, NaN if the mask is empty.

        Args:
            volatility: Values to average.
            weights: Weights.
            mask: Which values to include.

        Returns:
            The weighted average.
        """
        if not mask.any():
            return float('nan')
        return float(numpy.average(volatility[mask], weights=weights[mask]))
