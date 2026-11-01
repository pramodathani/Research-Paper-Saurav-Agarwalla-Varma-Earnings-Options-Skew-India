"""Tests that the study's package installs and imports."""

import unittest

import saurav_agarwalla_varma_asymmetric_uncertainty_india


class PackageImportTest(unittest.TestCase):
    """Checks that the package can be imported."""

    def test_package_has_docstring(self) -> None:
        """Checks that the installed package carries its docstring.

        Raises:
            AssertionError: If the package has no docstring.
        """
        self.assertIn(
            'NSE', saurav_agarwalla_varma_asymmetric_uncertainty_india.__doc__
        )
