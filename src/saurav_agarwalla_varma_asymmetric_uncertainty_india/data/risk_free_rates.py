"""Reads IIMA's monthly risk-free return into annual continuous rates."""

import math
import pathlib

import pandas


class RiskFreeRates:
    """Looks up the annual continuously compounded rate for any date."""

    def __init__(self, path: pathlib.Path) -> None:
        """Reads IIMA's four-factor file.

        Args:
            path: The IIMA csv with a Date column such as 2015-01 and a
                monthly RF column in percent.
        """
        table = pandas.read_csv(path, na_values=['NA'])
        table = table.dropna(subset=['RF'])
        self.rates = {
            str(row['Date']): math.log1p(row['RF'] / 100.0) * 12.0
            for _, row in table.iterrows()
        }
        self.last_month = max(self.rates)

    def rate(self, date: pandas.Timestamp) -> float:
        """Returns the rate of the date's month.

        Args:
            date: Any date.

        Returns:
            The annual continuous rate. After IIMA's last month, the last
            rate is used, and before its first month the first.
        """
        key = f'{date.year:04d}-{date.month:02d}'
        if key in self.rates:
            return self.rates[key]
        if key > self.last_month:
            return self.rates[self.last_month]
        return self.rates[min(self.rates)]
