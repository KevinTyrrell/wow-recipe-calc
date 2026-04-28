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

from functools import cache
from pathlib import Path

_ROOT_IDENTIFIERS: src = [  # known landmarks to ascertain location of project root
    "LICENSE", "src", "pyproject.toml", ".git", ".idea", "setup.py", "setup.cfg", ".vscode"
]


@cache
def get_project_root() -> Path:
    """
    :return: Path to the root folder of the current project
    """
    path: Path = Path(__file__)
    for parent in path.parents:
        for landmark in _ROOT_IDENTIFIERS:
            if (parent / landmark).exists():
                return parent
    raise FileNotFoundError("project root could not be ascertained")
