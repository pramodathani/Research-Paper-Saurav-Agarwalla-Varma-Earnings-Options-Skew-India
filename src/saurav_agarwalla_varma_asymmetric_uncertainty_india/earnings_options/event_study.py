"""Averages event-day variables by offset and by surprise tercile."""

import pandas


class EventStudy:
    """Builds the lines of Figures 1 to 5."""

    def __init__(self, windows: pandas.DataFrame) -> None:
        """Stores the event-day table.

        Args:
            windows: The table from EventWindowBuilder.
        """
        self.windows = windows

    def mean_by_offset(self, column: str) -> pandas.DataFrame:
        """Averages one variable on each day relative to the announcement.

        Args:
            column: The variable's name.

        Returns:
            One row per offset with the mean, the standard error of the
            mean and the number of events with a value.
        """
        grouped = self.windows.groupby('offset')[column]
        table = pandas.DataFrame(
            {
                'mean': grouped.mean(),
                'standard_error': grouped.sem(),
                'events': grouped.count(),
            },
        )
        return table.reset_index()

    def terciles(self, surprise: str = 'sue') -> pandas.DataFrame:
        """Assigns each event to a tercile of the surprise.

        Terciles are cut once over all events that have a surprise, as the
        paper splits all EAs into three quantiles.

        Args:
            surprise: The surprise column.

        Returns:
            A table with event_id and tercile, 1 for the large negative
            third, 2 for the middle third and 3 for the large positive
            third.
        """
        events = self.windows.drop_duplicates('event_id')[
            ['event_id', surprise]
        ].dropna()
        events['tercile'] = (
            pandas.qcut(events[surprise], 3, labels=False, duplicates='drop')
            + 1
        )
        return events[['event_id', 'tercile']]

    def mean_by_tercile(
        self,
        column: str,
        surprise: str = 'sue',
    ) -> pandas.DataFrame:
        """Averages one variable by offset within each surprise tercile.

        Args:
            column: The variable's name.
            surprise: The surprise column.

        Returns:
            One row per tercile and offset with mean, standard error and
            count.
        """
        merged = self.windows.merge(self.terciles(surprise), on='event_id')
        grouped = merged.groupby(['tercile', 'offset'])[column]
        table = pandas.DataFrame(
            {
                'mean': grouped.mean(),
                'standard_error': grouped.sem(),
                'events': grouped.count(),
            },
        )
        return table.reset_index()
