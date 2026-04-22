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

from argparse import Namespace as ArgNamespace

from src.util.log_manager import LogManager
from src.crafting_app import CraftingApp
from src.io.arguments import parse_args
from src.view.ui_manager import UIManager


def main() -> None:
    args: ArgNamespace = parse_args()
    log_manager = LogManager(log_level = args.log_level)
    app: CraftingApp = CraftingApp(args)
    app.populate_recipes()
    ui: UIManager = UIManager(app, log_manager)
    ui.show()

if __name__ == "__main__":
    main()
