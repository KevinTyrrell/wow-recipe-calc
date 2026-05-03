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

from pathlib import Path

from wow_recipe_calc.crafts.recipe.recipe import Recipe
from wow_recipe_calc.io.resources.project import Resource
from wow_recipe_calc.io.enums import Expansion, Profession
from wow_recipe_calc.util.json_wrapper import JsonWrappable


class RecipeProvider(Resource[str, JsonValue], JsonWrappable):
    _DEFAULT_FILE_EXT: str = "json"
    _RESOURCE: Path = Path("data/recipes")
    _DEFAULT_FILE_ENCODING: str = "utf-8"

    def __init__(self, expac: Expansion, prof: Profession) -> None:
        super().__init__(prof.resource, self._RESOURCE / expac.navigation)
        self.__expac: Expansion = expac
        self.__prof: Profession = prof

    def load(self) -> None:
        """Attempts to load the json file from the storage medium"""
        with self.file_path.open("r", encoding = self._DEFAULT_FILE_ENCODING) as f:
            data: dict[str, JsonValue] = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"expected a JSON object, got {type(data).__name__}, path: {self.file_path}")
        self._data = data
