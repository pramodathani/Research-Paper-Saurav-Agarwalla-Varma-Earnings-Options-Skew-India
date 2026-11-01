"""Tests for the event study averages and surprise terciles."""

import unittest

import pandas

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    event_study,
)


class EventStudyTest(unittest.TestCase):
    """Six events with surprises one to six, on two offsets each."""

    def setUp(self) -> None:
        """Builds the event-day table.

        Raises:
            AssertionError: Never.
        """
        rows = []
        for event_id in range(6):
            for offset in [-1, 0]:
                rows.append(
                    {
                        'event_id': event_id,
                        'offset': offset,
                        'sue': float(event_id + 1),
                        'rr_iv': float(event_id) * (1 if offset == -1 else 2),
                    },
                )
        self.study = event_study.EventStudy(pandas.DataFrame(rows))

    def test_mean_by_offset(self) -> None:
        """Checks the averages 2.5 and 5.0 and the counts.

        Raises:
            AssertionError: If a mean or count is wrong.
        """
        table = self.study.mean_by_offset('rr_iv').set_index('offset')
        self.assertAlmostEqual(table.loc[-1, 'mean'], 2.5)
        self.assertAlmostEqual(table.loc[0, 'mean'], 5.0)
        self.assertEqual(table.loc[0, 'events'], 6)

    def test_terciles_split_the_events_in_three(self) -> None:
        """Checks events 0 and 1 are low, 2 and 3 middle, 4 and 5 high.

        Raises:
            AssertionError: If a tercile is wrong.
        """
        terciles = self.study.terciles().set_index('event_id')['tercile']
        self.assertEqual(list(terciles), [1, 1, 2, 2, 3, 3])

    def test_mean_by_tercile(self) -> None:
        """Checks the large negative tercile's mean at offset 0.

        Raises:
            AssertionError: If a mean is wrong.
        """
        table = self.study.mean_by_tercile('rr_iv')
        row = table[(table['tercile'] == 1) & (table['offset'] == 0)].iloc[0]
        self.assertAlmostEqual(row['mean'], 1.0)
        row = table[(table['tercile'] == 3) & (table['offset'] == -1)].iloc[0]
        self.assertAlmostEqual(row['mean'], 4.5)

    def test_events_without_a_surprise_are_left_out(self) -> None:
        """Checks events whose surprise is missing get no tercile.

        Raises:
            AssertionError: If such an event is assigned.
        """
        windows = self.study.windows.copy()
        windows.loc[windows['event_id'] == 5, 'sue'] = float('nan')
        terciles = event_study.EventStudy(windows).terciles()
        self.assertNotIn(5, list(terciles['event_id']))


if __name__ == '__main__':
    unittest.main()
