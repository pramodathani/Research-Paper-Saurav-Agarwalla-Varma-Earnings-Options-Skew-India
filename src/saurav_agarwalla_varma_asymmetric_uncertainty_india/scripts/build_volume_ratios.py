"""Builds the daily O/S, O/F and P/C table for 2014 to 2025."""

import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    volume_ratio_builder,
)


class BuildVolumeRatiosApplication:
    """Command-line program that builds the volume ratio table."""

    def run(self) -> None:
        """Builds the table and saves it as parquet.

        Raises:
            FileNotFoundError: If the yearly stores are missing.
        """
        data_folder = pathlib.Path('data')
        table = volume_ratio_builder.VolumeRatioBuilder().build(
            data_folder,
            2014,
            2025,
        )
        target = data_folder / 'derived' / 'volume_ratios_2014_2025.parquet'
        table.to_parquet(target)
        print('saved', target, len(table))


if __name__ == '__main__':
    BuildVolumeRatiosApplication().run()
