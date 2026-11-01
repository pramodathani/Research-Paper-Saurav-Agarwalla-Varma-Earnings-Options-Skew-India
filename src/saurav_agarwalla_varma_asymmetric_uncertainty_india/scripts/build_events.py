"""Builds the event table from the EPS panel and the derived stores."""

import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    event_builder,
    trading_calendar,
)


class BuildEventsApplication:
    """Command-line program that builds the events."""

    def run(self) -> None:
        """Builds the events and saves them as parquet.

        Raises:
            FileNotFoundError: If a derived store is missing.
        """
        data_folder = pathlib.Path('data')
        derived = data_folder / 'derived'
        dates = []
        expiries = []
        for year in range(2009, 2026):
            cash = pandas.read_parquet(
                derived / f'cash_{year}.parquet',
                columns=['date'],
            )
            dates += list(cash['date'].dt.date.unique())
        for year in range(2014, 2026):
            fno = pandas.read_parquet(
                derived / f'fno_{year}.parquet',
                columns=['symbol', 'kind', 'expiry'],
            )
            futures = fno[fno['kind'] == 'FUT']
            expiries.append(futures[['symbol', 'expiry']].drop_duplicates())
        expiry_table = pandas.concat(expiries).drop_duplicates()
        ratios = pandas.read_parquet(
            derived / 'volume_ratios_2014_2025.parquet',
            columns=['date', 'symbol'],
        )
        builder = event_builder.EventBuilder(
            trading_calendar.TradingCalendar(dates),
            expiry_table,
            ratios,
        )
        panel = pandas.read_parquet(derived / 'eps_panel.parquet')
        events = builder.build(panel)
        events.to_parquet(derived / 'events.parquet')
        events['year'] = events['broadcast'].dt.year
        print(events.groupby('year')['keep'].agg(['size', 'sum']))
        print(events['reason'].value_counts())


if __name__ == '__main__':
    BuildEventsApplication().run()
