"""Builds the daily O/S, O/F and P/C volume ratios for each share."""

import pathlib

import numpy
import pandas


class VolumeRatioBuilder:
    """Sums option and future trading over all expiries for each stock-day."""

    def build_frame(
        self,
        derivatives: pandas.DataFrame,
        cash: pandas.DataFrame,
    ) -> pandas.DataFrame:
        """Computes the ratios for every stock-day with options.

        The options volume is notional rupees, (strike plus premium) times
        the quantity traded, because that is what the bhavcopy reports and
        it puts options on the same footing as stock and futures turnover.
        O/S is options over stock turnover, O/F is options over futures
        turnover, and P/C is put over call volume, in contracts and in
        notional rupees.

        Args:
            derivatives: Rows from the F&O reader.
            cash: Rows from the cash bhavcopy reader.

        Returns:
            One row per date and symbol with the sums and the ratios.
        """
        options = derivatives[derivatives['kind'] == 'OPT']
        futures = derivatives[derivatives['kind'] == 'FUT']
        keys = ['date', 'symbol']
        calls = options[options['option_type'] == 'CE']
        puts = options[options['option_type'] == 'PE']
        table = pandas.DataFrame(
            {
                'option_notional': options.groupby(keys)['value_rupees'].sum(),
                'call_notional': calls.groupby(keys)['value_rupees'].sum(),
                'put_notional': puts.groupby(keys)['value_rupees'].sum(),
                'call_contracts': calls.groupby(keys)['contracts'].sum(),
                'put_contracts': puts.groupby(keys)['contracts'].sum(),
            },
        )
        table['future_notional'] = futures.groupby(keys)['value_rupees'].sum()
        table = table.fillna({'call_contracts': 0, 'put_contracts': 0})
        table = table.fillna(
            {'call_notional': 0.0, 'put_notional': 0.0},
        )
        stock = self.stock_value(cash)
        table = table.join(stock, how='left').reset_index()
        table['os_ratio'] = table['option_notional'] / self.nonzero(
            table['stock_value'],
        )
        table['of_ratio'] = table['option_notional'] / self.nonzero(
            table['future_notional'],
        )
        table['pc_contracts'] = table['put_contracts'] / self.nonzero(
            table['call_contracts'],
        )
        table['pc_value'] = table['put_notional'] / self.nonzero(
            table['call_notional'],
        )
        return table

    def stock_value(self, cash: pandas.DataFrame) -> pandas.Series:
        """Returns each share's daily turnover, preferring series EQ.

        Args:
            cash: Rows from the cash bhavcopy reader.

        Returns:
            Turnover in rupees indexed by date and symbol.
        """
        ordered = cash.assign(
            rank=numpy.where(cash['series'] == 'EQ', 0, 1),
        ).sort_values(['date', 'symbol', 'rank'])
        first = ordered.drop_duplicates(['date', 'symbol'])
        return first.set_index(['date', 'symbol'])['value_rupees'].rename(
            'stock_value',
        )

    def nonzero(self, values: pandas.Series) -> pandas.Series:
        """Replaces zeros by NaN so a division gives NaN, not infinity.

        Args:
            values: A numeric series.

        Returns:
            The series with zeros replaced by NaN.
        """
        return values.where(values > 0)

    def build(
        self,
        data_folder: pathlib.Path,
        first_year: int,
        last_year: int,
    ) -> pandas.DataFrame:
        """Builds the ratios for a range of years from the yearly stores.

        Args:
            data_folder: The study's data folder.
            first_year: The first year.
            last_year: The last year.

        Returns:
            The ratio table for all the years.
        """
        pieces = []
        for year in range(first_year, last_year + 1):
            derivatives = pandas.read_parquet(
                data_folder / 'derived' / f'fno_{year}.parquet',
            )
            cash = pandas.read_parquet(
                data_folder / 'derived' / f'cash_{year}.parquet',
            )
            pieces.append(self.build_frame(derivatives, cash))
        return pandas.concat(pieces, ignore_index=True)
