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

import logging

from argparse import Namespace as ArgNamespace

from src.crafting_app import CraftingApp
from src.io.arguments import parse_args
from src.crafts.craft_planner import CraftPlan

logging.basicConfig(
    level=logging.DEBUG,  # or INFO, etc.
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)

def main():
    args: ArgNamespace = parse_args()
    app: CraftingApp = CraftingApp(args)
    app.populate_recipes()
    plan: CraftPlan = app.run_planner()
    
if __name__ == "__main__":
    main()
