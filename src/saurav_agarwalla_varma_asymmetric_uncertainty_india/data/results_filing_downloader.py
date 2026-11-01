"""Downloads NSE results filings, resumably and politely."""

import json
import pathlib
import time
from typing import ClassVar

import requests


class ResultsFilingDownloader:
    """Saves each results filing exactly as NSE served it."""

    HEADERS: ClassVar[dict[str, str]] = {
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/124 Safari/537.36'
        ),
        'Referer': 'https://www.nseindia.com/',
    }

    def __init__(
        self,
        folder: pathlib.Path,
        pause_seconds: float = 0.25,
    ) -> None:
        """Prepares the output folder and the HTTP session.

        Args:
            folder: Where the filings are saved.
            pause_seconds: The pause between two requests.
        """
        self.folder = folder
        self.pause_seconds = pause_seconds
        self.folder.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def file_name(self, target: dict[str, str]) -> str:
        """Builds the file name for one filing.

        Args:
            target: A target from ResultsFilingTargets.

        Returns:
            The file name, made of symbol, period end and the NSE file name.
        """
        original = target['url'].rsplit('/', 1)[-1]
        return f'{target["symbol"]}__{target["to_date"]}__{original}'

    def run(self, targets: list[dict[str, str]]) -> dict[str, int]:
        """Downloads every filing that is not yet on disk.

        Args:
            targets: The filings to fetch.

        Returns:
            The counts of downloaded, skipped, missing and failed filings.
        """
        counts = {'downloaded': 0, 'skipped': 0, 'no_link': 0, 'failed': 0}
        failed_path = self.folder / 'failed.jsonl'
        for index, target in enumerate(targets):
            if not target['url']:
                counts['no_link'] += 1
                continue
            path = self.folder / self.file_name(target)
            if path.exists():
                counts['skipped'] += 1
                continue
            try:
                response = self.session.get(target['url'], timeout=40)
                if response.status_code == 200 and len(response.content) > 500:
                    path.write_bytes(response.content)
                    counts['downloaded'] += 1
                else:
                    self.record_failure(failed_path, target, response)
                    counts['failed'] += 1
            except requests.RequestException as error:
                self.record_failure(failed_path, target, error)
                counts['failed'] += 1
            time.sleep(self.pause_seconds)
            if index % 200 == 0:
                print(index, len(targets), counts, flush=True)
        return counts

    def record_failure(
        self,
        failed_path: pathlib.Path,
        target: dict[str, str],
        problem: object,
    ) -> None:
        """Appends one failure to the failure log.

        Args:
            failed_path: The log file.
            target: The filing that failed.
            problem: The response or the exception.
        """
        status = getattr(problem, 'status_code', str(problem))
        with failed_path.open('a') as handle:
            handle.write(json.dumps({'target': target, 'status': status}))
            handle.write('\n')
