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

from functools import cached_property
from pathlib import Path
from logging import getLogger, Logger

from io.resources.project import Saveable, Loadable, Project
from io.resources.json_store import load_json, save_json
from wow_recipe_calc.crafts.recipe.recipe import Recipe
from wow_recipe_calc.io.enums import Expansion, Profession
from util.json_wrapper import JsonValue, wrap_json, JSW

logger: Logger = getLogger(__name__)


class RecipeBook:
    def __init__(self, expac: Expansion, prof: Profession) -> None:
        self.__expac: Expansion = expac
        self.__prof: Profession = prof
        self.__book: _RecipeBookData = _RecipeBookData(prof.resource, expac.navigation)
        logger.debug(f"attempting to load {prof.name} recipes from {expac.name}")
        self.__book.load()
        # TODO: Check if loaded content exists -- if not, request from server & save

    @staticmethod
    def parse_recipe(data: JsonValue) -> Recipe:
        jso: JSW = wrap_json(data)
        return Recipe(
            jso.label,  # name
            next(iter(jso.levels)),  # level learned at
            list(jso.levels)[1:],  # orange/yellow/green/gray levels
            { int(k): v for k, v in jso.reagents },  # reagent map
            int(jso.product),  # product item id
            jso.produces)  # yield count

    @cached_property
    def recipes(self) -> tuple[Recipe, ...]:
        return tuple(Recipe(self.parse_recipe(e))  for e in self.__book)


class _RecipeBookData(MutableSequence[JsonValue], Saveable, Loadable):
    _DEFAULT_RESOURCE_EXT: str = "json"
    _RESOURCE: Path = Path("data/recipes")

    def __init__(self, file_stem: str, parent_dir: str) -> None:
        self.__file_path: Path = Project.resource(file_stem, self._RESOURCE / parent_dir, self._DEFAULT_RESOURCE_EXT)
        self.__data: list[JsonValue] = list()

    def load(self) -> None:
        """Attempts to load the recipe data from the storage medium"""
        self.__data = load_json(self.__file_path, list, True)

    def save(self) -> None:
        """Attempts to save the recipe data from the storage medium"""
        try:
            save_json(self.__file_path, self.__data)
        except Exception as e:
            logger.error(f"failed to save recipe data '{self.file_path}': {e}")

    # MutableSequence implementation
    def __len__(self) -> int: return len(self.__data)
    def __getitem__(self, index: int) -> JsonValue: return self.__data[index]
    def __setitem__(self, index: int, value: JsonValue) -> None: self.__data[index] = value
    def __delitem__(self, index: int) -> None: del self.__data[index]
    def insert(self, index: int, value: JsonValue) -> None: self.__data.insert(index, value)

    @property
    def file_path(self) -> Path: return self.__file_path
