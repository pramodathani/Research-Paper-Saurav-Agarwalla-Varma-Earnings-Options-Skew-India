"""Tests for the results filing parser on short made-up filings."""

import pathlib
import tempfile
import unittest

from saurav_agarwalla_varma_asymmetric_uncertainty_india.data import (
    results_filing_parser,
)

OLD_HTML = (
    '<html><body><table><tr><td>Amount(Rs. in lakhs)</td></tr>'
    '<tr><td>Face Value (in Rs.)</td><td>10.00</td></tr>'
    '<tr><td>Paid-up equity share capital</td><td>1,618.93</td></tr>'
    '<tr><td>Basic EPS before Extraordinary items (in Rs.)</td>'
    '<td>-1.83</td></tr></table></body></html>'
)
MIDDLE_HTML = (
    '<td>Face Value (in Rs.)</td><td>2.00</td>'
    '<td>Paid-up equity share capital</td><td>4238.00</td>'
    '<td>Earnings per share (before extraordinary items) (not annualised):'
    '</td><td>(a) Basic</td><td>8.09</td><td>(b) Diluted</td><td>8.09</td>'
)
IND_AS_HTML = (
    '<td>Face Value (in Rs.)</td><td>2.00</td>'
    '<td>Paid-up equity share capital</td><td>4238.00</td>'
    '<td>Basic EPS for continuing operations</td><td>4.16</td>'
)
BLANK_HTML = (
    '<td>Earnings per share (before extraordinary items) (not annualised):'
    '</td><td>(a) Basic</td><td>-</td><td>(b) Diluted</td><td>-</td>'
)
XML = (
    '<xbrli:xbrl>'
    '<in-bse-fin:PaidUpValueOfEquityShareCapital contextRef="OneD" '
    'unitRef="INR" decimals="-7">59260000000.00\n'
    '</in-bse-fin:PaidUpValueOfEquityShareCapital>'
    '<in-bse-fin:FaceValueOfEquityShareCapital contextRef="OneD" '
    'unitRef="INRPerShare" decimals="INF">10\n'
    '</in-bse-fin:FaceValueOfEquityShareCapital>'
    '<in-bse-fin:BasicEarningsLossPerShareFromContinuingOperations '
    'contextRef="FourD" unitRef="INRPerShare">99.0\n'
    '</in-bse-fin:BasicEarningsLossPerShareFromContinuingOperations>'
    '<in-bse-fin:BasicEarningsLossPerShareFromContinuingOperations '
    'contextRef="OneD" unitRef="INRPerShare">17.05\n'
    '</in-bse-fin:BasicEarningsLossPerShareFromContinuingOperations>'
    '</xbrli:xbrl>'
)
BANK_XML = (
    '<in-bse-fin:BasicEarningsPerShareBeforeExtraordinaryItems '
    'contextRef="OneD" unitRef="INRPerShare">3.5\n'
    '</in-bse-fin:BasicEarningsPerShareBeforeExtraordinaryItems>'
)


class ResultsFilingParserTest(unittest.TestCase):
    """Checks each layout, the units and the missing-value cases."""

    def parse(self, name: str, text: str):
        """Writes a filing to a temporary file and parses it.

        Args:
            name: The file name, in SYMBOL__period__original form.
            text: The file's text.

        Returns:
            The parsed figures.
        """
        folder = pathlib.Path(self.enterContext(tempfile.TemporaryDirectory()))
        path = folder / name
        path.write_text(text)
        return results_filing_parser.ResultsFilingParser().parse(path)

    def test_old_html_layout(self) -> None:
        """Checks EPS, face value and lakhs-to-rupees conversion.

        Raises:
            AssertionError: If a figure is wrong.
        """
        figures = self.parse('AAA__31-Dec-2009__x.html', OLD_HTML)
        self.assertEqual(figures.symbol, 'AAA')
        self.assertEqual(figures.period_end, '31-Dec-2009')
        self.assertAlmostEqual(figures.eps, -1.83)
        self.assertAlmostEqual(figures.paid_up_rupees, 161893000.0)
        self.assertAlmostEqual(figures.shares_outstanding, 16189300.0)

    def test_middle_html_layout(self) -> None:
        """Checks the 2012 to 2016 wording takes the Basic figure.

        Raises:
            AssertionError: If the EPS is wrong.
        """
        figures = self.parse('AAA__31-Mar-2015__x.html', MIDDLE_HTML)
        self.assertAlmostEqual(figures.eps, 8.09)
        self.assertAlmostEqual(figures.shares_outstanding, 211900000.0)

    def test_ind_as_html_layout(self) -> None:
        """Checks the 2017 Ind-AS wording.

        Raises:
            AssertionError: If the EPS is wrong.
        """
        figures = self.parse('AAA__31-Mar-2017__x.html', IND_AS_HTML)
        self.assertAlmostEqual(figures.eps, 4.16)

    def test_blank_eps_is_missing(self) -> None:
        """Checks a dash in the EPS cell gives None.

        Raises:
            AssertionError: If an EPS is returned.
        """
        figures = self.parse('AAA__31-Mar-2017__x.html', BLANK_HTML)
        self.assertIsNone(figures.eps)
        self.assertIsNone(figures.shares_outstanding)

    def test_xml_uses_the_reports_own_period(self) -> None:
        """Checks the OneD context is used and amounts are in rupees.

        Raises:
            AssertionError: If a figure is wrong.
        """
        figures = self.parse('RELIANCE__30-Jun-2019__x.xml', XML)
        self.assertAlmostEqual(figures.eps, 17.05)
        self.assertAlmostEqual(figures.paid_up_rupees, 59260000000.0)
        self.assertAlmostEqual(figures.shares_outstanding, 5926000000.0)

    def test_bank_xml_tag(self) -> None:
        """Checks the bank EPS tag is read.

        Raises:
            AssertionError: If the EPS is wrong.
        """
        figures = self.parse('BANK__31-Mar-2019__x.xml', BANK_XML)
        self.assertAlmostEqual(figures.eps, 3.5)
        self.assertIsNone(figures.face_value)


if __name__ == '__main__':
    unittest.main()
