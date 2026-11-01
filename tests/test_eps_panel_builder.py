"""Tests for the EPS panel builder on small made-up tables."""

import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    eps_panel_builder,
)


class EpsPanelBuilderTest(unittest.TestCase):
    """Checks re-filing selection, split adjustment and SUE assembly."""

    def setUp(self) -> None:
        """Creates a builder.

        Raises:
            AssertionError: Never.
        """
        self.builder = eps_panel_builder.EpsPanelBuilder(None)

    def test_select_earliest_keeps_first_broadcast(self) -> None:
        """Checks a later re-filing of the same quarter is dropped.

        Raises:
            AssertionError: If the wrong filing is kept.
        """
        targets = [
            {
                'symbol': 'AAA',
                'to_date': '31-Mar-2019',
                'broadcast': '04-Sep-2019 18:34:57',
                'url': 'late',
            },
            {
                'symbol': 'AAA',
                'to_date': '31-Mar-2019',
                'broadcast': '06-May-2019 08:02:19',
                'url': 'early',
            },
            {
                'symbol': 'AAA',
                'to_date': '30-Jun-2019',
                'broadcast': '12-Jul-2019 16:32:10',
                'url': 'next',
            },
        ]
        kept = self.builder.select_earliest(targets)
        urls = sorted(target['url'] for target in kept)
        self.assertEqual(urls, ['early', 'next'])

    def test_adjustment_uses_only_later_actions(self) -> None:
        """Checks only actions after the announcement scale the EPS.

        Raises:
            AssertionError: If a factor is wrong.
        """
        panel = pandas.DataFrame(
            {
                'symbol': ['AAA', 'AAA', 'BBB'],
                'broadcast': pandas.to_datetime(
                    [
                        '2014-10-20 10:00',
                        '2015-10-20 10:00',
                        '2014-10-20 00:00',
                    ],
                ),
            },
        )
        actions = pandas.DataFrame(
            {
                'symbol': ['AAA', 'AAA', 'AAA'],
                'ex_date': pandas.to_datetime(
                    ['2014-12-02', '2015-06-15', '2016-01-01'],
                ),
                'kind': ['factor', 'factor', 'dividend'],
                'value': [0.5, 0.5, 3.0],
            },
        )
        factors = self.builder.adjustment_factors(panel, actions)
        self.assertEqual(list(factors), [0.25, 1.0, 1.0])

    def test_sue_table_per_firm(self) -> None:
        """Checks SUE is computed per firm and kept apart between firms.

        Raises:
            AssertionError: If SUE leaks across firms.
        """
        quarters = pandas.date_range('2010-03-31', periods=24, freq='QE')
        rows = []
        for symbol, shock in [('AAA', 3.0), ('BBB', 0.0)]:
            for number, period_end in enumerate(quarters):
                value = float(number) + (shock if number == 22 else 0.0)
                rows.append(
                    {
                        'symbol': symbol,
                        'period_end': period_end,
                        'adjusted_eps': value,
                    },
                )
        table = self.builder.sue_table(pandas.DataFrame(rows))
        last_a = table[
            (table['symbol'] == 'AAA') & (table['period_end'] == quarters[23])
        ]
        last_b = table[
            (table['symbol'] == 'BBB') & (table['period_end'] == quarters[23])
        ]
        self.assertAlmostEqual(last_a['sue'].iloc[0], -0.375 / 1.125**0.5)
        self.assertTrue(pandas.isna(last_b['sue'].iloc[0]))


if __name__ == '__main__':
    unittest.main()
