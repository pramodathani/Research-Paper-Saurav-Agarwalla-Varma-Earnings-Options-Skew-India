"""Tests for the F&O and cash bhavcopy readers, on tiny made-up files."""

import pathlib
import tempfile
import unittest
import zipfile

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    cash_bhavcopy_reader,
    fno_bhavcopy_reader,
)

OLD_FNO = (
    'INSTRUMENT,SYMBOL,EXPIRY_DT,STRIKE_PR,OPTION_TYP,OPEN,HIGH,LOW,CLOSE,'
    'SETTLE_PR,CONTRACTS,VAL_INLAKH,OPEN_INT,CHG_IN_OI,TIMESTAMP,\n'
    'FUTSTK,AAA,27-Jul-2017,0,XX,100,101,99,100.5,100.4,10,50.25,900,5,'
    '14-JUL-2017,\n'
    'OPTSTK,AAA,27-Jul-2017,100,CE,5,6,4,5.5,5.4,4,19.63,2500,0,'
    '14-JUL-2017,\n'
    'OPTSTK,AAA,27-Jul-2017,100,PE,5,6,4,5.5,5.4,0,0,2500,0,14-JUL-2017,\n'
    'FUTIDX,NIFTY,27-Jul-2017,0,XX,1,1,1,1,1,9,9,9,9,14-JUL-2017,\n'
)
UDIFF_FNO = (
    'TradDt,FinInstrmTp,TckrSymb,XpryDt,StrkPric,OptnTp,ClsPric,SttlmPric,'
    'UndrlygPric,OpnIntrst,TtlTradgVol,TtlTrfVal,NewBrdLotQty\n'
    '2025-01-06,STF,BBB,2025-01-30,,,200,201,199,100,7,2800000.00,400\n'
    '2025-01-06,STO,BBB,2025-01-30,2100.00,CE,8.5,8.6,1937.85,1600,4756,'
    '4012302480.00,400\n'
    '2025-01-06,IDO,NIFTY,2025-01-30,2100.00,CE,8.5,8.6,1937.85,1,1,1,50\n'
    '2025-01-06,STO,BBB,2025-01-30,2200.00,PE,1,1,1937.85,5,0,0,400\n'
)
OLD_CASH = (
    'SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,'
    'TIMESTAMP,TOTALTRADES,ISIN,\n'
    'AAA,EQ,1,1,1,972.05,972,977.05,11239090,11076700000.5,14-JUL-2017,5,'
    'INE009A01021,\n'
    'GOLDBEES,EQ,1,1,1,2,2,2,1,1,14-JUL-2017,1,INF204KB17I5,\n'
    'CCC,N1,1,1,1,2,2,2,1,1,14-JUL-2017,1,INE000000000,\n'
)
UDIFF_CASH = (
    'TradDt,FinInstrmTp,TckrSymb,SctySrs,ISIN,ClsPric,PrvsClsgPric,'
    'TtlTradgVol,TtlTrfVal\n'
    '2025-01-06,STK,AAA,EQ,INE009A01021,1937.85,1938.75,7164403,'
    '13925990000.0\n'
    '2025-01-06,STK,DDD,SM,INE000000001,10,10,1,10\n'
)


