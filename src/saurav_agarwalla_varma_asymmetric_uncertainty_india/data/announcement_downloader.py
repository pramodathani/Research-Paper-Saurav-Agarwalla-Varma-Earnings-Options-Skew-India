"""Downloads NSE's corporate announcements about financial results."""

import json
import pathlib
import time
from typing import ClassVar

import requests


class AnnouncementDownloader:
    """Saves each share's results announcements, two years at a time."""

    HEADERS: ClassVar[dict[str, str]] = {
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/124 Safari/537.36'
        ),
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.nseindia.com/',
    }
    PAGE = (
        'https://www.nseindia.com/companies-listing/'
        'corporate-filings-announcements'
    )
    API = (
        'https://www.nseindia.com/api/corporate-announcements'
        '?index=equities&symbol={symbol}&from_date={start}&to_date={end}'
    )
    KEEP_WORDS = ('financial result', 'outcome of board', 'integrated filing')

    def __init__(
        self,
        folder: pathlib.Path,
        pause_seconds: float = 0.4,
    ) -> None:
        """Prepares the output folder and the HTTP session.

        Args:
            folder: Where the files are saved.
            pause_seconds: The pause between two requests.
        """
        self.folder = folder
        self.pause_seconds = pause_seconds
        self.folder.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.requests_since_cookie = 0
        self.refresh_cookies()

    def refresh_cookies(self) -> None:
        """Loads NSE's page so the session carries the cookies it needs."""
        self.session.get(self.PAGE, timeout=30)
        self.requests_since_cookie = 0
        time.sleep(1.0)

    def relevant(self, rows: list[dict]) -> list[dict]:
        """Keeps the announcements about results and board outcomes.

        Args:
            rows: The rows NSE returned.

        Returns:
            The rows whose description mentions results, a board outcome or
            an integrated filing, reduced to the fields the study uses.
        """
        kept = []
        for row in rows:
            description = (row.get('desc') or '').lower()
            if any(word in description for word in self.KEEP_WORDS):
                kept.append(
                    {
                        'symbol': row.get('symbol'),
                        'an_dt': row.get('an_dt'),
                        'desc': row.get('desc'),
                        'text': row.get('attchmntText'),
                        'seq_id': row.get('seq_id'),
                    },
                )
        return kept

    def fetch(self, symbol: str, first_year: int, last_year: int) -> list[dict]:
        """Fetches one share's announcements for a range of years.

        Args:
            symbol: The NSE symbol.
            first_year: The first year.
            last_year: The last year.

        Returns:
            The relevant rows.

        Raises:
            requests.RequestException: If NSE keeps refusing after retries.
        """
        url = self.API.format(
            symbol=symbol.replace('&', '%26'),
            start=f'01-01-{first_year}',
            end=f'31-12-{last_year}',
        )
        for attempt in range(4):
            if self.requests_since_cookie >= 150:
                self.refresh_cookies()
            response = self.session.get(url, timeout=60)
            self.requests_since_cookie += 1
            if response.status_code == 200:
                try:
                    return self.relevant(response.json())
                except ValueError:
                    pass
            self.refresh_cookies()
            time.sleep(2.0 * (attempt + 1))
        raise requests.RequestException(f'Gave up on {symbol} {first_year}')

    def run(
        self,
        symbols: list[str],
        first_year: int,
        last_year: int,
        chunk_years: int = 2,
    ) -> dict[str, int]:
        """Downloads every symbol and chunk not yet on disk.

        Args:
            symbols: The symbols to fetch.
            first_year: The first year.
            last_year: The last year.
            chunk_years: Years per request.

        Returns:
            The counts of fetched, skipped and failed requests.
        """
        counts = {'fetched': 0, 'skipped': 0, 'failed': 0}
        for index, symbol in enumerate(symbols):
            for start in range(first_year, last_year + 1, chunk_years):
                end = min(start + chunk_years - 1, last_year)
                name = symbol.replace('&', '_and_')
                path = self.folder / f'{name}__{start}_{end}.json'
                if path.exists():
                    counts['skipped'] += 1
                    continue
                try:
                    rows = self.fetch(symbol, start, end)
                except requests.RequestException as error:
                    counts['failed'] += 1
                    print('failed', symbol, start, error, flush=True)
                    continue
                path.write_text(json.dumps(rows))
                counts['fetched'] += 1
                time.sleep(self.pause_seconds)
            if index % 20 == 0:
                print(index, len(symbols), counts, flush=True)
        return counts
