"""Turns the study's result tables into the companion page's JSON snapshot."""

import json
import math
import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    paper_values,
    table_one_example,
)


class SiteSnapshot:
    """Builds site/data/snapshot.json from derived results only."""

    RUNS = (
        ('main', 'main', '2015-2019, main smile'),
        ('extension', 'extension_2020_2025', '2020 to March 2025, main smile'),
        ('c1', 'variants/c1', '2015-2019, at least 1 contract'),
        ('c20', 'variants/c20', '2015-2019, at least 20 contracts'),
        ('settle', 'variants/settle', '2015-2019, settle prices'),
        ('priceerror', 'variants/priceerror', '2015-2019, premium-error fit'),
    )
    REGRESSIONS = (
        ('sue_contracts', 'tables_6_to_9'),
        ('sue_value', 'tables_6_to_9_pc_value'),
        ('alternative_contracts', 'tables_6_to_9_sue_alternative'),
    )

    def __init__(self, results_folder: pathlib.Path) -> None:
        """Remembers where the results are.

        Args:
            results_folder: The study's results folder.
        """
        self.results = results_folder

    def clean(self, value: object, digits: int = 4) -> object:
        """Rounds a number for JSON and turns NaN into None.

        Args:
            value: Any value.
            digits: Decimal places to keep.

        Returns:
            The rounded number, None for NaN, or the value unchanged.
        """
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            return round(value, digits)
        if hasattr(value, 'item'):
            return self.clean(value.item(), digits)
        return value

    def records(self, table: pandas.DataFrame, digits: int = 4) -> list[dict]:
        """Turns a table into a list of rounded records.

        Args:
            table: A result table.
            digits: Decimal places to keep.

        Returns:
            One dictionary per row.
        """
        rows = []
        for record in table.to_dict(orient='records'):
            rows.append(
                {
                    key: self.clean(value, digits)
                    for key, value in record.items()
                },
            )
        return rows

    def series(self, table: pandas.DataFrame, group: str | None) -> dict:
        """Turns an event-study table into lines by offset.

        Args:
            table: A figure table with offset and mean, and a group column.
            group: The column naming the line, or None for one line.

        Returns:
            A dictionary from line name to the means by offset, with the
            offsets under 'offsets'.
        """
        offsets = sorted(table['offset'].unique())
        result = {'offsets': [int(offset) for offset in offsets]}
        if group is None:
            values = table.set_index('offset').reindex(offsets)['mean']
            result['mean'] = [self.clean(value, 4) for value in values]
            return result
        for name, part in table.groupby(group):
            values = part.set_index('offset').reindex(offsets)['mean']
            result[str(name)] = [self.clean(value, 4) for value in values]
        return result

    def read_table(self, folder: pathlib.Path, name: str) -> pandas.DataFrame:
        """Reads one result table of a run.

        Args:
            folder: The run's folder.
            name: The table's name without .csv.

        Returns:
            The table.
        """
        return pandas.read_csv(folder / f'{name}.csv')

    def run(self, folder: pathlib.Path) -> dict:
        """Collects one run's tables and figure lines.

        Args:
            folder: A folder written by run_study.py or the sensitivity run.

        Returns:
            The run's part of the snapshot.
        """
        figure_one = self.read_table(folder, 'figure_1')
        figure_four = self.read_table(folder, 'figure_4')
        run = {
            'figure_1': {
                name: self.series(
                    figure_one[figure_one['variable'] == name], None
                )
                for name in figure_one['variable'].unique()
            },
            'figure_2': self.series(
                self.read_table(folder, 'figure_2'), 'tercile'
            ),
            'figure_3': self.series(
                self.read_table(folder, 'figure_3'), 'tercile'
            ),
            'figure_5': self.series(
                self.read_table(folder, 'figure_5'), 'tercile'
            ),
            'figure_5_value': self.series(
                self.read_table(folder, 'figure_5_value'), 'tercile'
            ),
            'figure_4': {
                name: self.series(
                    figure_four[figure_four['variable'] == name], None
                )
                for name in figure_four['variable'].unique()
            },
            'table_5': self.records(self.read_table(folder, 'table_5')),
            'table_3': self.records(self.read_table(folder, 'table_3')),
            'table_4': self.records(self.read_table(folder, 'table_4')),
            'regressions': {},
        }
        for key, name in self.REGRESSIONS:
            table = self.read_table(folder, name).drop(
                columns=['lag'], errors='ignore'
            )
            run['regressions'][key] = self.records(table)
        events = folder / 'events.csv'
        if events.exists():
            frame = pandas.read_csv(events)
            run['events'] = len(frame)
            run['firms'] = int(frame['symbol'].nunique())
        return run

    def trading(self) -> dict:
        """Collects the trading test's summary and daily returns.

        Returns:
            The summary rows and, for each period, the dates and the gross
            and net daily returns of each signal and cost setting.
        """
        summary = pandas.read_csv(self.results / 'trading_test.csv')
        daily = pandas.read_csv(self.results / 'trading_test_daily.csv')
        periods = {}
        for period, part in daily.groupby('period'):
            dates = sorted(part['date'].unique())
            lines = {}
            for (signal, costs), piece in part.groupby(['signal', 'costs']):
                piece = piece.set_index('date').reindex(dates)
                lines.setdefault(
                    signal,
                    {'gross': [self.clean(v, 6) for v in piece['gross']]},
                )
                lines[signal][costs] = [self.clean(v, 6) for v in piece['net']]
            periods[period] = {'dates': dates, 'lines': lines}
        return {'summary': self.records(summary, 6), 'daily': periods}

    def table_one(self) -> list[dict]:
        """Recomputes Table 1.

        Returns:
            One dictionary per scenario.
        """
        columns = []
        for column in table_one_example.TableOneExample().build():
            columns.append(
                {
                    'name': column.name,
                    'spot': round(column.spot, 2),
                    'strikes': [round(value, 2) for value in column.strikes],
                    'premiums': [round(value, 2) for value in column.premiums],
                    'volatilities': [
                        round(100 * value, 2) for value in column.volatilities
                    ],
                    'risk_reversal': round(column.risk_reversal, 2),
                },
            )
        return columns

    def paper(self) -> dict:
        """Collects the paper's printed numbers.

        Returns:
            The paper's Table 3, 4 and 5 values, regressions and figure
            points.
        """
        values = paper_values.PaperValues()
        regressions = []
        for (table, column), entries in values.REGRESSIONS.items():
            for variable, pair in entries.items():
                if isinstance(pair, tuple):
                    regressions.append(
                        {
                            'table': table,
                            'column': column,
                            'variable': variable,
                            'coefficient': pair[0],
                            'standard_error': pair[1],
                        },
                    )
            regressions.append(
                {
                    'table': table,
                    'column': column,
                    'variable': 'observations',
                    'coefficient': entries['observations'],
                    'standard_error': None,
                },
            )
            regressions.append(
                {
                    'table': table,
                    'column': column,
                    'variable': 'adjusted_r2',
                    'coefficient': entries['adjusted_r2'],
                    'standard_error': None,
                },
            )
        return {
            'table_5': {
                key: list(value) for key, value in values.TABLE_5.items()
            },
            'table_3': {
                key: list(value) for key, value in values.TABLE_3.items()
            },
            'table_4': values.TABLE_4_SUE,
            'figure_4': {
                key: {str(day): value for day, value in points.items()}
                for key, points in values.FIGURE_4.items()
            },
            'figure_3': {
                str(day): value
                for day, value in values.FIGURE_3_SUE_LARGE_NEGATIVE.items()
            },
            'regressions': regressions,
            'sample': values.SAMPLE,
        }

    def build(self) -> dict:
        """Builds the whole snapshot from the runs that exist.

        Returns:
            The snapshot dictionary.
        """
        runs = {}
        labels = {}
        for key, folder, label in self.RUNS:
            path = self.results / folder
            if (path / 'figure_1.csv').exists():
                runs[key] = self.run(path)
                labels[key] = label
        sensitivity = pandas.read_csv(self.results / 'sensitivity.csv')
        return {
            'runs': runs,
            'run_labels': labels,
            'trading': self.trading(),
            'sensitivity': self.records(sensitivity),
            'table_1': self.table_one(),
            'paper': self.paper(),
        }

    def write(self, site_folder: pathlib.Path) -> int:
        """Writes the snapshot into the site's data folder.

        Args:
            site_folder: The package's site folder.

        Returns:
            The size of the file in bytes.
        """
        target = site_folder / 'data' / 'snapshot.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.build(), separators=(',', ':'))
        target.write_text(text)
        return len(text)
