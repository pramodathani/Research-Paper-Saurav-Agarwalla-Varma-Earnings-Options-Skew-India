"""Runs the study on the real derived data and writes the result tables."""

import argparse
import json
import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    market_index_reader,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    study_runner,
    trading_calendar,
)


class RunStudyApplication:
    """Command-line program that runs the study."""

    def run(self) -> None:
        """Loads the inputs, runs the study and saves every table as CSV.

        Raises:
            FileNotFoundError: If a derived file is missing.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--smile', default='smile_main_2014_2025.parquet')
        parser.add_argument('--first-date', default='2015-01-01')
        parser.add_argument('--last-date', default='2019-12-31')
        parser.add_argument('--output', default='results/main')
        arguments = parser.parse_args()
        derived = pathlib.Path('data') / 'derived'
        dates = []
        for year in range(2009, 2026):
            cash = pandas.read_parquet(
                derived / f'cash_{year}.parquet',
                columns=['date'],
            )
            dates += list(cash['date'].dt.date.unique())
        events = pandas.read_parquet(derived / 'events.parquet')
        panel = pandas.read_parquet(derived / 'eps_panel.parquet')
        market = market_index_reader.MarketIndexReader().read(
            pathlib.Path('data') / 'niftyindices' / 'total_return',
        )
        inputs = study_runner.StudyInputs(
            events=events,
            smile=pandas.read_parquet(derived / arguments.smile),
            ratios=pandas.read_parquet(
                derived / 'volume_ratios_2014_2025.parquet',
            ),
            daily_returns=pandas.read_parquet(
                derived / 'daily_returns_2009_2025.parquet',
            ),
            market_levels=market,
            calendar=trading_calendar.TradingCalendar(dates),
            shares=panel[['symbol', 'broadcast', 'shares']],
        )
        runner = study_runner.StudyRunner(
            inputs,
            arguments.first_date,
            arguments.last_date,
        )
        results = runner.run()
        output = pathlib.Path(arguments.output)
        output.mkdir(parents=True, exist_ok=True)
        for name, table in results.items():
            table.to_csv(output / f'{name}.csv', index=False)
        summary = {name: len(table) for name, table in results.items()}
        (output / 'row_counts.json').write_text(json.dumps(summary, indent=2))
        print(summary)


if __name__ == '__main__':
    RunStudyApplication().run()
