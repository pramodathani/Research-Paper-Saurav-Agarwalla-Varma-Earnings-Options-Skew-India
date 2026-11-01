"""Runs the study for every variant and collects the headline numbers."""

import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    market_index_reader,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    sensitivity_summary,
    study_runner,
    trading_calendar,
)


class RunSensitivitiesApplication:
    """Command-line program that runs the sensitivity analysis."""

    SMILE_VARIANTS = (
        (
            'main (5 contracts, IV error, close)',
            'smile_main_2014_2025.parquet',
            'main',
        ),
        ('at least 1 contract', 'smile_c1_2014_2020.parquet', 'c1'),
        ('at least 20 contracts', 'smile_c20_2014_2020.parquet', 'c20'),
        (
            'premium-error fit',
            'smile_priceerror_2014_2020.parquet',
            'priceerror',
        ),
        ('settle prices', 'smile_settle_2014_2020.parquet', 'settle'),
    )

    def run(self) -> None:
        """Runs all variants for 2015 to 2019 and saves one table.

        Raises:
            FileNotFoundError: If a smile panel is missing.
        """
        derived = pathlib.Path('data') / 'derived'
        dates = []
        for year in range(2009, 2026):
            cash = pandas.read_parquet(
                derived / f'cash_{year}.parquet',
                columns=['date'],
            )
            dates += list(cash['date'].dt.date.unique())
        panel = pandas.read_parquet(derived / 'eps_panel.parquet')
        shared = {
            'events': pandas.read_parquet(derived / 'events.parquet'),
            'ratios': pandas.read_parquet(
                derived / 'volume_ratios_2014_2025.parquet',
            ),
            'daily_returns': pandas.read_parquet(
                derived / 'daily_returns_2009_2025.parquet',
            ),
            'market_levels': market_index_reader.MarketIndexReader().read(
                pathlib.Path('data') / 'niftyindices' / 'total_return',
            ),
            'calendar': trading_calendar.TradingCalendar(dates),
            'shares': panel[['symbol', 'broadcast', 'shares']],
        }
        summary = sensitivity_summary.SensitivitySummary()
        rows = []
        for name, file_name, key in self.SMILE_VARIANTS:
            if not (derived / file_name).exists():
                print('skipped, panel not built yet:', name, flush=True)
                continue
            inputs = study_runner.StudyInputs(
                smile=pandas.read_parquet(derived / file_name),
                **shared,
            )
            results = study_runner.StudyRunner(inputs).run()
            rows.append(summary.row(name, results))
            if key != 'main':
                self.save(results, pathlib.Path('results') / 'variants' / key)
            print(name, flush=True)
            if file_name.startswith('smile_main'):
                rows.append(
                    summary.row(
                        'main, P/C in value',
                        results,
                        'tables_6_to_9_pc_value',
                    ),
                )
                rows.append(
                    summary.row(
                        'main, alternative SUE',
                        results,
                        'tables_6_to_9_sue_alternative',
                    ),
                )
        table = pandas.DataFrame(rows)
        target = pathlib.Path('results') / 'sensitivity.csv'
        table.to_csv(target, index=False)
        print(table.round(3).T.to_string())

    def save(
        self,
        results: dict[str, pandas.DataFrame],
        folder: pathlib.Path,
    ) -> None:
        """Saves a variant's derived result tables, without the event rows.

        Args:
            results: The result tables of one run.
            folder: Where to write them.
        """
        folder.mkdir(parents=True, exist_ok=True)
        for name, table in results.items():
            if name in ('events', 'dataset'):
                continue
            table.to_csv(folder / f'{name}.csv', index=False)


if __name__ == '__main__':
    RunSensitivitiesApplication().run()
