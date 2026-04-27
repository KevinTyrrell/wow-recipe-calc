#  Copyright (C) 2026  Kevin Tyrrell
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
import json
import logging
from pathlib import Path

def _json_file(path_str: str):
    path = Path(path_str)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"path does not exist: {path_str}")
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"path is not a file: {path_str}")
    if path.suffix.lower() != ".json":
        raise argparse.ArgumentTypeError(f"path must be a .json file: {path_str}")
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(f"json file at path is malformed: {path_str} | {e}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "WoW Recipe Calculator\n\n"
            "This program reads two JSON files:\n"
            "1. All craftable recipes for a specific profession.\n"
            "2. The recipes you wish to craft, with quantities.\n\n"
            "After evaluation, a list of raw materials will be displayed for these crafts along with a list of items to-be-crafted, in order of skill level progression."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    # ---------------------------
    # Required positional arguments
    # ---------------------------
    parser.add_argument("profession_data_path",
        type=_json_file,
        help=(
            "Path to a JSON file containing all craftable recipes in a particular profession.\n"
            "Each recipe must have the keys: 'name', 'levels', 'reagents', 'product', 'produces'."
        )
    )

    parser.add_argument("required_crafts_path",
        type=_json_file,
        help=(
            "Path to a JSON file describing what craftable recipes you wish to make, and in what quantity.\n"
            "Must be a JSON object mapping recipe names (strings) to quantities (positive integers)."
        )
    )

    parser.add_argument("--log-level",
        dest="log_level",
        type=lambda x: getattr(logging, x),  # convert to logging param
        choices = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=logging.INFO,
        help="Sets the logging level, which is primarily used for debugging."
    )

    return parser.parse_args()
