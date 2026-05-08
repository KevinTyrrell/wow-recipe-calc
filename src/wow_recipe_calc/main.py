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

from logging import getLogger, Logger
from argparse import Namespace as ArgNamespace
from pathlib import Path
from typing import Optional, TextIO

from wow_recipe_calc.io.resources.project import Project
from wow_recipe_calc.util.log_manager import LogManager
from wow_recipe_calc.crafting_app import CraftingApp
from wow_recipe_calc.io.arguments import parse_args
from wow_recipe_calc.view.ui_manager import UIManager

logger: Logger = getLogger(__name__)

_LOG_RESOURCE: Path = Path("session.log")
_DEFAULT_FILE_ENCODING: str = "utf-8"

def main() -> None:
    args: ArgNamespace = parse_args()
    log_manager = LogManager(log_level = args.log_level)
    session: Optional[FileIO] = setup_logging(log_manager)
    app: CraftingApp = CraftingApp()
    app.populate_recipes()
    ui: UIManager = UIManager(app, log_manager)
    ui.show()
    # ------ cleanup ------
    if session is not None:
        session.close()

def setup_logging(logs: LogManager) -> Optional[TextIO]:
    resource: Path = Project.resource(_LOG_RESOURCE.stem, ext = _LOG_RESOURCE.suffix)
    try:
        session: TextIO = resource.open("w", encoding = _DEFAULT_FILE_ENCODING)
        logs.broadcast(session)  # begin writing logging records into the file
        return session
    except Exception as e:
        logger.error(f"failed to open log file '{resource}': {e}")
    return None


if __name__ == "__main__":
    main()
