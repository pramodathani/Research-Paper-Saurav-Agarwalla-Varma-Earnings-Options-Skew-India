"""Lines up each event's smile and volume ratios on days -10 to +10."""

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    trading_calendar,
)


class EventWindowBuilder:
    """Builds the long table of event days used by tables and figures."""

    SMILE_COLUMNS = (
        'atm_iv',
        'iv_75',
        'iv_25',
        'rr_iv',
        'alt_atm_iv',
        'alt_rr_iv',
    )
    RATIO_COLUMNS = ('os_ratio', 'of_ratio', 'pc_contracts', 'pc_value')
    LEVEL_COLUMNS = ('atm_iv', 'iv_75', 'iv_25')
    MIN_BASE_DAYS = 5

    def __init__(
        self,
        calendar: trading_calendar.TradingCalendar,
        smile: pandas.DataFrame,
        ratios: pandas.DataFrame,
    ) -> None:
        """Stores the calendar and the two daily panels.

        Args:
            calendar: The trading calendar.
            smile: The stock-day smile panel.
            ratios: The stock-day volume ratio table.
        """
        self.calendar = calendar
        self.smile = smile
        self.ratios = ratios
        self.base = self.monthly_base()

    def monthly_base(self) -> pandas.DataFrame:
        """Averages each smile level over every share-month.

        Returns:
            A table indexed by symbol and month with the mean of each level
            and the number of days, for the normalisation of Table 2.
        """
        frame = self.smile.assign(month=self.smile['date'].dt.to_period('M'))
        grouped = frame.groupby(['symbol', 'month'])
        base = grouped[list(self.LEVEL_COLUMNS)].mean()
        base.columns = [f'base_{name}' for name in base.columns]
        base['base_days'] = grouped.size()
        return base

    def offset_dates(
        self,
        events: pandas.DataFrame,
        offsets: range,
    ) -> pandas.DataFrame:
        """Finds the trading date at each offset from day 0.

        Args:
            events: Events with an event_id and day0.
            offsets: The offsets in trading days.

        Returns:
            One row per event and offset with the date, NaT when the date
            lies outside the calendar.
        """
        dates = numpy.array(self.calendar.dates, dtype='datetime64[ns]')
        position = numpy.searchsorted(dates, events['day0'].to_numpy())
        rows = []
        for offset in offsets:
            target = position + offset
            valid = (target >= 0) & (target < len(dates))
            chosen = numpy.where(valid, target, 0)
            frame = pandas.DataFrame(
                {
                    'event_id': events['event_id'].to_numpy(),
                    'offset': offset,
                    'date': numpy.where(
                        valid, dates[chosen], numpy.datetime64('NaT', 'ns')
                    ),
                },
            )
            rows.append(frame)
        return pandas.concat(rows, ignore_index=True)

    def build(
        self,
        events: pandas.DataFrame,
        first_offset: int = -10,
        last_offset: int = 10,
    ) -> pandas.DataFrame:
        """Builds the event-day table.

        Args:
            events: Kept events with symbol, day0 and sue columns.
            first_offset: The first offset in trading days.
            last_offset: The last offset in trading days.

        Returns:
            One row per event and offset, with raw and normalised smile
            levels, volume ratios and the event's surprise.
        """
        events = events.reset_index(drop=True).assign(
            event_id=lambda frame: frame.index,
        )
        table = self.offset_dates(events, range(first_offset, last_offset + 1))
        table = table.dropna(subset=['date'])
        table = table.merge(
            events[['event_id', 'symbol', 'day0', 'sue', 'sue_alternative']],
            on='event_id',
        )
        smile = self.smile[['date', 'symbol', *self.SMILE_COLUMNS, 'expiry']]
        table = table.merge(smile, on=['date', 'symbol'], how='left')
        ratios = self.ratios[['date', 'symbol', *self.RATIO_COLUMNS]]
        table = table.merge(ratios, on=['date', 'symbol'], how='left')
        previous = table['day0'].dt.to_period('M') - 1
        keys = pandas.MultiIndex.from_arrays([table['symbol'], previous])
        base = self.base.reindex(keys)
        base.index = table.index
        usable = base['base_days'] >= self.MIN_BASE_DAYS
        for name in self.LEVEL_COLUMNS:
            table[f'{name}_normalised'] = table[name] / base[
                f'base_{name}'
            ].where(
                usable,
            )
        return table
