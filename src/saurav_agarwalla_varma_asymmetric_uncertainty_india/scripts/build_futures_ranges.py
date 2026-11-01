"""Builds data/derived/futures_ranges.json from the yearly F&O stores."""

import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    futures_range_builder,
)


class BuildFuturesRangesApplication:
    """Command-line program that builds the futures ranges file."""

    def run(self) -> None:
        """Builds the file for 2009 to 2025.

        Raises:
            FileNotFoundError: If a yearly store is missing.
        """
        data_folder = pathlib.Path('data')
        builder = futures_range_builder.FuturesRangeBuilder(data_folder)
        ranges = builder.build(2009, 2025)
        target = data_folder / 'derived' / 'futures_ranges.json'
        builder.save(ranges, target)
        print('saved', target, len(ranges), 'symbols')


if __name__ == '__main__':
    BuildFuturesRangesApplication().run()
