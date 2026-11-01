"""Tests for the corporate action reader."""

import json
import pathlib
import tempfile
import unittest

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    corporate_action_reader,
)


class CorporateActionReaderTest(unittest.TestCase):
    """Checks factors, dividends and the actions that are skipped."""

    def setUp(self) -> None:
        """Creates a reader.

        Raises:
            AssertionError: Never.
        """
        self.reader = corporate_action_reader.CorporateActionReader()

    def test_bonus_factor(self) -> None:
        """Checks 1:1 gives 0.5 and 3:2 gives 0.4.

        Raises:
            AssertionError: If a factor is wrong.
        """
        self.assertEqual(
            self.reader.parse_subject(' Bonus 1:1'), ('factor', 0.5)
        )
        self.assertEqual(
            self.reader.parse_subject('Bonus 3:2'), ('factor', 0.4)
        )

    def test_split_factor(self) -> None:
        """Checks a 10 to 1 split gives 0.1 and a 10 to 2 split gives 0.2.

        Raises:
            AssertionError: If a factor is wrong.
        """
        text = (
            'Face Value Split (Sub-Division) - From Rs 10/- Per Share '
            'To Re 1/- Per Share'
        )
        self.assertEqual(self.reader.parse_subject(text), ('factor', 0.1))
        text = text.replace('Re 1/-', 'Rs 2/-')
        self.assertEqual(self.reader.parse_subject(text), ('factor', 0.2))

    def test_consolidation_factor_is_above_one(self) -> None:
        """Checks a reverse split from 1 to 10 gives a factor of 10.

        Raises:
            AssertionError: If the factor is wrong.
        """
        text = 'Face Value Consolidation - From Rs 1/- To Rs 10/- Per Share'
        self.assertEqual(self.reader.parse_subject(text), ('factor', 10.0))

    def test_dividends(self) -> None:
        """Checks several dividend wordings.

        Raises:
            AssertionError: If an amount is wrong.
        """
        wordings = [
            'Annual General Meeting/Dividend - Rs 2.5 Per Share',
            'Interim Dividend - Rs 2.5/- Per Share (Purpose Revised)',
            'Dividend- Rs 2.5 Per Share',
        ]
        for text in wordings:
            self.assertEqual(
                self.reader.parse_subject(text),
                ('dividend', 2.5),
            )
        self.assertEqual(
            self.reader.parse_subject('Dividend - Re 1/- Per Share'),
            ('dividend', 1.0),
        )

    def test_other_actions_are_skipped(self) -> None:
        """Checks meetings, buybacks and interest are ignored.

        Raises:
            AssertionError: If an action is returned.
        """
        for text in [
            'Annual General Meeting',
            'Buyback',
            'Interest Payment',
            '',
        ]:
            self.assertIsNone(self.reader.parse_subject(text))

    def test_read_year_drops_duplicates_and_bad_dates(self) -> None:
        """Checks a year file is filtered and de-duplicated.

        Raises:
            AssertionError: If the table is wrong.
        """
        rows = [
            {'symbol': 'AAA', 'exDate': '02-Jan-2017', 'subject': 'Bonus 1:1'},
            {'symbol': 'AAA', 'exDate': '02-Jan-2017', 'subject': 'Bonus 1:1'},
            {'symbol': 'AAA', 'exDate': '-', 'subject': 'Bonus 1:1'},
            {'symbol': 'BBB', 'exDate': '03-Jan-2017', 'subject': 'Buyback'},
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'corporate_actions_2017.json'
            path.write_text(json.dumps(rows))
            table = self.reader.read_year(path)
        self.assertEqual(len(table), 1)
        self.assertEqual(table['value'].iloc[0], 0.5)


if __name__ == '__main__':
    unittest.main()
