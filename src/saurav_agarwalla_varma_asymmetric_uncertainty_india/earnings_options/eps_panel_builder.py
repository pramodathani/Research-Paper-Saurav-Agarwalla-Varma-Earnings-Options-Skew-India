"""Builds each firm's quarterly EPS history and its SUE."""

import datetime
import pathlib

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    corporate_action_reader,
    results_filing_downloader,
    results_filing_parser,
    results_filing_targets,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    sue_calculator,
)


class EpsPanelBuilder:
    """Joins filings, announcement times, corporate actions and SUE."""

    MIN_SHARES = 1e6
    MAX_SHARES = 5e10

    def __init__(self, data_folder: pathlib.Path) -> None:
        """Remembers the study's data folder.

        Args:
            data_folder: The study's data folder.
        """
        self.data_folder = data_folder
        self.calculator = sue_calculator.SueCalculator()

    def select_earliest(
        self,
        targets: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Keeps the first broadcast of each symbol and period end.

        Later rows for the same quarter are re-filings, such as a restated
        result, and the market reacted to the first one.

        Args:
            targets: Filing targets with symbol, to_date and broadcast.

        Returns:
            One target per symbol and period end.
        """
        best: dict[tuple[str, str], tuple[datetime.datetime, dict]] = {}
        for target in targets:
            stamp = datetime.datetime.strptime(
                target['broadcast'],
                '%d-%b-%Y %H:%M:%S',
            )
            key = (target['symbol'], target['to_date'])
            if key not in best or stamp < best[key][0]:
                best[key] = (stamp, target)
        return [pair[1] for pair in best.values()]

    def adjustment_factors(
        self,
        panel: pandas.DataFrame,
        actions: pandas.DataFrame,
    ) -> pandas.Series:
        """Finds, for each filing, the product of later split and bonus factors.

        Multiplying a quarter's EPS by this puts it on the share basis after
        every split and bonus whose ex-date came after its announcement.

        Args:
            panel: Rows with symbol and broadcast.
            actions: Corporate actions with symbol, ex_date, kind and value.

        Returns:
            One factor per row of the panel, 1.0 when none applies.
        """
        factors = actions[actions['kind'] == 'factor']
        by_symbol = {
            symbol: group.sort_values('ex_date')
            for symbol, group in factors.groupby('symbol')
        }
        result = []
        for symbol, broadcast in zip(
            panel['symbol'],
            panel['broadcast'],
            strict=True,
        ):
            product = 1.0
            group = by_symbol.get(symbol)
            if group is not None:
                later = group[group['ex_date'] > broadcast.normalize()]
                for value in later['value']:
                    product *= value
            result.append(product)
        return pandas.Series(result, index=panel.index)

    def sue_table(self, panel: pandas.DataFrame) -> pandas.DataFrame:
        """Computes SUE for every firm's quarters.

        Args:
            panel: Rows with symbol, period_end and adjusted_eps.

        Returns:
            The panel with expected EPS, surprise, sigma, sue and
            sue_alternative added.
        """
        pieces = []
        for _, group in panel.groupby('symbol'):
            group = group.copy()
            group['quarter'] = self.calculator.quarter_index(
                group['period_end'],
            )
            group = group.drop_duplicates('quarter').sort_values('quarter')
            table = self.calculator.compute(
                group.set_index('quarter')['adjusted_eps'],
            )
            group = group.set_index('quarter').join(
                table[
                    [
                        'expected',
                        'surprise',
                        'sigma',
                        'sue',
                        'sue_alternative',
                    ]
                ],
            )
            pieces.append(group.reset_index())
        return pandas.concat(pieces, ignore_index=True)

    def use_announcement_times(
        self,
        panel: pandas.DataFrame,
        announcements: pandas.DataFrame,
    ) -> pandas.DataFrame:
        """Replaces the results API's broadcast time by the announcement time.

        The results API time is the time of the structured filing, which can
        come weeks after the results were announced. The announcement of the
        results on NSE's announcement feed is what the paper dates events by.
        An announcement is used when it is for the same symbol and period, is
        not before the period ended and is not more than a day after the
        structured filing. Otherwise the API time is kept.

        Args:
            panel: Rows with symbol, period_end and broadcast.
            announcements: One row per symbol and period end with announced.

        Returns:
            The panel with broadcast replaced where an announcement matched,
            results_broadcast holding the original and time_source saying
            which was used.
        """
        merged = panel.merge(
            announcements[['symbol', 'period_end', 'announced']],
            on=['symbol', 'period_end'],
            how='left',
        )
        merged['results_broadcast'] = merged['broadcast']
        late = merged['announced'] > merged['broadcast'] + pandas.Timedelta(
            days=1
        )
        early = merged['announced'] < merged['period_end']
        usable = merged['announced'].notna() & ~late & ~early
        merged['broadcast'] = merged['announced'].where(
            usable, merged['broadcast']
        )
        merged['time_source'] = usable.map(
            {True: 'announcement', False: 'results_api'},
        )
        return merged.drop(columns=['announced'])

    def build(
        self,
        ranges_path: pathlib.Path,
        announcements: pandas.DataFrame | None = None,
    ) -> pandas.DataFrame:
        """Builds the panel for every stock-futures share.

        Args:
            ranges_path: The JSON of futures date ranges by symbol.
            announcements: The first results announcement of each symbol
                and period, or None to keep the results API times.

        Returns:
            One row per symbol and quarter with the first broadcast time,
            EPS, adjusted EPS, shares outstanding and SUE.
        """
        targets = results_filing_targets.ResultsFilingTargets(
            self.data_folder,
        ).build(ranges_path)
        chosen = self.select_earliest(targets)
        downloader = results_filing_downloader.ResultsFilingDownloader(
            self.data_folder / 'nse' / 'results_filings',
        )
        parser = results_filing_parser.ResultsFilingParser()
        rows = []
        for target in chosen:
            if not target['url']:
                continue
            path = downloader.folder / downloader.file_name(target)
            if not path.exists():
                continue
            figures = parser.parse(path)
            shares = figures.shares_outstanding
            if shares is not None and not (
                self.MIN_SHARES <= shares <= self.MAX_SHARES
            ):
                shares = None
            rows.append(
                {
                    'symbol': target['symbol'],
                    'period_end': pandas.to_datetime(
                        target['to_date'],
                        format='%d-%b-%Y',
                    ),
                    'broadcast': pandas.to_datetime(
                        target['broadcast'],
                        format='%d-%b-%Y %H:%M:%S',
                    ),
                    'eps': figures.eps,
                    'shares': shares,
                },
            )
        panel = pandas.DataFrame(rows).dropna(subset=['eps'])
        actions = corporate_action_reader.CorporateActionReader().read_folder(
            self.data_folder / 'nse' / 'corporate_actions',
            2009,
            2026,
        )
        if announcements is not None:
            panel = self.use_announcement_times(panel, announcements)
        factor = self.adjustment_factors(panel, actions)
        panel['adjusted_eps'] = panel['eps'] * factor
        return self.sue_table(panel)
