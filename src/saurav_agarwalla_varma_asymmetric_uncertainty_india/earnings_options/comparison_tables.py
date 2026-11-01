"""Writes Markdown tables that set the recreation beside the paper."""

import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    paper_values,
    table_one_example,
)


class ComparisonTables:
    """Turns the result tables into Markdown comparisons with the paper."""

    REGRESSION_ORDER = (
        'RR-IV',
        'Alt RR-IV',
        'P/C',
        'ATM-IV',
        'Alt ATM-IV',
        'beta',
        'momentum',
        'size',
        'bhar',
    )

    def __init__(self, results_folder: pathlib.Path) -> None:
        """Reads the result tables of one run.

        Args:
            results_folder: A folder written by run_study.py.
        """
        self.folder = results_folder
        self.paper = paper_values.PaperValues()

    def stars(self, t_statistic: float) -> str:
        """Returns the significance stars of a two-sided t-test.

        Args:
            t_statistic: The t-statistic.

        Returns:
            Three stars at 1 percent, two at 5, one at 10, else nothing.
        """
        size = abs(t_statistic)
        if size >= 2.576:
            return '***'
        if size >= 1.960:
            return '**'
        if size >= 1.645:
            return '*'
        return ''

    def table_one(self) -> str:
        """Recomputes Table 1 and lays it out like the paper.

        Returns:
            A Markdown table.
        """
        columns = table_one_example.TableOneExample().build()
        lines = [
            '| | ' + ' | '.join(column.name for column in columns) + ' |',
            '|---|' + '---|' * len(columns),
            '| Spot | '
            + ' | '.join(f'{column.spot:.2f}' for column in columns)
            + ' |',
        ]
        for index, label in enumerate(['ITM', 'ATM', 'OTM']):
            lines.append(
                f'| {label} strike / premium / IV | '
                + ' | '.join(
                    f'{column.strikes[index]:.2f} / '
                    f'{column.premiums[index]:.2f} / '
                    f'{100 * column.volatilities[index]:.2f}%'
                    for column in columns
                )
                + ' |',
            )
        lines.append(
            '| RR-IV (points) | '
            + ' | '.join(f'{column.risk_reversal:+.2f}' for column in columns)
            + ' |',
        )
        return '\n'.join(lines)

    def table_five(self) -> str:
        """Lays out Table 5 with the paper's numbers beside ours.

        Returns:
            A Markdown table.
        """
        table = pandas.read_csv(self.folder / 'table_5.csv').set_index(
            'parameter'
        )
        labels = {
            'atm_iv': 'ATM-IV',
            'iv_75': 'IV(Δ=0.75)',
            'iv_25': 'IV(Δ=0.25)',
        }
        lines = [
            '| Level | Pre-EA month | EA month | Post-EA month | EA − pre (t) | EA − post (t) |',
            '|---|---|---|---|---|---|',
        ]
        for name, label in labels.items():
            row = table.loc[name]
            paper = self.paper.TABLE_5[name]
            lines.append(
                f'| {label}, this study | {row["pre"]:.3f} | {row["ea"]:.3f} | '
                f'{row["post"]:.3f} | {row["ea_minus_pre"]:+.3f} '
                f'({row["t_welch_pre"]:.2f}; paired {row["t_paired_pre"]:.1f}) | '
                f'{row["ea_minus_post"]:+.3f} ({row["t_welch_post"]:.2f}; '
                f'paired {row["t_paired_post"]:.1f}) |',
            )
            lines.append(
                f'| {label}, paper | {paper[0]:.3f} | {paper[1]:.3f} | '
                f'{paper[2]:.3f} | {paper[3]:+.3f} ({paper[4]:.2f}) | '
                f'{paper[5]:+.3f} ({paper[6]:.2f}) |',
            )
        events = int(table['events'].iloc[0])
        lines.append('')
        lines.append(
            f'Events with at least five smile days in each of the three months: {events:,}. '
            "The first t-statistic is Welch's two-sample test, as a difference in means; the paired one compares months within each event.",
        )
        return '\n'.join(lines)

    def regression(self, key: str = 'tables_6_to_9') -> str:
        """Lays out Tables 6 to 9, SUE columns, beside the paper.

        Args:
            key: Which regression file to read.

        Returns:
            Markdown tables, one per paper table.
        """
        table = pandas.read_csv(self.folder / f'{key}.csv')
        blocks = []
        for name in ('Table 6', 'Table 7', 'Table 8', 'Table 9'):
            part = table[table['table'] == name]
            columns = list(dict.fromkeys(part['column']))
            header = (
                '| Variable | '
                + ' | '.join(
                    f'{column} this study | {column} paper'
                    for column in columns
                )
                + ' |'
            )
            lines = [
                f'**{name}**',
                '',
                header,
                '|---|' + '---|---|' * len(columns),
            ]
            for variable in self.REGRESSION_ORDER:
                rows = part[part['variable'] == variable]
                if rows.empty:
                    continue
                cells = []
                for column in columns:
                    ours = rows[rows['column'] == column]
                    paper = self.paper.REGRESSIONS[(name, column)].get(variable)
                    if ours.empty:
                        cells.append('')
                    else:
                        record = ours.iloc[0]
                        cells.append(
                            f'{record["coefficient"]:.3f}'
                            f'{self.stars(record["t_statistic"])} '
                            f'({record["standard_error"]:.3f}; '
                            f'clustered t {record["clustered_t_statistic"]:.2f})',
                        )
                    if paper is None:
                        cells.append('')
                    else:
                        cells.append(
                            f'{paper[0]:.3f}'
                            f'{self.stars(paper[0] / paper[1])} ({paper[1]:.3f})',
                        )
                lines.append(f'| {variable} | ' + ' | '.join(cells) + ' |')
            counts = []
            for column in columns:
                record = part[part['column'] == column].iloc[0]
                paper = self.paper.REGRESSIONS[(name, column)]
                counts.append(f'{int(record["observations"]):,}')
                counts.append(f'{paper["observations"]:,}')
            lines.append('| Observations | ' + ' | '.join(counts) + ' |')
            fits = []
            for column in columns:
                record = part[part['column'] == column].iloc[0]
                paper = self.paper.REGRESSIONS[(name, column)]
                fits.append(
                    f'{record["adjusted_r2"]:.3f} (within {record["within_r2"]:.3f})',
                )
                fits.append(f'{paper["adjusted_r2"]:.3f}')
            lines.append('| Adjusted R² | ' + ' | '.join(fits) + ' |')
            blocks.append('\n'.join(lines))
        return '\n\n'.join(blocks)

    def table_three(self) -> str:
        """Sets Table 3's counts, means and standard deviations beside the paper.

        Returns:
            A Markdown table.
        """
        table = pandas.read_csv(self.folder / 'table_3.csv').set_index(
            'variable'
        )
        lines = [
            '| Variable | N | Mean | St. dev. | Median | Paper N | Paper mean | Paper st. dev. |',
            '|---|---|---|---|---|---|---|---|',
        ]
        for name, paper in self.paper.TABLE_3.items():
            if name not in table.index:
                continue
            row = table.loc[name]
            lines.append(
                f'| {name} | {int(row["N"]):,} | {row["mean"]:.3f} | '
                f'{row["st_dev"]:.3f} | {row["median"]:.3f} | {paper[0]:,} | '
                f'{paper[1]:.3f} | {paper[2]:.3f} |',
            )
        return '\n'.join(lines)

    def table_four(self) -> str:
        """Sets the correlations with SUE beside the paper's Table 4.

        Returns:
            A Markdown table.
        """
        table = pandas.read_csv(self.folder / 'table_4.csv').set_index(
            'variable'
        )
        lines = ['| Variable | Correlation with SUE | Paper |', '|---|---|---|']
        for name, paper in self.paper.TABLE_4_SUE.items():
            lines.append(
                f'| {name} | {table.loc[name, "sue"]:.3f} | {paper:.3f} |'
            )
        return '\n'.join(lines)

    def figure_points(self) -> str:
        """Lists key points of the figures beside values read off the paper.

        Returns:
            A Markdown table.
        """
        four = pandas.read_csv(self.folder / 'figure_4.csv')
        lines = [
            '| Series | Day | This study | Paper (read off chart) |',
            '|---|---|---|---|',
        ]
        for variable, label in [('os_ratio', 'O/S'), ('of_ratio', 'O/F')]:
            rows = four[four['variable'] == variable].set_index('offset')
            for day, value in self.paper.FIGURE_4[variable].items():
                lines.append(
                    f'| {label} | {day:+d} | {rows.loc[day, "mean"]:.2f} | {value:.2f} |',
                )
        three = pandas.read_csv(self.folder / 'figure_3.csv')
        rows = three[three['tercile'] == 1].set_index('offset')
        for day, value in self.paper.FIGURE_3_SUE_LARGE_NEGATIVE.items():
            lines.append(
                f'| RR-IV, large negative SUE | {day:+d} | {rows.loc[day, "mean"]:.4f} | {value:.4f} |',
            )
        return '\n'.join(lines)
