"""Reads NIFTY 500 total-return index levels saved from niftyindices.com."""

import json
import pathlib

import pandas


class MarketIndexReader:
    """Joins the five-year JSON chunks into one daily series."""

    def read(
        self, folder: pathlib.Path, name: str = 'NIFTY_500'
    ) -> pandas.Series:
        """Reads every chunk of one index.

        Args:
            folder: The total_return folder.
            name: The index's file prefix, such as NIFTY_500.

        Returns:
            Daily total-return index levels indexed by date.

        Raises:
            FileNotFoundError: If no chunk of that index exists.
        """
        paths = sorted(folder.glob(f'{name}_[0-9]*.json'))
        if not paths:
            raise FileNotFoundError(f'No chunks for {name} in {folder}')
        rows = []
        for path in paths:
            for item in json.loads(path.read_text()):
                rows.append(
                    {
                        'date': pandas.to_datetime(
                            item['Date'],
                            format='%d %b %Y',
                        ),
                        'level': float(item['TotalReturnsIndex']),
                    },
                )
        table = pandas.DataFrame(rows).drop_duplicates('date')
        return table.set_index('date')['level'].sort_index()
