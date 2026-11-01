"""Tests for the announcement reader and the broadcast replacement."""

import datetime
import json
import pathlib
import tempfile
import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    announcement_reader,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    eps_panel_builder,
)


class AnnouncementReaderTest(unittest.TestCase):
    """Checks date parsing, folder reading and de-duplication."""

    def setUp(self) -> None:
        """Creates a reader.

        Raises:
            AssertionError: Never.
        """
        self.reader = announcement_reader.AnnouncementReader()

    def test_period_formats_seen_on_nse(self) -> None:
        """Checks the wordings found in NSE's announcement texts.

        Raises:
            AssertionError: If a date is read wrongly.
        """
        cases = {
            'Infosys Limited has submitted the financial results for the '
            'period ended September 30, 2017.': (2017, 9, 30),
            'Reliance has submitted the standalone & consolidated financial '
            'results for the period ended 31-Mar-2015.': (2015, 3, 31),
            'results for the quarter ended 30 June 2018 along with': (
                2018,
                6,
                30,
            ),
            'results for the year ended 31.03.2016': (2016, 3, 31),
        }
        for text, expected in cases.items():
            self.assertEqual(
                self.reader.parse_period(text),
                datetime.date(*expected),
            )

    def test_text_without_a_period_gives_none(self) -> None:
        """Checks missing and unreadable text gives None.

        Raises:
            AssertionError: If a date is returned.
        """
        self.assertIsNone(self.reader.parse_period(None))
        self.assertIsNone(self.reader.parse_period('Outcome of Board Meeting'))
        self.assertIsNone(self.reader.parse_period('period ended soon'))

    def test_read_folder_keeps_financial_results_only(self) -> None:
        """Checks board outcomes are dropped and the earliest is kept.

        Raises:
            AssertionError: If the wrong rows are kept.
        """
        rows = [
            {
                'symbol': 'AAA',
                'an_dt': '24-Oct-2017 15:43:00',
                'desc': 'Financial Result Updates',
                'text': 'results for the period ended September 30, 2017.',
            },
            {
                'symbol': 'AAA',
                'an_dt': '26-Oct-2017 10:00:00',
                'desc': 'Financial Result Updates',
                'text': 'results for the period ended September 30, 2017.',
            },
            {
                'symbol': 'AAA',
                'an_dt': '24-Oct-2017 15:59:00',
                'desc': 'Outcome of Board Meeting',
                'text': 'Outcome of Board Meeting held on October 24, 2017.',
            },
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'AAA__2016_2017.json'
            path.write_text(json.dumps(rows))
            table = self.reader.read_folder(pathlib.Path(folder))
        self.assertEqual(len(table), 2)
        first = self.reader.first_announcements(table)
        self.assertEqual(len(first), 1)
        self.assertEqual(
            first['announced'].iloc[0],
            pandas.Timestamp('2017-10-24 15:43:00'),
        )


class UseAnnouncementTimesTest(unittest.TestCase):
    """Checks which announcement times replace the results API times."""

    def test_replacement_rules(self) -> None:
        """Checks match, late announcement, early announcement and none.

        Raises:
            AssertionError: If a time is replaced wrongly.
        """
        panel = pandas.DataFrame(
            {
                'symbol': ['A', 'B', 'C', 'D'],
                'period_end': pandas.to_datetime(['2017-03-31'] * 4),
                'broadcast': pandas.to_datetime(['2017-06-21 16:15'] * 4),
            },
        )
        announcements = pandas.DataFrame(
            {
                'symbol': ['A', 'B', 'C'],
                'period_end': pandas.to_datetime(['2017-03-31'] * 3),
                'announced': pandas.to_datetime(
                    [
                        '2017-04-13 08:50',
                        '2017-07-30 10:00',
                        '2017-03-01 10:00',
                    ],
                ),
            },
        )
        builder = eps_panel_builder.EpsPanelBuilder(None)
        result = builder.use_announcement_times(panel, announcements)
        result = result.set_index('symbol')
        self.assertEqual(
            result.loc['A', 'broadcast'],
            pandas.Timestamp('2017-04-13 08:50'),
        )
        self.assertEqual(result.loc['A', 'time_source'], 'announcement')
        for symbol in 'BCD':
            self.assertEqual(
                result.loc[symbol, 'broadcast'],
                pandas.Timestamp('2017-06-21 16:15'),
            )
            self.assertEqual(result.loc[symbol, 'time_source'], 'results_api')
        self.assertEqual(
            result.loc['A', 'results_broadcast'],
            pandas.Timestamp('2017-06-21 16:15'),
        )


if __name__ == '__main__':
    unittest.main()
