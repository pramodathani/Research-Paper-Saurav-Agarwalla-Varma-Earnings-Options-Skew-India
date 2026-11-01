"""Runs the optional futures trading test on the real data."""

import pathlib

import pandas
from data_and_analytics.backtesting.costs import futures_costs

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    market_index_reader,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    event_trading_test,
    study_runner,
    trading_calendar,
)


class RunTradingTestApplication:
    """Command-line program that runs the trading test."""

    PERIODS = (
        ('2015-2019', '2015-01-01', '2019-12-31'),
        ('2020-Mar 2025', '2020-01-01', '2025-03-31'),
    )

    def run(self) -> None:
        """Runs three signals, two periods and two cost assumptions.

        Raises:
            FileNotFoundError: If a derived file is missing.
        """
        derived = pathlib.Path('data') / 'derived'
        dates = []
        futures = []
        for year in range(2009, 2026):
            cash = pandas.read_parquet(
                derived / f'cash_{year}.parquet',
                columns=['date'],
            )
            dates += list(cash['date'].dt.date.unique())
        for year in range(2014, 2026):
            table = pandas.read_parquet(
                derived / f'fno_{year}.parquet',
                columns=['date', 'symbol', 'kind', 'expiry', 'close'],
            )
            futures.append(table[table['kind'] == 'FUT'])
        futures = pandas.concat(futures, ignore_index=True)
        calendar = trading_calendar.TradingCalendar(dates)
        panel = pandas.read_parquet(derived / 'eps_panel.parquet')
        inputs = study_runner.StudyInputs(
            events=pandas.read_parquet(derived / 'events.parquet'),
            smile=pandas.read_parquet(derived / 'smile_main_2014_2025.parquet'),
            ratios=pandas.read_parquet(
                derived / 'volume_ratios_2014_2025.parquet',
            ),
            daily_returns=pandas.read_parquet(
                derived / 'daily_returns_2009_2025.parquet',
            ),
            market_levels=market_index_reader.MarketIndexReader().read(
                pathlib.Path('data') / 'niftyindices' / 'total_return',
            ),
            calendar=calendar,
            shares=panel[['symbol', 'broadcast', 'shares']],
        )
        runner = study_runner.StudyRunner(inputs, '2014-01-01', '2025-03-31')
        events = runner.sample_events()
        events = events.merge(
            pandas.read_parquet(derived / 'smile_main_2014_2025.parquet')[
                ['date', 'symbol', 'rr_iv']
            ].rename(columns={'date': 'day_before', 'rr_iv': 'rr_iv_1'}),
            on=['day_before', 'symbol'],
            how='left',
        )
        ratios = inputs.ratios[['date', 'symbol', 'pc_contracts']].rename(
            columns={'date': 'day_before', 'pc_contracts': 'pc_contracts_1'},
        )
        events = events.merge(ratios, on=['day_before', 'symbol'], how='left')
        test = event_trading_test.EventTradingTest(events, futures, calendar)
        returns = test.trade_returns()
        cost_models = {
            'STT 0.01% (rate in force to Sep 2024)': futures_costs.FuturesCosts(
                impact_cost=0.001,
                securities_transaction_tax_on_sells=0.0001,
            ),
            'STT 0.05% (library default, 2026 rate)': futures_costs.FuturesCosts(
                impact_cost=0.001,
            ),
        }
        rows = []
        for signal, percentile in test.signals().items():
            direction = test.positions(percentile)
            for period, first, last in self.PERIODS:
                for cost_name, cost_model in cost_models.items():
                    result = test.run_one(
                        signal,
                        direction,
                        returns,
                        cost_name,
                        cost_model,
                        first,
                        last,
                    )
                    rows.append(
                        {
                            'signal': signal,
                            'period': period,
                            'costs': cost_name,
                            'trades': result.trades,
                            'mean_trade_return': result.mean_trade_return,
                            'hit_rate': result.hit_rate,
                            'round_trip_cost': result.round_trip_cost,
                            'days': result.gross['periods'],
                            'gross_mean_daily': result.gross['mean'],
                            'gross_nw_t': result.gross['newey_west_t'],
                            'gross_annual': result.gross['compound_annual'],
                            'gross_max_drawdown': result.gross[
                                'maximum_drawdown'
                            ],
                            'net_mean_daily': result.net['mean'],
                            'net_nw_t': result.net['newey_west_t'],
                            'net_annual': result.net['compound_annual'],
                            'net_max_drawdown': result.net['maximum_drawdown'],
                            'net_sharpe': result.net['sharpe'],
                        },
                    )
        table = pandas.DataFrame(rows)
        table.to_csv(pathlib.Path('results') / 'trading_test.csv', index=False)
        print(table.round(4).to_string())


if __name__ == '__main__':
    RunTradingTestApplication().run()
