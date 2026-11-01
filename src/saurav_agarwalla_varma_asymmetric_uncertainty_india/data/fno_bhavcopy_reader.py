"""Reads NSE's daily F&O bhavcopy in both of its formats."""

import datetime
import io
import pathlib
import re
import zipfile

import pandas


class FnoBhavcopyReader:
    """Turns one daily F&O zip into stock futures and stock options rows."""

    COLUMNS = (
        'date',
        'symbol',
        'kind',
        'expiry',
        'strike',
        'option_type',
        'close',
        'settle',
        'contracts',
        'value_rupees',
        'open_interest',
        'lot_size',
        'underlying_price',
    )
    LAKH = 100000.0

    def read(self, path: pathlib.Path) -> pandas.DataFrame:
        """Reads a zip in either format.

        Args:
            path: The zip file, old format (fo01JAN2015bhav.csv.zip) or UDiFF
                (BhavCopy_NSE_FO_0_0_0_20240708_F_0000.csv.zip).

        Returns:
            One row per stock future or stock option that traded, with the
            columns in COLUMNS. Value is in rupees and notional for options.

        Raises:
            ValueError: If the file name is in neither format.
        """
        with zipfile.ZipFile(path) as archive:
            text = archive.read(archive.namelist()[0]).decode('utf-8')
        frame = pandas.read_csv(io.StringIO(text), dtype=str)
        if path.name.startswith('fo'):
            return self.read_old(frame)
        if path.name.startswith('BhavCopy_NSE_FO'):
            return self.read_udiff(frame)
        raise ValueError(f'Unknown F&O bhavcopy name: {path.name}')

    def read_old(self, frame: pandas.DataFrame) -> pandas.DataFrame:
        """Normalises the old format used until 2024-07-05.

        Args:
            frame: The raw table, all text.

        Returns:
            The normalised table.
        """
        frame = frame[frame['INSTRUMENT'].isin(['FUTSTK', 'OPTSTK'])].copy()
        result = pandas.DataFrame(
            {
                'date': self.parse_date(frame['TIMESTAMP']),
                'symbol': frame['SYMBOL'],
                'kind': self.kind_labels(frame['INSTRUMENT'] == 'FUTSTK'),
                'expiry': self.parse_date(frame['EXPIRY_DT']),
                'strike': pandas.to_numeric(frame['STRIKE_PR']),
                'option_type': frame['OPTION_TYP'].where(
                    frame['INSTRUMENT'] == 'OPTSTK',
                    '',
                ),
                'close': pandas.to_numeric(frame['CLOSE']),
                'settle': pandas.to_numeric(frame['SETTLE_PR']),
                'contracts': pandas.to_numeric(frame['CONTRACTS']),
                'value_rupees': (
                    pandas.to_numeric(frame['VAL_INLAKH']) * self.LAKH
                ),
                'open_interest': pandas.to_numeric(frame['OPEN_INT']),
                'lot_size': float('nan'),
                'underlying_price': float('nan'),
            },
        )
        return self.keep_traded(result)

    def read_udiff(self, frame: pandas.DataFrame) -> pandas.DataFrame:
        """Normalises the UDiFF format used from 2024-07-08.

        Args:
            frame: The raw table, all text.

        Returns:
            The normalised table. Contracts are the lots traded, and value
            is notional rupees.
        """
        frame = frame[frame['FinInstrmTp'].isin(['STF', 'STO'])].copy()
        is_future = frame['FinInstrmTp'] == 'STF'
        result = pandas.DataFrame(
            {
                'date': pandas.to_datetime(frame['TradDt']),
                'symbol': frame['TckrSymb'],
                'kind': self.kind_labels(is_future),
                'expiry': pandas.to_datetime(frame['XpryDt']),
                'strike': pandas.to_numeric(frame['StrkPric']).fillna(0.0),
                'option_type': frame['OptnTp'].where(~is_future, '').fillna(''),
                'close': pandas.to_numeric(frame['ClsPric']),
                'settle': pandas.to_numeric(frame['SttlmPric']),
                'contracts': pandas.to_numeric(frame['TtlTradgVol']),
                'value_rupees': pandas.to_numeric(frame['TtlTrfVal']),
                'open_interest': pandas.to_numeric(frame['OpnIntrst']),
                'lot_size': pandas.to_numeric(frame['NewBrdLotQty']),
                'underlying_price': pandas.to_numeric(frame['UndrlygPric']),
            },
        )
        return self.keep_traded(result)

    def parse_date(self, text: pandas.Series) -> pandas.Series:
        """Parses dates written with a four or two digit year.

        Args:
            text: Dates such as 13-JUL-2020 or 13-Jul-20.

        Returns:
            The dates as timestamps.
        """
        four = pandas.to_datetime(text, format='%d-%b-%Y', errors='coerce')
        two = pandas.to_datetime(text, format='%d-%b-%y', errors='coerce')
        return four.fillna(two)

    def keep_traded(self, frame: pandas.DataFrame) -> pandas.DataFrame:
        """Keeps the rows that traded and fixes the column order.

        Args:
            frame: A normalised table.

        Returns:
            The rows with at least one contract traded.
        """
        traded = frame[frame['contracts'] > 0]
        return traded[list(self.COLUMNS)].reset_index(drop=True)

    def date_from_name(self, path: pathlib.Path) -> datetime.date:
        """Reads the trading date from a file name.

        Args:
            path: A bhavcopy zip in either format.

        Returns:
            The trading date.

        Raises:
            ValueError: If the name has no date.
        """
        name = path.name
        if name.startswith('fo'):
            return datetime.datetime.strptime(name[2:11], '%d%b%Y').date()
        match = re.search(r'_(\d{8})_', name)
        if match is None:
            raise ValueError(f'No date in {name}')
        return datetime.datetime.strptime(match.group(1), '%Y%m%d').date()

    def kind_labels(self, is_future: pandas.Series) -> pandas.Series:
        """Maps a boolean series to the kind labels FUT and OPT.

        Args:
            is_future: True for stock futures.

        Returns:
            A series of FUT and OPT.
        """
        return is_future.map({True: 'FUT', False: 'OPT'})
