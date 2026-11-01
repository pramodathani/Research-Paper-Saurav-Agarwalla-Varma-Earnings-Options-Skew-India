"""Winsorises variables at chosen percentiles."""

import pandas


class Winsoriser:
    """Clips each column at its lower and upper percentile."""

    def __init__(self, lower: float = 0.05, upper: float = 0.95) -> None:
        """Stores the percentiles.

        Args:
            lower: The lower percentile as a fraction.
            upper: The upper percentile as a fraction.
        """
        self.lower = lower
        self.upper = upper

    def apply(
        self,
        data: pandas.DataFrame,
        columns: list[str],
    ) -> pandas.DataFrame:
        """Clips the given columns, ignoring missing values.

        Args:
            data: The table.
            columns: The columns to clip.

        Returns:
            A copy of the table with the columns clipped.
        """
        result = data.copy()
        for name in columns:
            low = result[name].quantile(self.lower)
            high = result[name].quantile(self.upper)
            result[name] = result[name].clip(low, high)
        return result
