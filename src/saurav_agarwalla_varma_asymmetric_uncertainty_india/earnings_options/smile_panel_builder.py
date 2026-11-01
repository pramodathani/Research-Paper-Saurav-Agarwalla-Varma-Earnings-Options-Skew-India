"""Builds the stock-day smile panel from the yearly F&O stores."""

import concurrent.futures
import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    risk_free_rates,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    smile_day_builder,
)


class SmilePanelBuilder:
    """Fits one smile per stock and day on the near-month series."""

    DAYS_PER_YEAR = 365.0

    def __init__(
        self,
        data_folder: pathlib.Path,
        min_traded_contracts: int = 5,
        price_field: str = 'close',
        price_error: bool = False,
        workers: int = 16,
    ) -> None:
        """Stores the settings, which are plain values so they can be sent
        to worker processes.

        Args:
            data_folder: The study's data folder.
            min_traded_contracts: The liquidity filter on each option.
            price_field: 'close' or 'settle', used for options and futures.
            price_error: Fit premium errors instead of IV errors.
            workers: How many months are processed at the same time.
        """
        self.data_folder = data_folder
        self.min_traded_contracts = min_traded_contracts
        self.price_field = price_field
        self.price_error = price_error
        self.workers = workers

    def build_frame(
        self,
        frame: pandas.DataFrame,
        rates: risk_free_rates.RiskFreeRates,
    ) -> pandas.DataFrame:
        """Fits every stock-day of a normalised F&O table.

        The series used on a day is the nearest expiry strictly after the
        day that has a stock future that traded, which is the near month.

        Args:
            frame: Rows from the F&O reader for any set of days.
            rates: The risk-free rate lookup.

        Returns:
            One row per fitted stock-day with the smile measures.
        """
        builder = smile_day_builder.SmileDayBuilder(
            self.min_traded_contracts,
            self.price_error,
        )
        futures = frame[frame['kind'] == 'FUT']
        options = frame[frame['kind'] == 'OPT']
        future_prices = {
            (row.date, row.symbol, row.expiry): getattr(row, self.price_field)
            for row in futures.itertuples()
        }
        expiries = futures.groupby(['date', 'symbol'])['expiry'].apply(sorted)
        rows = []
        for (date, symbol), group in options.groupby(['date', 'symbol']):
            candidates = expiries.get((date, symbol))
            if candidates is None:
                continue
            later = [expiry for expiry in candidates if expiry > date]
            if not later:
                continue
            expiry = later[0]
            chain = group[group['expiry'] == expiry]
            forward = future_prices[(date, symbol, expiry)]
            chain = chain.assign(price=chain[self.price_field])
            years = (expiry - date).days / self.DAYS_PER_YEAR
            result = builder.build(chain, forward, years, rates.rate(date))
            if result is None:
                continue
            result.update(
                {
                    'date': date,
                    'symbol': symbol,
                    'expiry': expiry,
                    'forward': forward,
                    'calendar_days_to_expiry': (expiry - date).days,
                },
            )
            rows.append(result)
        return pandas.DataFrame(rows)

    @staticmethod
    def build_month(arguments: dict) -> pandas.DataFrame:
        """Fits one calendar month, run in a worker process.

        Args:
            arguments: A dictionary with the data folder, settings, year and
                month.

        Returns:
            The month's smile panel.
        """
        builder = SmilePanelBuilder(
            pathlib.Path(arguments['data_folder']),
            arguments['min_traded_contracts'],
            arguments['price_field'],
            arguments['price_error'],
        )
        rates = risk_free_rates.RiskFreeRates(
            builder.data_folder / 'nse' / 'iima' / arguments['iima_file'],
        )
        path = (
            builder.data_folder / 'derived' / f'fno_{arguments["year"]}.parquet'
        )
        table = pandas.read_parquet(path)
        table = table[table['date'].dt.month == arguments['month']]
        return builder.build_frame(table, rates)

    def build(self, first_year: int, last_year: int) -> pandas.DataFrame:
        """Fits every month of a range of years, in parallel.

        Args:
            first_year: The first year.
            last_year: The last year.

        Returns:
            The stock-day smile panel.
        """
        iima = next((self.data_folder / 'nse' / 'iima').glob('*.csv')).name
        jobs = [
            {
                'data_folder': str(self.data_folder),
                'min_traded_contracts': self.min_traded_contracts,
                'price_field': self.price_field,
                'price_error': self.price_error,
                'iima_file': iima,
                'year': year,
                'month': month,
            }
            for year in range(first_year, last_year + 1)
            for month in range(1, 13)
        ]
        with concurrent.futures.ProcessPoolExecutor(self.workers) as pool:
            pieces = []
            for index, piece in enumerate(pool.map(self.build_month, jobs)):
                pieces.append(piece)
                print(
                    'month', index + 1, 'of', len(jobs), len(piece), flush=True
                )
        return pandas.concat(pieces, ignore_index=True)
