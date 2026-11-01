"""An optional test: trade stock futures on the day-before smile signal."""

import dataclasses

import numpy
import pandas
from data_and_analytics.backtesting import backtest, performance_report
from data_and_analytics.backtesting.costs import futures_costs

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    trading_calendar,
)


@dataclasses.dataclass
class TradingResult:
    """The outcome of one signal under one cost assumption.

    Attributes:
        signal: The signal's name.
        costs: The cost assumption's name.
        trades: The number of trades.
        mean_trade_return: The mean return per trade, before costs.
        hit_rate: The share of trades that made money before costs.
        gross: Performance of the daily return series before costs.
        net: Performance of the daily return series after costs.
        round_trip_cost: The mean cost of one round trip, as a fraction.
    """

    signal: str
    costs: str
    trades: int
    mean_trade_return: float
    hit_rate: float
    gross: dict
    net: dict
    round_trip_cost: float


class EventTradingTest:
    """Longs and shorts stock futures from the close of day -1 to day 0."""

    LOOKBACK_DAYS = 365
    MINIMUM_HISTORY = 150
    LONG_PERCENTILE = 2.0 / 3.0
    SHORT_PERCENTILE = 1.0 / 3.0
    POSITION_SIZE = 0.02
    PERIODS_PER_YEAR = 250
    LARGEST_PLAUSIBLE_MOVE = 0.5

    def __init__(
        self,
        events: pandas.DataFrame,
        futures: pandas.DataFrame,
        calendar: trading_calendar.TradingCalendar,
    ) -> None:
        """Stores the events, futures prices and calendar.

        Args:
            events: Sample events in the order of the regression dataset,
                with symbol, day0, expiry, rr_iv_1 and pc_contracts_1.
            futures: Stock futures rows with date, symbol, expiry and close.
            calendar: The trading calendar.
        """
        self.events = events.reset_index(drop=True)
        self.calendar = calendar
        self.close = {
            (row.symbol, row.expiry, row.date): row.close
            for row in futures.itertuples()
        }

    def trade_returns(self) -> pandas.Series:
        """Finds each event's futures return from day -1 close to day 0 close.

        The same expiry's contract is used on both days, so the return is
        a true price change and not a roll. A move beyond 50 percent is
        taken to be an unadjusted corporate action and left out, as with
        IGL on 9 November 2017, whose future fell 80 percent while the
        share fell 1 percent.

        Returns:
            One return per event, NaN where either price is missing.
        """
        values = []
        for row in self.events.itertuples():
            before = self.calendar.shift(row.day0.date(), -1)
            if before is None:
                values.append(numpy.nan)
                continue
            key = (row.symbol, row.expiry)
            start = self.close.get((*key, pandas.Timestamp(before)))
            end = self.close.get((*key, row.day0))
            if start is None or end is None or start <= 0:
                values.append(numpy.nan)
                continue
            change = end / start - 1.0
            if abs(change) > self.LARGEST_PLAUSIBLE_MOVE:
                values.append(numpy.nan)
            else:
                values.append(change)
        return pandas.Series(values, index=self.events.index)

    def trailing_percentile(self, score: pandas.Series) -> pandas.Series:
        """Ranks each event's score among the previous year's events.

        Only events announced strictly earlier than the event, within the
        last 365 days, are used, so no event sees its own or later scores.

        Args:
            score: One score per event, higher meaning more bullish.

        Returns:
            The share of earlier events with a lower score, NaN when fewer
            than 150 earlier events exist.
        """
        days = self.events['day0'].to_numpy()
        values = score.to_numpy(dtype=float)
        result = numpy.full(len(values), numpy.nan)
        window = numpy.timedelta64(self.LOOKBACK_DAYS, 'D')
        for position in range(len(values)):
            current = days[position]
            if numpy.isnan(values[position]):
                continue
            mask = (days < current) & (days >= current - window)
            history = values[mask]
            history = history[~numpy.isnan(history)]
            if len(history) < self.MINIMUM_HISTORY:
                continue
            result[position] = float((history < values[position]).mean())
        return pandas.Series(result, index=self.events.index)

    def signals(self) -> dict[str, pandas.Series]:
        """Builds the three signals as trailing percentiles.

        Returns:
            RR-IV alone, minus P/C alone, and the mean of the two.
        """
        skew = self.trailing_percentile(self.events['rr_iv_1'])
        puts = self.trailing_percentile(-self.events['pc_contracts_1'])
        return {
            'RR-IV': skew,
            'P/C': puts,
            'RR-IV and P/C': (skew + puts) / 2.0,
        }

    def positions(self, percentile: pandas.Series) -> pandas.Series:
        """Turns a percentile into +1 (long), -1 (short) or 0.

        Args:
            percentile: A trailing percentile per event.

        Returns:
            The direction of each event's trade.
        """
        direction = pandas.Series(0.0, index=percentile.index)
        direction[percentile >= self.LONG_PERCENTILE] = 1.0
        direction[percentile <= self.SHORT_PERCENTILE] = -1.0
        return direction

    def run_one(
        self,
        name: str,
        direction: pandas.Series,
        returns: pandas.Series,
        cost_name: str,
        cost_model: futures_costs.FuturesCosts,
        first_date: str,
        last_date: str,
    ) -> TradingResult:
        """Backtests one signal with the shared engine.

        Args:
            name: The signal's name.
            direction: +1, -1 or 0 per event.
            returns: Each event's futures return.
            cost_name: The cost assumption's name.
            cost_model: The futures cost model.
            first_date: The first trading day to score.
            last_date: The last trading day to score.

        Returns:
            The result for the signal.
        """
        mask = (
            (direction != 0)
            & returns.notna()
            & (self.events['day0'] >= pandas.Timestamp(first_date))
            & (self.events['day0'] <= pandas.Timestamp(last_date))
        )
        trades = self.events[mask]
        dates = [
            pandas.Timestamp(day)
            for day in self.calendar.dates
            if pandas.Timestamp(first_date)
            <= pandas.Timestamp(day)
            <= pandas.Timestamp(last_date)
        ]
        symbols = sorted(trades['symbol'].unique())
        panel = pandas.DataFrame(numpy.nan, index=dates, columns=symbols)
        weights = pandas.DataFrame(0.0, index=dates, columns=symbols)
        for index, row in trades.iterrows():
            panel.loc[row['day0'], row['symbol']] = returns[index]
            weights.loc[row['day0'], row['symbol']] += (
                self.POSITION_SIZE * direction[index]
            )
        result = backtest.Backtest(panel, weights, cost_model).run()
        gross = self.score(result.gross_returns, dates)
        net = self.score(result.net_returns, dates)
        signed = returns[mask] * direction[mask]
        costs = result.costs.dropna()
        traded = (
            result.bought.add(result.sold).where(result.costs.notna()).dropna()
        )
        round_trip = (
            float(costs.sum() / traded.sum() * 2.0) if traded.sum() else 0.0
        )
        return TradingResult(
            signal=name,
            costs=cost_name,
            trades=int(mask.sum()),
            mean_trade_return=float(signed.mean()),
            hit_rate=float((signed > 0).mean()),
            gross=gross,
            net=net,
            round_trip_cost=round_trip,
        )

    def score(self, returns: pandas.Series, dates: list) -> dict:
        """Scores a daily series, counting days without trades as zero.

        Args:
            returns: Daily returns with NaN on days with no position.
            dates: Every trading day of the period.

        Returns:
            The performance report's summary.
        """
        filled = returns.reindex(dates).fillna(0.0)
        report = performance_report.PerformanceReport(
            filled,
            periods_per_year=self.PERIODS_PER_YEAR,
        )
        return report.summary()
