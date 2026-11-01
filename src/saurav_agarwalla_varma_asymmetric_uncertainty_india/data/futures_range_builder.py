"""Finds the dates on which each share had stock futures."""

import json
import pathlib

import pandas


class FuturesRangeBuilder:
    """Reads the yearly F&O stores and lists each share's futures dates."""

    def __init__(self, data_folder: pathlib.Path) -> None:
        """Remembers the study's data folder.

        Args:
            data_folder: The study's data folder.
        """
        self.data_folder = data_folder

    def build(self, first_year: int, last_year: int) -> dict[str, list]:
        """Finds first date, last date and number of days for each symbol.

        Args:
            first_year: The first year of the stores to read.
            last_year: The last year of the stores to read.

        Returns:
            A dictionary from symbol to the first date, last date and
            number of days on which a stock future traded.
        """
        pieces = []
        for year in range(first_year, last_year + 1):
            table = pandas.read_parquet(
                self.data_folder / 'derived' / f'fno_{year}.parquet',
                columns=['date', 'symbol', 'kind'],
            )
            futures = table[table['kind'] == 'FUT']
            pieces.append(futures[['date', 'symbol']].drop_duplicates())
        days = pandas.concat(pieces, ignore_index=True)
        grouped = days.groupby('symbol')['date']
        summary = pandas.DataFrame(
            {
                'first': grouped.min(),
                'last': grouped.max(),
                'days': grouped.size(),
            },
        )
        return {
            symbol: [
                row['first'].date().isoformat(),
                row['last'].date().isoformat(),
                int(row['days']),
            ]
            for symbol, row in summary.iterrows()
        }

    def save(self, ranges: dict[str, list], path: pathlib.Path) -> None:
        """Writes the ranges as JSON.

        Args:
            ranges: The result of build.
            path: Where to write.
        """
        path.write_text(json.dumps(ranges))