class BhavcopyReadersTest(unittest.TestCase):
    """Checks both readers on both formats."""

    def write_zip(self, name: str, text: str) -> pathlib.Path:
        """Writes a one-file zip in a temporary folder.

        Args:
            name: The zip's name.
            text: The CSV text inside.

        Returns:
            The path of the zip.
        """
        folder = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory()))
        path = folder / name
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('inner.csv', text)
        return path

    def test_old_fno_keeps_traded_stock_rows_only(self) -> None:
        """Checks index rows and zero-volume rows are dropped.

        Raises:
            AssertionError: If the wrong rows remain.
        """
        path = self.write_zip('fo14JUL2017bhav.csv.zip', OLD_FNO)
        frame = fno_bhavcopy_reader.FnoBhavcopyReader().read(path)
        self.assertEqual(list(frame['kind']), ['FUT', 'OPT'])
        self.assertEqual(list(frame['symbol']), ['AAA', 'AAA'])

    def test_old_fno_converts_lakh_to_rupees(self) -> None:
        """Checks 19.63 lakh becomes 1,963,000 rupees.

        Raises:
            AssertionError: If the value is wrong.
        """
        path = self.write_zip('fo14JUL2017bhav.csv.zip', OLD_FNO)
        frame = fno_bhavcopy_reader.FnoBhavcopyReader().read(path)
        self.assertAlmostEqual(frame['value_rupees'].iloc[1], 1963000.0)
        self.assertEqual(frame['option_type'].iloc[1], 'CE')
        self.assertEqual(frame['option_type'].iloc[0], '')
        self.assertEqual(str(frame['date'].iloc[0].date()), '2017-07-14')
        self.assertEqual(str(frame['expiry'].iloc[0].date()), '2017-07-27')

    def test_udiff_fno_reads_stock_rows(self) -> None:
        """Checks index options and zero-volume rows are dropped.

        Raises:
            AssertionError: If the wrong rows remain.
        """
        name = 'BhavCopy_NSE_FO_0_0_0_20250106_F_0000.csv.zip'
        path = self.write_zip(name, UDIFF_FNO)
        frame = fno_bhavcopy_reader.FnoBhavcopyReader().read(path)
        self.assertEqual(list(frame['kind']), ['FUT', 'OPT'])
        self.assertEqual(frame['lot_size'].iloc[1], 400)
        self.assertEqual(frame['strike'].iloc[0], 0.0)
        self.assertAlmostEqual(frame['underlying_price'].iloc[1], 1937.85)
        self.assertEqual(frame['contracts'].iloc[1], 4756)

    def test_unknown_fno_name_raises(self) -> None:
        """Checks that an unknown name is refused.

        Raises:
            AssertionError: If no error is raised.
        """
        path = self.write_zip('mystery.zip', OLD_FNO)
        with self.assertRaises(ValueError):
            fno_bhavcopy_reader.FnoBhavcopyReader().read(path)

    def test_date_from_name(self) -> None:
        """Checks the date is read from both file name styles.

        Raises:
            AssertionError: If a date is wrong.
        """
        reader = fno_bhavcopy_reader.FnoBhavcopyReader()
        old = reader.date_from_name(pathlib.Path('fo14JUL2017bhav.csv.zip'))
        new = reader.date_from_name(
            pathlib.Path('BhavCopy_NSE_FO_0_0_0_20250106_F_0000.csv.zip'),
        )
        self.assertEqual(str(old), '2017-07-14')
        self.assertEqual(str(new), '2025-01-06')

    def test_old_cash_keeps_equity_series(self) -> None:
        """Checks other series are dropped and ISINs are kept.

        Raises:
            AssertionError: If the wrong rows remain.
        """
        path = self.write_zip('cm14JUL2017bhav.csv.zip', OLD_CASH)
        frame = cash_bhavcopy_reader.CashBhavcopyReader().read(path)
        self.assertEqual(list(frame['symbol']), ['AAA', 'GOLDBEES'])
        self.assertEqual(frame['isin'].iloc[0], 'INE009A01021')
        self.assertAlmostEqual(frame['previous_close'].iloc[0], 977.05)

    def test_udiff_cash_keeps_equity_series(self) -> None:
        """Checks the SM series is dropped.

        Raises:
            AssertionError: If the wrong rows remain.
        """
        name = 'BhavCopy_NSE_CM_0_0_0_20250106_F_0000.csv.zip'
        path = self.write_zip(name, UDIFF_CASH)
        frame = cash_bhavcopy_reader.CashBhavcopyReader().read(path)
        self.assertEqual(list(frame['symbol']), ['AAA'])
        self.assertEqual(frame['volume'].iloc[0], 7164403)


if __name__ == '__main__':
    unittest.main()
