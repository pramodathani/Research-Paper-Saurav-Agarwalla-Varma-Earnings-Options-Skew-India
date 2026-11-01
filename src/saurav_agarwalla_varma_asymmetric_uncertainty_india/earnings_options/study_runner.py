"""Runs the whole study on prepared inputs and returns every result table."""

import dataclasses

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    controls_builder,
    descriptive_statistics,
    event_study,
    event_window_builder,
    month_comparison,
    regression_dataset_builder,
    regression_tables,
    trading_calendar,
)


@dataclasses.dataclass
class StudyInputs:
    """Everything the study needs, already loaded.

    Attributes:
        events: All announcements with day0, keep and surprise columns.
        smile: The stock-day smile panel.
        ratios: The stock-day volume ratio table.
        daily_returns: Adjusted daily returns with close.
        market_levels: Daily NIFTY 500 total-return index levels.
        calendar: The trading calendar.
        shares: Rows with symbol, broadcast and shares per filing.
    """

    events: pandas.DataFrame
    smile: pandas.DataFrame
    ratios: pandas.DataFrame
    daily_returns: pandas.DataFrame
    market_levels: pandas.Series
    calendar: trading_calendar.TradingCalendar
    shares: pandas.DataFrame


class StudyRunner:
    """Builds the sample and every table and figure series."""

    def __init__(
        self,
        inputs: StudyInputs,
        first_date: str = '2015-01-01',
        last_date: str = '2019-12-31',
    ) -> None:
        """Stores the inputs and the sample period.

        Args:
            inputs: The loaded inputs.
            first_date: The first day 0 of the sample.
            last_date: The last day 0 of the sample.
        """
        self.inputs = inputs
        self.first_date = pandas.Timestamp(first_date)
        self.last_date = pandas.Timestamp(last_date)

    def sample_events(self) -> pandas.DataFrame:
        """Selects the events in the sample period that have a smile on day -1.

        The paper's sample is the announcements whose RR-IV one day before
        the announcement exists on the series expiring after it, since its Table 3 has the same count for
        RR-IV, ATM-IV and P/C on that day.

        Returns:
            The kept events in the period, with a smile the day before.
        """
        events = self.inputs.events
        events = events[events['keep']]
        events = events[
            (events['day0'] >= self.first_date)
            & (events['day0'] <= self.last_date)
        ].reset_index(drop=True)
        before = []
        for day_zero in events['day0']:
            date = self.inputs.calendar.shift(day_zero.date(), -1)
            before.append(None if date is None else pandas.Timestamp(date))
        events = events.assign(day_before=before)
        smile = self.inputs.smile[['date', 'symbol', 'expiry']].assign(
            has_smile=True,
        )
        smile = smile.rename(columns={'expiry': 'smile_expiry'})
        merged = events.merge(
            smile,
            left_on=['day_before', 'symbol', 'expiry'],
            right_on=['date', 'symbol', 'smile_expiry'],
            how='left',
        )
        merged = merged[merged['has_smile'].fillna(False).astype(bool)]
        merged = merged.drop(columns=['date', 'has_smile', 'smile_expiry'])
        return merged.reset_index(drop=True)

    def run(self) -> dict[str, pandas.DataFrame]:
        """Runs every analysis.

        Returns:
            A dictionary of result tables by name: events, windows,
            table_1 is left to its own class, table_3 and table_4 on the
            winsorised data used by the regressions (with raw versions),
            table_5,
            figure_1, figure_2, figure_3, figure_4, figure_5 and
            tables_6_to_9.
        """
        events = self.sample_events()
        windows = event_window_builder.EventWindowBuilder(
            self.inputs.calendar,
            self.inputs.smile,
            self.inputs.ratios,
        ).build(events)
        study = event_study.EventStudy(windows)
        controls = controls_builder.ControlsBuilder(
            self.inputs.daily_returns,
            self.inputs.market_levels,
        )
        dataset = regression_dataset_builder.RegressionDatasetBuilder(
            windows,
            controls,
            self.inputs.calendar,
            self.inputs.shares,
        ).build(events)
        statistics = descriptive_statistics.DescriptiveStatistics()
        tables = regression_tables.RegressionTables(dataset)
        winsorised = tables.dataset
        results = {
            'events': events,
            'dataset': dataset,
            'table_3': statistics.summary(winsorised),
            'table_3_raw': statistics.summary(dataset),
            'table_4': statistics.correlations(winsorised).reset_index(
                names='variable',
            ),
            'table_4_raw': statistics.correlations(dataset).reset_index(
                names='variable',
            ),
            'table_5': month_comparison.MonthComparison(
                self.inputs.smile,
            ).table(events),
        }
        figure_one = []
        for column in (
            'atm_iv_normalised',
            'iv_75_normalised',
            'iv_25_normalised',
        ):
            series = study.mean_by_offset(column)
            series.insert(0, 'variable', column)
            figure_one.append(series)
        results['figure_1'] = pandas.concat(figure_one, ignore_index=True)
        for name, column in [
            ('figure_2', 'atm_iv_normalised'),
            ('figure_3', 'rr_iv'),
            ('figure_5', 'pc_contracts'),
        ]:
            results[name] = study.mean_by_tercile(column)
        results['figure_5_value'] = study.mean_by_tercile('pc_value')
        figure_four = []
        for column in ('os_ratio', 'of_ratio'):
            series = study.mean_by_offset(column)
            series.insert(0, 'variable', column)
            figure_four.append(series)
        results['figure_4'] = pandas.concat(figure_four, ignore_index=True)
        results['tables_6_to_9'] = tables.all_tables()
        results['tables_6_to_9_pc_value'] = tables.all_tables('pc_value')
        results['tables_6_to_9_sue_alternative'] = tables.all_tables(
            'pc_contracts',
            'sue_alternative',
        )
        return results
