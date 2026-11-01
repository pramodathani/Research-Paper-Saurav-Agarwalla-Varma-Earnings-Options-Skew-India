"""Downloads results announcements for every stock-futures share."""

import argparse
import json
import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    announcement_downloader,
)


class DownloadAnnouncementsApplication:
    """Command-line program that downloads the announcements."""

    def run(self) -> None:
        """Downloads 2014 to 2025 for every symbol with stock futures.

        Raises:
            FileNotFoundError: If the futures ranges file is missing.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--shard', type=int, default=0)
        parser.add_argument('--shards', type=int, default=1)
        arguments = parser.parse_args()
        data_folder = pathlib.Path('data')
        ranges = json.loads(
            (data_folder / 'derived' / 'futures_ranges.json').read_text(),
        )
        symbols = sorted(ranges)[arguments.shard :: arguments.shards]
        downloader = announcement_downloader.AnnouncementDownloader(
            data_folder / 'nse' / 'announcements',
        )
        print(downloader.run(symbols, 2014, 2025))


if __name__ == '__main__':
    DownloadAnnouncementsApplication().run()
