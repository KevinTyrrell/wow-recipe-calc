#  Copyright (C) 2026  Kevin Tyrrell
#  GUI-driven WoW profession analyzer for material aggregation, cost calculation, and optimized crafting sequences
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>

import argparse
import logging

from argparse import ArgumentParser


def parse_args() -> argparse.Namespace:
    parser: ArgumentParser = ArgumentParser(
        description=(
            "WoW Recipe Calculator\n\n"
            "Calculates the raw materials required for a set of crafts."
        ),
        formatter_class = argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--log-level",
        dest = "log_level",
        type = lambda x: getattr(logging, x.upper()),
        choices = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default = logging.INFO,
        help = "Sets the logging level (default: INFO)"
    )

    return parser.parse_args()
