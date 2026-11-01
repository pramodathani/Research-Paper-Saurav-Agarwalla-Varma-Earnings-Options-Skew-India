"""Chooses which NSE results filings to download for the study."""

import datetime
import json
import pathlib


class ResultsFilingTargets:
    """Lists the standalone quarterly filings of every share with futures."""

    FIRST_YEAR = 2010
    LAST_DATE = datetime.date(2025, 4, 30)
    MARGIN_DAYS = 800

    def __init__(self, data_folder: pathlib.Path) -> None:
        """Remembers where the study's data folder is.

        Args:
            data_folder: The study's data folder.
        """
        self.data_folder = data_folder

    def build(self, ranges_path: pathlib.Path) -> list[dict[str, str]]:
        """Reads the results rows and keeps the ones the study needs.

        Args:
            ranges_path: A JSON file mapping each symbol with stock futures
                to its first date, last date and number of days.

        Returns:
            One dictionary per filing with symbol, to_date, broadcast and url.

        Raises:
            FileNotFoundError: If the ranges file does not exist.
        """
        ranges = json.loads(ranges_path.read_text())
        targets = []
        results_folder = self.data_folder / 'nse' / 'results_dates'
        for path in sorted(results_folder.glob('results_*.json')):
            for row in json.loads(path.read_text()):
                target = self.convert(row, ranges)
                if target is not None:
                    targets.append(target)
        return targets

    def convert(
        self,
        row: dict,
        ranges: dict[str, list],
    ) -> dict[str, str] | None:
        """Turns one results row into a target, or None to skip it.

        Args:
            row: One row of NSE's financial results answer.
            ranges: The futures date ranges by symbol.

        Returns:
            The target dictionary, or None when the row is not needed.
        """
        symbol = row['symbol']
        if symbol not in ranges:
            return None
        if row['consolidated'] != 'Non-Consolidated':
            return None
        try:
            broadcast = datetime.datetime.strptime(
                row['broadCastDate'],
                '%d-%b-%Y %H:%M:%S',
            ).date()
        except TypeError, ValueError:
            return None
        first = datetime.date.fromisoformat(ranges[symbol][0])
        last = datetime.date.fromisoformat(ranges[symbol][1])
        margin = datetime.timedelta(days=self.MARGIN_DAYS)
        if broadcast < first - margin:
            return None
        if broadcast > last + datetime.timedelta(days=100):
            return None
        if broadcast.year < self.FIRST_YEAR or broadcast > self.LAST_DATE:
            return None
        url = row.get('resultDetailedDataLink') or ''
        if not url:
            xbrl = row.get('xbrl') or ''
            if not xbrl.endswith('/-'):
                url = xbrl
        return {
            'symbol': symbol,
            'to_date': row['toDate'],
            'broadcast': row['broadCastDate'],
            'url': url,
        }
