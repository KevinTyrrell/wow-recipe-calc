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

import json
from functools import cached_property

from pathlib import Path
from typing import Optional

from io.resources.project import Saveable, Loadable
from util.json_wrapper import JsonValue
from wow_recipe_calc.crafts.recipe.recipe import Recipe
from wow_recipe_calc.io.enums import Expansion, Profession
from wow_recipe_calc.util.json_wrapper import JsonWrappable


class RecipeBook:
    def __init__(self, expac: Expansion, prof: Profession) -> None:
        self.__expac: Expansion = expac
        self.__prof: Profession = prof

    @cached_property
    def recipes(self) -> tuple[Recipe, ...]:
        return tuple()


class _RecipeBookData(MutableSequence[JsonValue], Saveable, Loadable):
    _DEFAULT_RESOURCE_EXT: str = "json"
    _RESOURCE: Path = Path("data/recipes")

    def __init__(self, file_stem: str, parent_dir: str) -> None:




