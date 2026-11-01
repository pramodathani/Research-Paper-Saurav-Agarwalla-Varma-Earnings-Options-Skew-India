"""Reads NSE's corporate action JSON into price factors and dividends."""

import json
import pathlib
import re

import pandas


class CorporateActionReader:
    """Keeps bonuses, splits and dividends and turns them into numbers."""

    BONUS = re.compile(r'bonus\s*(\d+)\s*:\s*(\d+)', re.IGNORECASE)
    SPLIT = re.compile(
        r'(?:split|sub-?division|consolidation).*?from\s*r[se]\.?\s*([\d.]+).*?'
        r'to\s*r[se]\.?\s*([\d.]+)',
        re.IGNORECASE,
    )
    DIVIDEND = re.compile(
        r'dividend\s*-?\s*r[se]\.?\s*([\d.]+)',
        re.IGNORECASE,
    )

    def parse_subject(self, subject: str) -> tuple[str, float] | None:
        """Parses one corporate action description.

        Args:
            subject: The text of the action, such as 'Bonus 1:1'.

        Returns:
            A pair of kind and value, or None if the action does not change
            the price. A bonus of a:b gives ('factor', b / (a + b)), a split
            from face value F1 to F2 gives ('factor', F2 / F1), and a
            dividend gives ('dividend', rupees per share).
        """
        bonus = self.BONUS.search(subject)
        if bonus:
            given = float(bonus.group(1))
            held = float(bonus.group(2))
            return 'factor', held / (given + held)
        split = self.SPLIT.search(subject)
        if split:
            old_value = float(split.group(1))
            new_value = float(split.group(2))
            if old_value > 0 and new_value > 0:
                return 'factor', new_value / old_value
            return None
        dividend = self.DIVIDEND.search(subject)
        if dividend and 'per share' in subject.lower():
            try:
                return 'dividend', float(dividend.group(1).rstrip('.'))
            except ValueError:
                return None
        return None

    def read_year(self, path: pathlib.Path) -> pandas.DataFrame:
        """Reads one year's JSON file.

        Args:
            path: A corporate_actions_YYYY.json file.

        Returns:
            One row per symbol, ex-date, kind and value, without duplicates,
            with columns symbol, ex_date, kind and value.
        """
        rows = []
        for item in json.loads(path.read_text()):
            parsed = self.parse_subject(item.get('subject') or '')
            if parsed is None:
                continue
            try:
                ex_date = pandas.to_datetime(item['exDate'], format='%d-%b-%Y')
            except KeyError, ValueError:
                continue
            rows.append(
                {
                    'symbol': item['symbol'],
                    'ex_date': ex_date,
                    'kind': parsed[0],
                    'value': parsed[1],
                },
            )
        frame = pandas.DataFrame(
            rows,
            columns=['symbol', 'ex_date', 'kind', 'value'],
        )
        return frame.drop_duplicates().reset_index(drop=True)

    def read_folder(
        self,
        folder: pathlib.Path,
        first_year: int,
        last_year: int,
    ) -> pandas.DataFrame:
        """Reads every year in a range.

        Args:
            folder: The corporate_actions folder.
            first_year: The first year.
            last_year: The last year.

        Returns:
            One table for all years.
        """
        frames = [
            self.read_year(folder / f'corporate_actions_{year}.json')
            for year in range(first_year, last_year + 1)
        ]
        table = pandas.concat(frames, ignore_index=True)
        return table.drop_duplicates().reset_index(drop=True)
