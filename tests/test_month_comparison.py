"""Tests for Table 5 on a made-up smile panel with known monthly means."""

import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    month_comparison,
)


class MonthComparisonTest(unittest.TestCase):
    """Two firms with ATM-IV of 0.30, 0.40 and 0.20 in the three months."""

    def setUp(self) -> None:
        """Builds twenty days a month for March to May 2017.

        Raises:
            AssertionError: Never.
        """
        rows = []
        for symbol, shift in [('AAA', 0.0), ('BBB', 0.02)]:
            for month, level in [(3, 0.30), (4, 0.40), (5, 0.20)]:
                for day in pandas.bdate_range(
                    f'2017-{month:02d}-01', periods=20
                ):
                    rows.append(
                        {
                            'date': day,
                            'symbol': symbol,
                            'atm_iv': level + shift,
                            'iv_75': level + shift + 0.01,
                            'iv_25': level + shift - 0.01,
                        },
                    )
        self.smile = pandas.DataFrame(rows)
        self.events = pandas.DataFrame(
            {
                'symbol': ['AAA', 'BBB', 'CCC'],
                'day0': pandas.to_datetime(['2017-04-10'] * 3),
            },
        )
        self.comparison = month_comparison.MonthComparison(self.smile)

    def test_event_means_pick_the_three_calendar_months(self) -> None:
        """Checks pre is March, EA is April and post is May.

        Raises:
            AssertionError: If a mean is wrong.
        """
        means = self.comparison.event_means(self.events)
        self.assertEqual(list(means.index), [0, 1])
        self.assertAlmostEqual(means.loc[0, 'atm_iv_pre'], 0.30)
        self.assertAlmostEqual(means.loc[0, 'atm_iv_ea'], 0.40)
        self.assertAlmostEqual(means.loc[1, 'atm_iv_post'], 0.22)

    def test_table_differences(self) -> None:
        """Checks the averages and differences against hand values.

        Raises:
            AssertionError: If a figure is wrong.
        """
        table = self.comparison.table(self.events).set_index('parameter')
        row = table.loc['atm_iv']
        self.assertAlmostEqual(row['pre'], 0.31)
        self.assertAlmostEqual(row['ea'], 0.41)
        self.assertAlmostEqual(row['post'], 0.21)
        self.assertAlmostEqual(row['ea_minus_pre'], 0.10)
        self.assertAlmostEqual(row['ea_minus_post'], 0.20)
        self.assertEqual(row['events'], 2.0)
        self.assertAlmostEqual(table.loc['iv_75', 'ea'], 0.42)

    def test_thin_month_drops_the_event(self) -> None:
        """Checks fewer than five days in a month removes the event.

        Raises:
            AssertionError: If the event stays.
        """
        thin = self.smile[
            ~(
                (self.smile['symbol'] == 'AAA')
                & (self.smile['date'].dt.month == 5)
                & (self.smile['date'].dt.day > 3)
            )
        ]
        comparison = month_comparison.MonthComparison(thin)
        means = comparison.event_means(self.events)
        self.assertEqual(list(means.index), [1])


if __name__ == '__main__':
    unittest.main()
