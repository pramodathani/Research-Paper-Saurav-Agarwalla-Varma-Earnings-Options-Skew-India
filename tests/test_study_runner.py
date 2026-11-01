"""End-to-end test of the whole study on a tiny made-up market."""

import unittest

import numpy
import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    study_runner,
    trading_calendar,
)


class StudyRunnerTest(unittest.TestCase):
    """Six shares over six years with eight quarterly announcements each.

    The surprise is built to depend positively on RR-IV and negatively on
    P/C the day before the announcement, so the study must find that.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Builds the inputs once and runs the study.

        Raises:
            AssertionError: Never.
        """
        generator = numpy.random.default_rng(11)
        days = pandas.bdate_range('2012-01-02', '2017-12-29')
        symbols = [f'S{index}' for index in range(6)]
        market = pandas.Series(
            100.0
            * numpy.cumprod(1.0 + generator.normal(0.0004, 0.01, len(days))),
            index=days,
        )
        calendar = trading_calendar.TradingCalendar(
            [day.date() for day in days],
        )
        returns_rows = []
        smile_rows = []
        ratio_rows = []
        market_returns = market.pct_change().fillna(0.0)
        for symbol in symbols:
            beta = generator.uniform(0.6, 1.6)
            price = 100.0
            for day in days:
                ret = beta * market_returns[day] + generator.normal(0.0, 0.01)
                price *= 1.0 + ret
                returns_rows.append(
                    {'date': day, 'symbol': symbol, 'close': price, 'ret': ret},
                )
        returns = pandas.DataFrame(returns_rows)
        event_rows = []
        planted = {}
        position = {day: index for index, day in enumerate(days)}
        for symbol in symbols:
            for quarter in range(8):
                day0 = days[
                    position[pandas.Timestamp('2016-02-15')] + quarter * 62
                ]
                rr = generator.normal(0.0, 0.03)
                pc = abs(generator.normal(0.45, 0.1))
                sue = 25.0 * rr - 3.0 * pc + generator.normal(0.0, 0.3)
                planted[(symbol, day0)] = (rr, pc)
                event_rows.append(
                    {
                        'symbol': symbol,
                        'day0': day0,
                        'expiry': pandas.Timestamp('2030-01-31'),
                        'keep': True,
                        'sue': sue,
                        'sue_alternative': sue,
                    },
                )
        for symbol in symbols:
            for day in days:
                smile_rows.append(
                    {
                        'date': day,
                        'symbol': symbol,
                        'expiry': pandas.Timestamp('2030-01-31'),
                        'atm_iv': 0.30 + generator.normal(0.0, 0.02),
                        'iv_75': 0.31,
                        'iv_25': 0.29,
                        'rr_iv': generator.normal(0.0, 0.01),
                        'alt_atm_iv': 0.30,
                        'alt_rr_iv': generator.normal(0.0, 0.01),
                    },
                )
                ratio_rows.append(
                    {
                        'date': day,
                        'symbol': symbol,
                        'os_ratio': 1.0,
                        'of_ratio': 0.5,
                        'pc_contracts': 0.45,
                        'pc_value': 0.45,
                    },
                )
        smile = pandas.DataFrame(smile_rows)
        ratios = pandas.DataFrame(ratio_rows)
        for (symbol, day0), (rr, pc) in planted.items():
            before = days[position[day0] - 1]
            mask = (smile['symbol'] == symbol) & (smile['date'] == before)
            smile.loc[mask, 'rr_iv'] = rr
            smile.loc[mask, 'alt_rr_iv'] = rr
            mask = (ratios['symbol'] == symbol) & (ratios['date'] == before)
            ratios.loc[mask, 'pc_contracts'] = pc
            ratios.loc[mask, 'pc_value'] = pc
        shares = pandas.DataFrame(
            {
                'symbol': symbols,
                'broadcast': pandas.Timestamp('2012-06-01'),
                'shares': 5.0e7,
            },
        )
        inputs = study_runner.StudyInputs(
            events=pandas.DataFrame(event_rows),
            smile=smile,
            ratios=ratios,
            daily_returns=returns,
            market_levels=market,
            calendar=calendar,
            shares=shares,
        )
        cls.results = study_runner.StudyRunner(
            inputs,
            '2016-01-01',
            '2017-12-31',
        ).run()

    def test_sample_has_every_event(self) -> None:
        """Checks all 48 events are in the sample.

        Raises:
            AssertionError: If the count is wrong.
        """
        self.assertEqual(len(self.results['events']), 48)
        self.assertEqual(len(self.results['dataset']), 48)

    def test_figure_series_have_twenty_one_offsets(self) -> None:
        """Checks the figure tables span days -10 to +10.

        Raises:
            AssertionError: If the offsets are wrong.
        """
        figure = self.results['figure_4']
        offsets = sorted(figure['offset'].unique())
        self.assertEqual(offsets, list(range(-10, 11)))
        self.assertEqual(
            sorted(self.results['figure_3']['tercile'].unique()), [1, 2, 3]
        )

    def test_table_five_and_descriptives_exist(self) -> None:
        """Checks Tables 3, 4 and 5 are filled in.

        Raises:
            AssertionError: If a table is empty.
        """
        self.assertEqual(len(self.results['table_5']), 3)
        self.assertGreater(len(self.results['table_3']), 5)
        self.assertEqual(len(self.results['table_4']), 10)

    def test_regression_finds_the_planted_signal(self) -> None:
        """Checks RR-IV is positive and P/C negative in Table 6 column (1).

        Raises:
            AssertionError: If the planted signs are not found.
        """
        table = self.results['tables_6_to_9']
        rows = table[(table['table'] == 'Table 6') & (table['column'] == '(1)')]
        rows = rows.set_index('variable')
        self.assertGreater(rows.loc['RR-IV', 'coefficient'], 10.0)
        self.assertLess(rows.loc['P/C', 'coefficient'], -1.0)
        self.assertGreater(rows.loc['RR-IV', 't_statistic'], 4.0)
        self.assertLess(rows.loc['P/C', 't_statistic'], -2.0)

    def test_later_lags_are_not_the_planted_ones(self) -> None:
        """Checks day -2 does not show the day -1 signal.

        Raises:
            AssertionError: If RR-IV at day -2 is strongly significant.
        """
        table = self.results['tables_6_to_9']
        rows = table[(table['table'] == 'Table 7') & (table['column'] == 'n=2')]
        rows = rows.set_index('variable')
        self.assertLess(abs(rows.loc['RR-IV', 't_statistic']), 3.0)


if __name__ == '__main__':
    unittest.main()
