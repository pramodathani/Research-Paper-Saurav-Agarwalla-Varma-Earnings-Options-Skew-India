"""Writes the companion page's snapshot from the result tables."""

import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    site_snapshot,
)


class BuildSnapshotApplication:
    """Command-line program that writes site/data/snapshot.json."""

    def run(self) -> None:
        """Builds and writes the snapshot.

        Raises:
            FileNotFoundError: If a result table is missing.
        """
        site = pathlib.Path(__file__).resolve().parents[1] / 'site'
        size = site_snapshot.SiteSnapshot(pathlib.Path('results')).write(site)
        print('wrote', site / 'data' / 'snapshot.json', size, 'bytes')


if __name__ == '__main__':
    BuildSnapshotApplication().run()
