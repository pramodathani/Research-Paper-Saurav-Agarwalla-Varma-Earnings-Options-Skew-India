"""Downloads the standalone results filings of the stock-futures shares."""

import pathlib
import sys

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    results_filing_downloader,
    results_filing_targets,
)


class DownloadResultsFilingsApplication:
    """Command-line program that downloads the results filings."""

    def run(self) -> None:
        """Builds the target list and downloads it.

        Raises:
            SystemExit: If the futures ranges file is missing.
        """
        data_folder = pathlib.Path('data')
        ranges_path = pathlib.Path(sys.argv[1])
        targets = results_filing_targets.ResultsFilingTargets(
            data_folder,
        ).build(ranges_path)
        print(len(targets), 'targets')
        downloader = results_filing_downloader.ResultsFilingDownloader(
            data_folder / 'nse' / 'results_filings',
        )
        print(downloader.run(targets))


if __name__ == '__main__':
    DownloadResultsFilingsApplication().run()
