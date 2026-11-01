"""Builds the yearly parquet stores from the raw bhavcopy zips."""

import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    derived_store_builder,
)


class BuildDerivedStoresApplication:
    """Command-line program that builds the yearly stores."""

    def run(self) -> None:
        """Builds the F&O stores for 2009 to 2025 and cash for 2009 to 2025.

        Raises:
            FileNotFoundError: If the raw data folder is missing.
        """
        builder = derived_store_builder.DerivedStoreBuilder(
            pathlib.Path('data'),
        )
        builder.build('fno', 2009, 2025)
        builder.build('cash', 2009, 2025)


if __name__ == '__main__':
    BuildDerivedStoresApplication().run()
