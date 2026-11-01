"""Reads saved NSE announcements and finds each quarter's first results time."""

import datetime
import json
import pathlib
import re

import pandas


class AnnouncementReader:
    """Parses result announcements and matches them to reporting periods."""

    PERIOD = re.compile(
        r'(?:period|quarter|year)\s+ended\s+(?:on\s+)?'
        r'([A-Za-z0-9][A-Za-z0-9 ,.\-/]{5,24})',
        re.IGNORECASE,
    )
    FORMATS = (
        '%B %d, %Y',
        '%B %d %Y',
        '%b %d, %Y',
        '%d-%b-%Y',
        '%d-%B-%Y',
        '%d %B %Y',
        '%d %b %Y',
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%b. %d, %Y',
    )
    MONTH_FORMATS = ('%B %Y', '%b %Y', '%B, %Y', '%B-%Y', '%b-%Y')
    RESULT_TEXT = re.compile(r'financial\s+(?:result|statement)', re.IGNORECASE)

    def parse_period(self, text: str | None) -> datetime.date | None:
        """Finds the period-end date in an announcement's text.

        Args:
            text: The announcement text.

        Returns:
            The period end, or None if no date can be read.
        """
        if not text:
            return None
        match = self.PERIOD.search(text)
        if match is None:
            return None
        words = match.group(1).strip().rstrip('.,')
        for length in range(len(words), 5, -1):
            piece = words[:length].strip().rstrip('.,')
            for pattern in self.FORMATS:
                try:
                    return datetime.datetime.strptime(piece, pattern).date()
                except ValueError:
                    continue
            for pattern in self.MONTH_FORMATS:
                try:
                    first = datetime.datetime.strptime(piece, pattern).date()
                except ValueError:
                    continue
                return self.month_end(first)
        return None

    def month_end(self, date: datetime.date) -> datetime.date:
        """Returns the last day of a date's month.

        Args:
            date: Any date in the month.

        Returns:
            The month's last day.
        """
        following = (date.replace(day=1) + datetime.timedelta(days=32)).replace(
            day=1,
        )
        return following - datetime.timedelta(days=1)

    def is_result_announcement(
        self, description: str, text: str | None
    ) -> bool:
        """Says whether an announcement is about a set of results.

        Args:
            description: NSE's category of the announcement.
            text: The announcement's text.

        Returns:
            True for a financial result update, and for a board outcome whose
            text says it considered financial results or statements.
        """
        description = description.lower()
        if 'financial result' in description:
            return True
        if 'outcome of board' in description and text:
            return self.RESULT_TEXT.search(text) is not None
        return False

    def read_folder(self, folder: pathlib.Path) -> pandas.DataFrame:
        """Reads every saved file and keeps the financial result updates.

        Args:
            folder: The announcements folder.

        Returns:
            Rows with symbol, announced (a timestamp) and period_end.
        """
        rows = []
        for path in sorted(folder.glob('*.json')):
            for item in json.loads(path.read_text()):
                description = item.get('desc') or ''
                if not self.is_result_announcement(
                    description,
                    item.get('text'),
                ):
                    continue
                try:
                    announced = pandas.to_datetime(
                        item['an_dt'],
                        format='%d-%b-%Y %H:%M:%S',
                    )
                except KeyError, ValueError, TypeError:
                    continue
                period = self.parse_period(item.get('text'))
                rows.append(
                    {
                        'symbol': item['symbol'],
                        'announced': announced,
                        'period_end': (
                            pandas.NaT
                            if period is None
                            else pandas.Timestamp(period)
                        ),
                    },
                )
        table = pandas.DataFrame(
            rows,
            columns=['symbol', 'announced', 'period_end'],
        )
        return table.drop_duplicates().reset_index(drop=True)

    def first_announcements(
        self, announcements: pandas.DataFrame
    ) -> pandas.DataFrame:
        """Keeps the earliest announcement of each symbol and period end.

        Args:
            announcements: The table from read_folder.

        Returns:
            One row per symbol and period end.
        """
        known = announcements.dropna(subset=['period_end'])
        ordered = known.sort_values('announced')
        return ordered.drop_duplicates(['symbol', 'period_end'])
