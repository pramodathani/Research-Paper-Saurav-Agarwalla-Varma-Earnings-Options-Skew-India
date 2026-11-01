"""Table 5: smile levels in the pre-EA, EA and post-EA months."""

import pandas
from scipy import stats


class MonthComparison:
    """Compares each event's smile levels across three calendar months."""

    PARAMETERS = ('atm_iv', 'iv_75', 'iv_25')
    MIN_DAYS = 5

    def __init__(self, smile: pandas.DataFrame) -> None:
        """Averages the smile levels over every share-month.

        Args:
            smile: The stock-day smile panel.
        """
        frame = smile.assign(month=smile['date'].dt.to_period('M'))
        grouped = frame.groupby(['symbol', 'month'])
        self.means = grouped[list(self.PARAMETERS)].mean()
        self.days = grouped.size()

    def event_means(self, events: pandas.DataFrame) -> pandas.DataFrame:
        """Looks up the pre, EA and post month means for each event.

        Args:
            events: Kept events with symbol and day0.

        Returns:
            One row per event whose three months each have at least five
            days, with columns such as atm_iv_pre, atm_iv_ea, atm_iv_post.
        """
        month = events['day0'].dt.to_period('M')
        pieces = {}
        for label, shift in [('pre', -1), ('ea', 0), ('post', 1)]:
            keys = pandas.MultiIndex.from_arrays(
                [events['symbol'], month + shift],
            )
            values = self.means.reindex(keys)
            values.index = events.index
            for name in self.PARAMETERS:
                pieces[f'{name}_{label}'] = values[name]
            pieces[f'days_{label}'] = self.days.reindex(keys).set_axis(
                events.index,
            )
        table = pandas.DataFrame(pieces)
        enough = (
            (table['days_pre'] >= self.MIN_DAYS)
            & (table['days_ea'] >= self.MIN_DAYS)
            & (table['days_post'] >= self.MIN_DAYS)
        )
        return table[enough]

    def table(self, events: pandas.DataFrame) -> pandas.DataFrame:
        """Builds Table 5.

        The t-statistics use a Welch two-sample test on the event means,
        as a difference-in-means test, and the paired t-statistic on the
        within-event differences is reported next to it.

        Args:
            events: Kept events with symbol and day0.

        Returns:
            One row per parameter with the three means, the two
            differences, their t-statistics and the number of events.
        """
        means = self.event_means(events)
        rows = []
        for name in self.PARAMETERS:
            pre = means[f'{name}_pre']
            during = means[f'{name}_ea']
            post = means[f'{name}_post']
            rows.append(
                {
                    'parameter': name,
                    'pre': pre.mean(),
                    'ea': during.mean(),
                    'post': post.mean(),
                    'ea_minus_pre': during.mean() - pre.mean(),
                    't_welch_pre': stats.ttest_ind(
                        during,
                        pre,
                        equal_var=False,
                    ).statistic,
                    't_paired_pre': stats.ttest_rel(during, pre).statistic,
                    'ea_minus_post': during.mean() - post.mean(),
                    't_welch_post': stats.ttest_ind(
                        during,
                        post,
                        equal_var=False,
                    ).statistic,
                    't_paired_post': stats.ttest_rel(during, post).statistic,
                    'events': float(len(means)),
                },
            )
        return pandas.DataFrame(rows)
