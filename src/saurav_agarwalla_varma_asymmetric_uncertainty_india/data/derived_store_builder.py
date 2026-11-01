"""Converts the raw bhavcopy zips into one parquet file per year."""

import concurrent.futures
import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    cash_bhavcopy_reader,
    fno_bhavcopy_reader,
)


class DerivedStoreBuilder:
    """Builds data/derived/fno_YYYY.parquet and cash_YYYY.parquet."""

    def __init__(self, data_folder: pathlib.Path, workers: int = 4) -> None:
        """Remembers the data folder and the number of processes.

        Args:
            data_folder: The study's data folder.
            workers: How many files are read at the same time.
        """
        self.data_folder = data_folder
        self.workers = workers
        self.output_folder = data_folder / 'derived'
        self.output_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def read_fno(path: pathlib.Path) -> pandas.DataFrame:
        """Reads one F&O zip in a worker process.

        Args:
            path: The zip file.

        Returns:
            The normalised rows.
        """
        return fno_bhavcopy_reader.FnoBhavcopyReader().read(path)

    @staticmethod
    def read_cash(path: pathlib.Path) -> pandas.DataFrame:
        """Reads one cash zip in a worker process.

        Args:
            path: The zip file.

        Returns:
            The normalised rows.
        """
        return cash_bhavcopy_reader.CashBhavcopyReader().read(path)

    def year_of(self, path: pathlib.Path) -> int:
        """Returns the trading year of a bhavcopy zip.

        Args:
            path: A bhavcopy zip of either format.

        Returns:
            The year.
        """
        name = path.name
        if name.startswith(('fo', 'cm')):
            return int(name[7:11])
        return int(name.split('_')[-3][:4])

    def build(
        self,
        source: str,
        first_year: int,
        last_year: int,
    ) -> dict[int, int]:
        """Builds one parquet file per year, skipping years already built.

        Args:
            source: 'fno' or 'cash'.
            first_year: The first year to build.
            last_year: The last year to build.

        Returns:
            The number of rows written for each year.

        Raises:
            ValueError: If the source is not fno or cash.
        """
        if source not in ('fno', 'cash'):
            raise ValueError('source must be fno or cash')
        folder = (
            self.data_folder
            / 'nse'
            / ('fno' if source == 'fno' else 'bhavcopy')
        )
        reader = self.read_fno if source == 'fno' else self.read_cash
        counts = {}
        for year in range(first_year, last_year + 1):
            target = self.output_folder / f'{source}_{year}.parquet'
            if target.exists():
                continue
            paths = sorted(
                path
                for path in folder.glob('*.zip')
                if self.year_of(path) == year
            )
            with concurrent.futures.ProcessPoolExecutor(self.workers) as pool:
                frames = list(pool.map(reader, paths, chunksize=8))
            table = pandas.concat(frames, ignore_index=True)
            table.to_parquet(target)
            counts[year] = len(table)
            print(source, year, len(paths), len(table), flush=True)
        return counts
