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


def _parse_log_level(value: str) -> int:
    # abuse the fact that logging has these constants pre-defined
    level: int = getattr(logging, value.upper(), None)
    if not isinstance(level, int):
        raise argparse.ArgumentTypeError(
            f"invalid log level: '{value}' — choices: debug, info, warning, error, critical")
    return level


def parse_args() -> argparse.Namespace:
    parser: ArgumentParser = ArgumentParser(
        description = (
            "WoW Recipe Calculator\n\n"
            
            "GUI-driven WoW profession analyzer for material aggregation,"
            " cost calculation, and optimized crafting sequences."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--log-level",
        dest = "log_level",
        type = _parse_log_level,
        default = logging.INFO,
        metavar = "LEVEL",
        help = "Sets the logging level — choices: debug, info, warning, error, critical (default: warning)"
    )

    return parser.parse_args()
