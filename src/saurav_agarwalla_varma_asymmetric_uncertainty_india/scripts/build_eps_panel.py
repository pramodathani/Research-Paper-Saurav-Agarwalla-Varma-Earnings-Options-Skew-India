"""Builds the EPS panel with SUE and announcement times."""

import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    announcement_reader,
)
from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    eps_panel_builder,
)


class BuildEpsPanelApplication:
    """Command-line program that builds the EPS panel."""

    def run(self) -> None:
        """Builds the panel and saves it as parquet.

        Raises:
            FileNotFoundError: If the futures ranges or filings are missing.
        """
        data_folder = pathlib.Path('data')
        reader = announcement_reader.AnnouncementReader()
        announcements = reader.first_announcements(
            reader.read_folder(data_folder / 'nse' / 'announcements'),
        )
        builder = eps_panel_builder.EpsPanelBuilder(data_folder)
        panel = builder.build(
            data_folder / 'derived' / 'futures_ranges.json',
            announcements,
        )
        target = data_folder / 'derived' / 'eps_panel.parquet'
        panel.to_parquet(target)
        print('saved', target, len(panel))
        print(panel['time_source'].value_counts())
        shifted = panel[panel['time_source'] == 'announcement']
        days = (
            shifted['results_broadcast'].dt.normalize()
            - shifted['broadcast'].dt.normalize()
        ).dt.days
        print('days the structured filing came after the announcement:')
        print(days.describe())


if __name__ == '__main__':
    BuildEpsPanelApplication().run()
