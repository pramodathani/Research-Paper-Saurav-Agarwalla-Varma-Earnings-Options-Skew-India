"""Builds daily total returns from raw bhavcopy closes."""

import numpy
import pandas


class AdjustedReturnBuilder:
    """Adjusts each day's return for splits, bonuses and dividends."""

    LOWEST_PLAUSIBLE = -0.5
    HIGHEST_PLAUSIBLE = 1.0

    def build(
        self,
        cash: pandas.DataFrame,
        actions: pandas.DataFrame,
    ) -> pandas.DataFrame:
        """Computes the daily return of every share.

        The return on a day is (close + dividend) / (previous close times
        the day's split and bonus factor) minus one. An action whose ex-date
        is not a trading day is applied on the next trading day of that
        share. Moves below -50% or above +100% are treated as missed
        corporate actions and set to zero, and they are flagged.

        Args:
            cash: Rows from the cash bhavcopy reader.
            actions: Corporate actions with symbol, ex_date, kind and value.

        Returns:
            Rows with date, symbol, close, ret and extreme, sorted by symbol
            and date. One row per share and day, preferring series EQ.
        """
        ordered = cash.assign(
            rank=numpy.where(cash['series'] == 'EQ', 0, 1),
        ).sort_values(['symbol', 'date', 'rank'])
        table = ordered.drop_duplicates(['symbol', 'date']).copy()
        table['factor'] = 1.0
        table['dividend'] = 0.0
        table = self.apply_actions(table, actions)
        base = table['previous_close'] * table['factor']
        raw = (table['close'] + table['dividend']) / base - 1.0
        extreme = (raw < self.LOWEST_PLAUSIBLE) | (raw > self.HIGHEST_PLAUSIBLE)
        table['extreme'] = extreme
        table['ret'] = raw.where(~extreme, 0.0)
        table.loc[table['previous_close'] <= 0, 'ret'] = numpy.nan
        columns = ['date', 'symbol', 'close', 'ret', 'extreme']
        return table[columns].reset_index(drop=True)

    def apply_actions(
        self,
        table: pandas.DataFrame,
        actions: pandas.DataFrame,
    ) -> pandas.DataFrame:
        """Puts each action on the first trading day on or after its ex-date.

        Args:
            table: Daily rows with symbol, date, factor and dividend.
            actions: Corporate actions.

        Returns:
            The table with the factor and dividend columns filled in.
        """
        dates_by_symbol = {
            symbol: group['date'].to_numpy()
            for symbol, group in table.groupby('symbol')
        }
        index_by_symbol = {
            symbol: group.index.to_numpy()
            for symbol, group in table.groupby('symbol')
        }
        for action in actions.itertuples():
            dates = dates_by_symbol.get(action.symbol)
            if dates is None:
                continue
            ex_date = action.ex_date.to_datetime64()
            if ex_date < dates[0]:
                continue
            position = numpy.searchsorted(dates, ex_date)
            if position >= len(dates):
                continue
            row = index_by_symbol[action.symbol][position]
            if action.kind == 'factor':
                table.loc[row, 'factor'] *= action.value
            else:
                table.loc[row, 'dividend'] += action.value
        return table
