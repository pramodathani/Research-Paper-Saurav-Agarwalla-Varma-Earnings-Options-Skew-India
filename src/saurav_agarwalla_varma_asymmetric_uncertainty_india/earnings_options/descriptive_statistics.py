"""Tables 3 and 4: summary statistics and correlations."""

import pandas


class DescriptiveStatistics:
    """Describes the event-level dataset before winsorising."""

    SUMMARY = (
        'sue',
        'rr_iv_1',
        'atm_iv_1',
        'pc_contracts_1',
        'rr_iv_2',
        'atm_iv_2',
        'pc_contracts_2',
        'rr_iv_3',
        'atm_iv_3',
        'pc_contracts_3',
        'beta',
        'momentum',
        'size',
        'bhar',
    )
    CORRELATION = (
        'sue',
        'rr_iv_1',
        'atm_iv_1',
        'pc_contracts_1',
        'rr_iv_2',
        'atm_iv_2',
        'pc_contracts_2',
        'rr_iv_3',
        'atm_iv_3',
        'pc_contracts_3',
    )

    def summary(self, dataset: pandas.DataFrame) -> pandas.DataFrame:
        """Computes Table 3.

        Args:
            dataset: One row per event.

        Returns:
            One row per variable with count, mean, standard deviation,
            minimum, quartiles and maximum.
        """
        columns = [name for name in self.SUMMARY if name in dataset.columns]
        table = dataset[columns].describe().T
        table = table.rename(
            columns={
                'count': 'N',
                'std': 'st_dev',
                '25%': 'p25',
                '50%': 'median',
                '75%': 'p75',
            },
        )
        return table.reset_index(names='variable')

    def correlations(self, dataset: pandas.DataFrame) -> pandas.DataFrame:
        """Computes Table 4, using pairwise complete observations.

        Args:
            dataset: One row per event.

        Returns:
            The correlation matrix.
        """
        columns = [name for name in self.CORRELATION if name in dataset.columns]
        return dataset[columns].corr()
