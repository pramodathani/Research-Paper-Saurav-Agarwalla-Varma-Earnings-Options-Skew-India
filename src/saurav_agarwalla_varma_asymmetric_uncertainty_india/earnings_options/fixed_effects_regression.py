"""OLS with firm and year-quarter fixed effects, as in equation 5."""

import dataclasses

import pandas
import statsmodels.api as sm


@dataclasses.dataclass
class RegressionResult:
    """The result of one fixed-effects regression.

    Attributes:
        coefficients: A table indexed by regressor with coefficient,
            classical standard error and t-statistic, and the firm-clustered
            standard error and t-statistic.
        observations: The number of events used.
        adjusted_r2: The adjusted R-squared of the model with all dummies.
        within_r2: The share of variance left after removing the fixed
            effects that the regressors explain.
        firms: The number of firms.
    """

    coefficients: pandas.DataFrame
    observations: int
    adjusted_r2: float
    within_r2: float
    firms: int


class FixedEffectsRegression:
    """Fits a regression with dummy variables for the fixed effects."""

    def fit(
        self,
        data: pandas.DataFrame,
        dependent: str,
        regressors: list[str],
        firm_column: str = 'symbol',
        time_column: str | None = None,
    ) -> RegressionResult:
        """Fits one regression on the rows with no missing values.

        Args:
            data: One row per event.
            dependent: The dependent variable's column.
            regressors: The regressors' columns.
            firm_column: The column holding the firm for the firm effect and
                for clustering the standard errors.
            time_column: The column holding the year-quarter for the time
                effect, or None for firm effects only.

        Returns:
            The coefficients, standard errors, R-squared values and counts.
        """
        columns = [dependent, *regressors, firm_column]
        if time_column is not None:
            columns.append(time_column)
        sample = data[columns].dropna().reset_index(drop=True)
        effects = pandas.get_dummies(
            sample[firm_column],
            prefix='firm',
            drop_first=True,
            dtype=float,
        )
        if time_column is not None:
            time = pandas.get_dummies(
                sample[time_column].astype(str),
                prefix='time',
                drop_first=True,
                dtype=float,
            )
            effects = pandas.concat([effects, time], axis=1)
        design = pandas.concat([sample[regressors], effects], axis=1)
        design = sm.add_constant(design, has_constant='add')
        outcome = sample[dependent]
        model = sm.OLS(outcome, design)
        classical = model.fit()
        groups = pandas.factorize(sample[firm_column])[0]
        clustered = model.fit(cov_type='cluster', cov_kwds={'groups': groups})
        only_effects = sm.OLS(
            outcome,
            sm.add_constant(effects, has_constant='add'),
        ).fit()
        table = pandas.DataFrame(
            {
                'coefficient': classical.params[regressors],
                'standard_error': classical.bse[regressors],
                't_statistic': classical.tvalues[regressors],
                'clustered_standard_error': clustered.bse[regressors],
                'clustered_t_statistic': clustered.tvalues[regressors],
            },
        )
        within = 1.0 - classical.ssr / only_effects.ssr
        return RegressionResult(
            coefficients=table,
            observations=int(classical.nobs),
            adjusted_r2=float(classical.rsquared_adj),
            within_r2=float(within),
            firms=int(sample[firm_column].nunique()),
        )
