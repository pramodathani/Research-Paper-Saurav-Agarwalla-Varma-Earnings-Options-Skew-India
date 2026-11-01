"""Reads NSE's daily cash-market bhavcopy in both of its formats."""

import io
import pathlib
import zipfile

import pandas


class CashBhavcopyReader:
    """Turns one daily cash bhavcopy zip into a table of shares."""

    COLUMNS = (
        'date',
        'symbol',
        'series',
        'isin',
        'close',
        'previous_close',
        'volume',
        'value_rupees',
    )
    SERIES = ('EQ', 'BE', 'BZ')

    def read(self, path: pathlib.Path) -> pandas.DataFrame:
        """Reads a zip in either format.

        Args:
            path: The zip file, old format (cm01JAN2015bhav.csv.zip) or UDiFF
                (BhavCopy_NSE_CM_0_0_0_20240708_F_0000.csv.zip).

        Returns:
            One row per share in series EQ, BE or BZ, with the columns in
            COLUMNS. Value is in rupees.

        Raises:
            ValueError: If the file name is in neither format.
        """
        with zipfile.ZipFile(path) as archive:
            text = archive.read(archive.namelist()[0]).decode('utf-8')
        frame = pandas.read_csv(io.StringIO(text), dtype=str)
        if path.name.startswith('cm'):
            return self.read_old(frame)
        if path.name.startswith('BhavCopy_NSE_CM'):
            return self.read_udiff(frame)
        raise ValueError(f'Unknown cash bhavcopy name: {path.name}')

    def read_old(self, frame: pandas.DataFrame) -> pandas.DataFrame:
        """Normalises the old format used until 2024-07-05.

        Args:
            frame: The raw table, all text.

        Returns:
            The normalised table.
        """
        frame = frame[frame['SERIES'].isin(self.SERIES)]
        if 'ISIN' not in frame.columns:
            frame = frame.assign(ISIN='')
        result = pandas.DataFrame(
            {
                'date': pandas.to_datetime(
                    frame['TIMESTAMP'],
                    format='%d-%b-%Y',
                ),
                'symbol': frame['SYMBOL'],
                'series': frame['SERIES'],
                'isin': frame['ISIN'].fillna(''),
                'close': pandas.to_numeric(frame['CLOSE']),
                'previous_close': pandas.to_numeric(frame['PREVCLOSE']),
                'volume': pandas.to_numeric(frame['TOTTRDQTY']),
                'value_rupees': pandas.to_numeric(frame['TOTTRDVAL']),
            },
        )
        return result[list(self.COLUMNS)].reset_index(drop=True)

    def read_udiff(self, frame: pandas.DataFrame) -> pandas.DataFrame:
        """Normalises the UDiFF format used from 2024-07-08.

        Args:
            frame: The raw table, all text.

        Returns:
            The normalised table.
        """
        frame = frame[frame['SctySrs'].isin(self.SERIES)]
        frame = frame[frame['FinInstrmTp'] == 'STK']
        result = pandas.DataFrame(
            {
                'date': pandas.to_datetime(frame['TradDt']),
                'symbol': frame['TckrSymb'],
                'series': frame['SctySrs'],
                'isin': frame['ISIN'].fillna(''),
                'close': pandas.to_numeric(frame['ClsPric']),
                'previous_close': pandas.to_numeric(frame['PrvsClsgPric']),
                'volume': pandas.to_numeric(frame['TtlTradgVol']),
                'value_rupees': pandas.to_numeric(frame['TtlTrfVal']),
            },
        )
        return result[list(self.COLUMNS)].reset_index(drop=True)
