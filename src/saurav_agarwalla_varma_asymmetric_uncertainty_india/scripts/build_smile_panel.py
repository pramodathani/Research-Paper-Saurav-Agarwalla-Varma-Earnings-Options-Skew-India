"""Builds the stock-day smile panel for a range of years and settings."""

import argparse
import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    smile_panel_builder,
)


class BuildSmilePanelApplication:
    """Command-line program that builds one smile panel."""

    def run(self) -> None:
        """Parses the arguments, builds the panel and saves it.

        Raises:
            SystemExit: If the arguments are wrong.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--first-year', type=int, default=2015)
        parser.add_argument('--last-year', type=int, default=2019)
        parser.add_argument('--min-contracts', type=int, default=5)
        parser.add_argument('--price-field', default='close')
        parser.add_argument('--price-error', action='store_true')
        parser.add_argument('--name', default='main')
        arguments = parser.parse_args()
        builder = smile_panel_builder.SmilePanelBuilder(
            pathlib.Path('data'),
            arguments.min_contracts,
            arguments.price_field,
            arguments.price_error,
        )
        panel = builder.build(arguments.first_year, arguments.last_year)
        target = (
            pathlib.Path('data')
            / 'derived'
            / (
                f'smile_{arguments.name}_{arguments.first_year}_'
                f'{arguments.last_year}.parquet'
            )
        )
        panel.to_parquet(target)
        print('saved', target, len(panel))


if __name__ == '__main__':
    BuildSmilePanelApplication().run()
