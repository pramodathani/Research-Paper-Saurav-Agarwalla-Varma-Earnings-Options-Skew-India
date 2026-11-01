"""Draws the paper's Figures 1 to 5 from the result tables."""

import pathlib

import matplotlib
import pandas

matplotlib.use('Agg')
from matplotlib import pyplot


class FigureDrawer:
    """Draws event-window charts in the Google chart style."""

    BLUE = '#1A73E8'
    ORANGE = '#E8710A'
    TEAL = '#12B5CB'
    GREY = '#5F6368'
    GRID = '#DADCE0'
    TERCILE_COLOURS = ('#E8710A', '#5F6368', '#1A73E8')
    TERCILE_LABELS = (
        'Large negative surprise',
        'Small surprise',
        'Large positive surprise',
    )

    def __init__(self, results_folder: pathlib.Path) -> None:
        """Remembers where the result tables are.

        Args:
            results_folder: A folder holding figure_1.csv to figure_5.csv.
        """
        self.results_folder = results_folder
        self.output_folder = results_folder / 'figures'
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def style(self, axes, title: str, label: str) -> None:
        """Applies the chart style: horizontal grid only, no frame.

        Args:
            axes: The matplotlib axes.
            title: The chart title.
            label: The y-axis label.
        """
        axes.set_title(title, loc='left', fontsize=12, color='#1F1F1F')
        axes.set_xlabel('Trading days from the announcement', fontsize=10)
        axes.set_ylabel(label, fontsize=10, color=self.GREY)
        axes.grid(axis='y', color=self.GRID, linewidth=1)
        axes.grid(axis='x', visible=False)
        for side in ('top', 'right', 'left'):
            axes.spines[side].set_visible(False)
        axes.spines['bottom'].set_color(self.GRID)
        axes.tick_params(colors=self.GREY, labelsize=9, length=0)
        axes.axvline(0, color=self.GREY, linestyle=(0, (4, 4)), linewidth=1)
        axes.set_xticks(range(-10, 11, 2))

    def draw_lines(
        self,
        table: pandas.DataFrame,
        series: list[tuple[str, str]],
        title: str,
        label: str,
        name: str,
        group_column: str | None = None,
        reference: dict[int, float] | None = None,
    ) -> pathlib.Path:
        """Draws one chart with one or more lines.

        Args:
            table: Rows with offset and mean, and the group column.
            series: Pairs of group value and legend label, or one pair of
                the variable's value and label when there is no group.
            title: The chart title.
            label: The y-axis label.
            name: The file name without extension.
            group_column: The column that tells the lines apart.
            reference: Optional values read off the paper, plotted as grey
                markers.

        Returns:
            The path of the saved image.
        """
        figure, axes = pyplot.subplots(figsize=(7.2, 4.0), dpi=150)
        colours = [self.BLUE, self.ORANGE, self.TEAL]
        if group_column == 'tercile':
            colours = list(self.TERCILE_COLOURS)
        for index, (value, legend) in enumerate(series):
            if group_column is None:
                rows = table
            else:
                rows = table[table[group_column] == value]
            axes.plot(
                rows['offset'],
                rows['mean'],
                color=colours[index % len(colours)],
                linewidth=2,
                label=legend,
            )
        if reference:
            axes.scatter(
                list(reference),
                list(reference.values()),
                color=self.GREY,
                s=22,
                zorder=3,
                label='Paper (read off the chart)',
            )
        self.style(axes, title, label)
        if len(series) > 1 or reference:
            axes.legend(frameon=False, fontsize=9, loc='upper left')
        figure.tight_layout()
        path = self.output_folder / f'{name}.png'
        figure.savefig(path)
        pyplot.close(figure)
        return path

    def draw_all(self) -> list[pathlib.Path]:
        """Draws every figure for which a result table exists.

        Returns:
            The saved image paths.
        """
        paths = []
        one = pandas.read_csv(self.results_folder / 'figure_1.csv')
        for column, legend in [
            ('atm_iv_normalised', 'ATM-IV'),
            ('iv_75_normalised', 'IV at delta 0.75'),
            ('iv_25_normalised', 'IV at delta 0.25'),
        ]:
            rows = one[one['variable'] == column]
            paths.append(
                self.draw_lines(
                    rows,
                    [(column, legend)],
                    f'Figure 1: {legend} around earnings',
                    'Mean, divided by its level the month before',
                    f'figure_1_{column}',
                ),
            )
        terciles = list(zip((1, 2, 3), self.TERCILE_LABELS, strict=True))
        for number, label, title in [
            (2, 'ATM-IV, normalised', 'Figure 2(b): ATM-IV by SUE tercile'),
            (3, 'RR-IV', 'Figure 3(b): RR-IV by SUE tercile'),
            (5, 'Put-to-call ratio', 'Figure 5(b): P/C by SUE tercile'),
        ]:
            table = pandas.read_csv(
                self.results_folder / f'figure_{number}.csv'
            )
            paths.append(
                self.draw_lines(
                    table,
                    terciles,
                    title,
                    label,
                    f'figure_{number}b',
                    group_column='tercile',
                ),
            )
        four = pandas.read_csv(self.results_folder / 'figure_4.csv')
        for column, title, reference in [
            (
                'os_ratio',
                'Figure 4(a): options to stock volume',
                {-10: 1.05, -2: 1.22, -1: 1.52, 0: 1.63, 1: 1.46},
            ),
            (
                'of_ratio',
                'Figure 4(b): options to futures volume',
                {-10: 0.46, -2: 0.51, -1: 0.64, 0: 0.71, 1: 0.68},
            ),
        ]:
            rows = four[four['variable'] == column]
            paths.append(
                self.draw_lines(
                    rows,
                    [(column, 'This study')],
                    title,
                    'Mean ratio',
                    f'figure_{column}',
                    reference=reference,
                ),
            )
        return paths
