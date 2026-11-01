"""Tables 6 to 9: equation 5 at n = 1, 2 and 3, with SUE as the surprise."""

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    fixed_effects_regression,
    winsoriser,
)


class RegressionTables:
    """Runs the paper's regressions on the event-level dataset."""

    CONTROLS = ('beta', 'momentum', 'size', 'bhar')

    def __init__(self, dataset: pandas.DataFrame) -> None:
        """Winsorises the dataset at the 5th and 95th percentiles.

        Args:
            dataset: One row per event from RegressionDatasetBuilder.
        """
        columns = [
            name
            for name in dataset.columns
            if name not in ('symbol', 'day0', 'year_quarter')
        ]
        self.dataset = winsoriser.Winsoriser().apply(dataset, columns)
        self.regression = fixed_effects_regression.FixedEffectsRegression()

    def run_one(
        self,
        table: str,
        column: str,
        lag: int,
        skew: str,
        level: str,
        ratio: str,
        with_time_effect: bool,
        surprise: str = 'sue',
    ) -> pandas.DataFrame:
        """Runs one column of one table.

        Args:
            table: The table's label.
            column: The column's label.
            lag: n, the days before the announcement.
            skew: The skew variable's base name, rr_iv or alt_rr_iv.
            level: The level variable's base name, atm_iv or alt_atm_iv.
            ratio: The put-to-call variable's base name.
            with_time_effect: Whether to add year-quarter effects.
            surprise: The dependent variable.

        Returns:
            A tidy table with one row per coefficient, plus the sample size
            and R-squared values repeated on each row.
        """
        names = {
            f'{skew}_{lag}': 'RR-IV' if skew == 'rr_iv' else 'Alt RR-IV',
            f'{ratio}_{lag}': 'P/C',
            f'{level}_{lag}': 'ATM-IV' if level == 'atm_iv' else 'Alt ATM-IV',
        }
        regressors = list(names) + list(self.CONTROLS)
        result = self.regression.fit(
            self.dataset,
            surprise,
            regressors,
            time_column='year_quarter' if with_time_effect else None,
        )
        table_frame = result.coefficients.reset_index(names='variable')
        table_frame['variable'] = table_frame['variable'].map(
            lambda name: names.get(name, name),
        )
        table_frame.insert(0, 'column', column)
        table_frame.insert(0, 'table', table)
        table_frame['observations'] = result.observations
        table_frame['firms'] = result.firms
        table_frame['adjusted_r2'] = result.adjusted_r2
        table_frame['within_r2'] = result.within_r2
        table_frame['lag'] = lag
        return table_frame

    def all_tables(
        self,
        ratio: str = 'pc_contracts',
        surprise: str = 'sue',
    ) -> pandas.DataFrame:
        """Runs the SUE columns of Tables 6 to 9.

        Table 6 and Table 8 use n = 1 with and without year-quarter effects.
        Tables 7 and 9 use n = 2 and 3 with both effects.

        Args:
            ratio: The put-to-call variable, pc_contracts or pc_value.
            surprise: The dependent variable, sue or sue_alternative.

        Returns:
            One tidy table for all columns.
        """
        pieces = []
        for lag in (1,):
            for effect in (False, True):
                label = '(2)' if effect else '(1)'
                pieces.append(
                    self.run_one(
                        'Table 6',
                        label,
                        lag,
                        'rr_iv',
                        'atm_iv',
                        ratio,
                        effect,
                        surprise,
                    ),
                )
                pieces.append(
                    self.run_one(
                        'Table 8',
                        label,
                        lag,
                        'alt_rr_iv',
                        'alt_atm_iv',
                        ratio,
                        effect,
                        surprise,
                    ),
                )
        for lag, label in [(2, 'n=2'), (3, 'n=3')]:
            pieces.append(
                self.run_one(
                    'Table 7',
                    label,
                    lag,
                    'rr_iv',
                    'atm_iv',
                    ratio,
                    True,
                    surprise,
                ),
            )
            pieces.append(
                self.run_one(
                    'Table 9',
                    label,
                    lag,
                    'alt_rr_iv',
                    'alt_atm_iv',
                    ratio,
                    True,
                    surprise,
                ),
            )
        return pandas.concat(pieces, ignore_index=True)
