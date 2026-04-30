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

from copy import deepcopy

from wow_recipe_calc.io.resources.project import MutableResource
from wow_recipe_calc.util.json_wrapper import wrap_json, JSO

JsonPrimitive = str | int | float | bool  # TODO: Include NoneType?
JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


class JsonStore(MutableResource[str, JsonValue]):
    _DEFAULT_FILE_EXT: str = "json"
    _DEFAULT_FILE_ENCODING: str = "utf-8"

    def jso(self) -> JSO:
        """
        :return: JSO instance, backed by a copy of the store object
        """
        return wrap_json(deepcopy(self._data))

    def load(self) -> None:
        """
        Attempts to load the JSON resource from the storage medium

        Raises an error if the file is not found, on file
        reading error(s), or if the file has malformed / invalid data.
        """
        with self.file_path.open("r", encoding = self._DEFAULT_FILE_ENCODING) as f:
            data: dict[str, JsonValue] = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"expected a JSON object, got {type(data).__name__}, path: {self.file_path}")
        self._data = data

    def save(self) -> None:
        """
        Saves the JSON resource to the storage medium
        """
        with self.file_path.open("w", encoding = self._DEFAULT_FILE_ENCODING) as f:
            json.dump(self._data, f, indent = 4, ensure_ascii = False)
