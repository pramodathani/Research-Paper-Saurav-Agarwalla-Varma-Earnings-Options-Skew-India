"""Builds adjusted daily returns for the stock-futures shares."""

import json
import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    corporate_action_reader,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    adjusted_return_builder,
)


class BuildDailyReturnsApplication:
    """Command-line program that builds the daily return panel."""

    def run(self) -> None:
        """Builds the panel for 2009 to 2025 and saves it as parquet.

        Raises:
            FileNotFoundError: If a derived store is missing.
        """
        data_folder = pathlib.Path('data')
        symbols = set(
            json.loads(
                data_folder / 'derived' / 'futures_ranges.json'.read_text()
            )
        )
        pieces = []
        for year in range(2009, 2026):
            cash = pandas.read_parquet(
                data_folder / 'derived' / f'cash_{year}.parquet',
            )
            pieces.append(cash[cash['symbol'].isin(symbols)])
        cash = pandas.concat(pieces, ignore_index=True)
        actions = corporate_action_reader.CorporateActionReader().read_folder(
            data_folder / 'nse' / 'corporate_actions',
            2009,
            2026,
        )
        actions = actions[actions['symbol'].isin(symbols)]
        returns = adjusted_return_builder.AdjustedReturnBuilder().build(
            cash,
            actions,
        )
        target = data_folder / 'derived' / 'daily_returns_2009_2025.parquet'
        returns.to_parquet(target)
        print(
            'saved',
            target,
            len(returns),
            int(returns['extreme'].sum()),
            'extreme',
        )


if __name__ == '__main__':
    BuildDailyReturnsApplication().run()
