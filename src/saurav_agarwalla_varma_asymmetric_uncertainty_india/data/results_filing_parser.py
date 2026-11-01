"""Reads EPS, face value and paid-up capital from NSE results filings."""

import dataclasses
import html
import pathlib
import re


@dataclasses.dataclass
class FilingFigures:
    """The numbers the study takes from one filing.

    Attributes:
        symbol: The NSE symbol.
        period_end: The period end text from the file name, such as
            '31-Dec-2015'.
        eps: Basic EPS before extraordinary items, in rupees, or None.
        face_value: Face value per share in rupees, or None.
        paid_up_rupees: Paid-up equity share capital in rupees, or None.
    """

    symbol: str
    period_end: str
    eps: float | None
    face_value: float | None
    paid_up_rupees: float | None

    @property
    def shares_outstanding(self) -> float | None:
        """Paid-up capital divided by face value.

        Returns:
            The number of shares, or None when either figure is missing.
        """
        if not self.face_value or self.paid_up_rupees is None:
            return None
        return self.paid_up_rupees / self.face_value


class ResultsFilingParser:
    """Parses the HTML and XBRL formats of NSE's financial results."""

    LAKH = 100000.0
    NUMBER = r'(-?\d[\d,]*\.?\d*)'
    HTML_EPS = (
        re.compile(
            r'(?i)(?:basic )?EPS before extra\w* items'
            r'[^\d-]{0,40}' + NUMBER,
        ),
        re.compile(
            r'(?i)Earnings per share \(before extra\w* items\)'
            r'[^\d-]{0,80}?' + NUMBER,
        ),
        re.compile(r'(?i)Basic EPS for continuing operations ' + NUMBER),
    )
    HTML_FACE_VALUE = re.compile(r'(?i)Face Value \(in Rs\.?\) ' + NUMBER)
    HTML_CAPITAL = re.compile(
        r'(?i)paid[- ]up equity share capital[^\d]{0,80}' + NUMBER,
    )
    XML_EPS_TAGS = (
        'BasicEarningsLossPerShareFromContinuingOperations',
        'BasicEarningsPerShareBeforeExtraordinaryItems',
        'BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations',
    )

    def parse(self, path: pathlib.Path) -> FilingFigures:
        """Parses one downloaded filing.

        Args:
            path: A file named SYMBOL__period-end__original-name.

        Returns:
            The figures found, with None for anything missing.
        """
        symbol, period_end, _ = path.name.split('__', 2)
        text = path.read_text(errors='ignore')
        if path.suffix == '.xml':
            return self.parse_xml(symbol, period_end, text)
        return self.parse_html(symbol, period_end, text)

    def number(self, text: str) -> float | None:
        """Turns a matched number into a float.

        Args:
            text: The matched text, possibly with commas.

        Returns:
            The value, or None if it is not a number.
        """
        try:
            return float(text.replace(',', '').rstrip('.'))
        except ValueError:
            return None

    def parse_html(
        self,
        symbol: str,
        period_end: str,
        text: str,
    ) -> FilingFigures:
        """Parses the HTML page, whose amounts are in lakhs of rupees.

        Args:
            symbol: The NSE symbol.
            period_end: The period end text.
            text: The page's HTML.

        Returns:
            The figures found.
        """
        plain = re.sub(r'<[^>]+>', ' ', text)
        plain = html.unescape(re.sub(r'\s+', ' ', plain))
        eps = None
        for pattern in self.HTML_EPS:
            match = pattern.search(plain)
            if match:
                eps = self.number(match.group(1))
                if eps is not None:
                    break
        face = self.HTML_FACE_VALUE.search(plain)
        capital = self.HTML_CAPITAL.search(plain)
        paid_up = self.number(capital.group(1)) if capital else None
        return FilingFigures(
            symbol=symbol,
            period_end=period_end,
            eps=eps,
            face_value=self.number(face.group(1)) if face else None,
            paid_up_rupees=None if paid_up is None else paid_up * self.LAKH,
        )

    def xml_value(self, text: str, tag: str) -> float | None:
        """Reads the first value of a tag in the report's own period.

        Args:
            text: The XBRL text.
            tag: The tag's local name.

        Returns:
            The value, or None if the tag is missing.
        """
        pattern = (
            r'<[\w-]+:' + tag + r'\b[^>]*contextRef="OneD"[^>]*>\s*'
            r'(-?[\d.]+)'
        )
        match = re.search(pattern, text)
        if match is None:
            pattern = r'<[\w-]+:' + tag + r'\b[^>]*>\s*(-?[\d.]+)'
            match = re.search(pattern, text)
        return self.number(match.group(1)) if match else None

    def parse_xml(
        self,
        symbol: str,
        period_end: str,
        text: str,
    ) -> FilingFigures:
        """Parses the XBRL file, whose amounts are in rupees.

        Args:
            symbol: The NSE symbol.
            period_end: The period end text.
            text: The XBRL text.

        Returns:
            The figures found.
        """
        eps = None
        for tag in self.XML_EPS_TAGS:
            eps = self.xml_value(text, tag)
            if eps is not None:
                break
        return FilingFigures(
            symbol=symbol,
            period_end=period_end,
            eps=eps,
            face_value=self.xml_value(text, 'FaceValueOfEquityShareCapital'),
            paid_up_rupees=self.xml_value(
                text,
                'PaidUpValueOfEquityShareCapital',
            ),
        )
