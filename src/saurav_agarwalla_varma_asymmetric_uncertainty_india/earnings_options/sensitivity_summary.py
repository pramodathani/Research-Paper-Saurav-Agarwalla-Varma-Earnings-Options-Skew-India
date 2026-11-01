"""Picks the headline numbers out of one run of the study."""

import pandas


class SensitivitySummary:
    """Reduces a run's result tables to one row of headline numbers."""

    def row(
        self,
        name: str,
        results: dict[str, pandas.DataFrame],
        regression_key: str = 'tables_6_to_9',
    ) -> dict[str, float | str]:
        """Builds one row.

        Args:
            name: The variant's label.
            results: The result tables of a StudyRunner run.
            regression_key: Which regression table to read, to compare the
                put-to-call or SUE variants.

        Returns:
            Counts, the Table 5 ATM-IV difference with its t-statistic, and
            the coefficients and t-statistics of RR-IV, P/C and ATM-IV in
            Tables 6 and 7.
        """
        regressions = results[regression_key]
        table_five = results['table_5'].set_index('parameter')
        dataset = results['dataset']
        row = {
            'variant': name,
            'events': float(len(results['events'])),
            'rr_iv_mean': float(dataset['rr_iv_1'].mean()),
            'atm_iv_mean': float(dataset['atm_iv_1'].mean()),
            'atm_ea_minus_pre': float(table_five.loc['atm_iv', 'ea_minus_pre']),
            'atm_t_welch': float(table_five.loc['atm_iv', 't_welch_pre']),
        }
        wanted = [
            ('Table 6', '(2)', 'RR-IV', 't6_rr'),
            ('Table 6', '(2)', 'P/C', 't6_pc'),
            ('Table 6', '(2)', 'ATM-IV', 't6_atm'),
            ('Table 7', 'n=2', 'RR-IV', 't7_n2_rr'),
            ('Table 7', 'n=3', 'RR-IV', 't7_n3_rr'),
            ('Table 8', '(2)', 'Alt RR-IV', 't8_alt_rr'),
        ]
        for table, column, variable, label in wanted:
            match = regressions[
                (regressions['table'] == table)
                & (regressions['column'] == column)
                & (regressions['variable'] == variable)
            ]
            if match.empty:
                continue
            record = match.iloc[0]
            row[f'{label}_coefficient'] = float(record['coefficient'])
            row[f'{label}_t'] = float(record['t_statistic'])
            row[f'{label}_clustered_t'] = float(record['clustered_t_statistic'])
            if label == 't6_rr':
                row['observations'] = float(record['observations'])
        return row
