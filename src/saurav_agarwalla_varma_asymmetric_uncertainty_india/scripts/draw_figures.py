"""Draws the figures for one results folder."""

import argparse
import pathlib

from saurav_agarwalla_varma_asymmetric_uncertainty_india.earnings_options import (
    figure_drawer,
)


class DrawFiguresApplication:
    """Command-line program that draws the figures."""

    def run(self) -> None:
        """Draws every figure into the folder's figures subfolder.

        Raises:
            FileNotFoundError: If a figure table is missing.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--results', default='results/main')
        arguments = parser.parse_args()
        drawer = figure_drawer.FigureDrawer(pathlib.Path(arguments.results))
        for path in drawer.draw_all():
            print(path)


if __name__ == '__main__':
    DrawFiguresApplication().run()
