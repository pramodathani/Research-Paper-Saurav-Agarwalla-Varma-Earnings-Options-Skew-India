"""Tests for near-month selection in the smile panel builder."""

import pathlib
import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    black76,
    smile_panel_builder,
)


class FlatRates:
    """A risk-free rate lookup that always returns zero."""

    def rate(self, date: pandas.Timestamp) -> float:
        """Returns zero.

        Args:
            date: Any date.

        Returns:
            0.0.
        """
        return 0.0


class SmilePanelBuilderTest(unittest.TestCase):
    """Builds a market with two expiries and checks which is used."""

    NEAR = pandas.Timestamp('2017-07-27')
    FAR = pandas.Timestamp('2017-08-31')

    def rows(
        self,
        date: str,
        symbol: str,
        expiry: pandas.Timestamp,
        volatility: float,
        with_future: bool = True,
    ) -> list[dict]:
        """Makes one expiry's future and option rows for a stock-day.

        Args:
            date: The trading date.
            symbol: The symbol.
            expiry: The expiry date.
            volatility: The flat volatility used to price the options.
            with_future: Whether the future traded.

        Returns:
            Rows in the F&O reader's layout.
        """
        stamp = pandas.Timestamp(date)
        years = (expiry - stamp).days / 365.0
        if years <= 0:
            return []
        strikes = numpy.arange(90.0, 110.1, 2.5)
        is_call = strikes >= 100.0
        price = black76.Black76(0.0).price(
            100.0,
            strikes,
            years,
            volatility,
            is_call,
        )
        rows = []
        if with_future:
            rows.append(self.row(stamp, symbol, 'FUT', expiry, 0.0, '', 100.0))
        for strike, call, premium in zip(strikes, is_call, price, strict=True):
            option_type = 'CE' if call else 'PE'
            rows.append(
                self.row(
                    stamp,
                    symbol,
                    'OPT',
                    expiry,
                    strike,
                    option_type,
                    premium,
                ),
            )
        return rows

    def row(self, date, symbol, kind, expiry, strike, option_type, price):
        """Builds one row of the F&O table.

        Args:
            date: The trading date.
            symbol: The symbol.
            kind: FUT or OPT.
            expiry: The expiry date.
            strike: The strike.
            option_type: CE, PE or an empty string.
            price: The close and settle price.

        Returns:
            The row as a dictionary.
        """
        return {
            'date': date,
            'symbol': symbol,
            'kind': kind,
            'expiry': expiry,
            'strike': strike,
            'option_type': option_type,
            'close': price,
            'settle': price,
            'contracts': 50,
            'value_rupees': 1.0e7,
            'open_interest': 100,
            'lot_size': float('nan'),
            'underlying_price': float('nan'),
        }

    def test_uses_the_nearest_later_expiry(self) -> None:
        """Checks the near series is used before expiry and the far one on it.

        Raises:
            AssertionError: If the wrong expiry is used.
        """
        data = []
        for date in ['2017-07-20', '2017-07-27']:
            data += self.rows(date, 'AAA', self.NEAR, 0.20)
            data += self.rows(date, 'AAA', self.FAR, 0.40)
        builder = smile_panel_builder.SmilePanelBuilder(pathlib.Path('.'))
        panel = builder.build_frame(pandas.DataFrame(data), FlatRates())
        panel = panel.set_index('date')
        before = panel.loc[pandas.Timestamp('2017-07-20')]
        on_expiry = panel.loc[pandas.Timestamp('2017-07-27')]
        self.assertEqual(before['expiry'], self.NEAR)
        self.assertAlmostEqual(before['atm_iv'], 0.20, places=2)
        self.assertEqual(before['calendar_days_to_expiry'], 7)
        self.assertEqual(on_expiry['expiry'], self.FAR)
        self.assertAlmostEqual(on_expiry['atm_iv'], 0.40, places=2)

    def test_symbol_without_future_is_skipped(self) -> None:
        """Checks a stock whose future did not trade gets no smile.

        Raises:
            AssertionError: If a row is produced.
        """
        data = self.rows('2017-07-20', 'AAA', self.NEAR, 0.2, False)
        builder = smile_panel_builder.SmilePanelBuilder(pathlib.Path('.'))
        panel = builder.build_frame(pandas.DataFrame(data), FlatRates())
        self.assertTrue(panel.empty)

    def test_two_symbols_are_kept_apart(self) -> None:
        """Checks each symbol gets its own smile.

        Raises:
            AssertionError: If the symbols are mixed.
        """
        data = self.rows('2017-07-20', 'AAA', self.NEAR, 0.20)
        data += self.rows('2017-07-20', 'BBB', self.NEAR, 0.35)
        builder = smile_panel_builder.SmilePanelBuilder(pathlib.Path('.'))
        panel = builder.build_frame(pandas.DataFrame(data), FlatRates())
        panel = panel.set_index('symbol')
        self.assertAlmostEqual(panel.loc['AAA', 'atm_iv'], 0.20, places=2)
        self.assertAlmostEqual(panel.loc['BBB', 'atm_iv'], 0.35, places=2)


if __name__ == '__main__':
    unittest.main()
