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

from typing import TypeAlias, Optional, TypeVar
from logging import getLogger, Logger

from wow_recipe_calc.io.resources.project import MutableResource
from wow_recipe_calc.util.json_wrapper import JsonWrappable

JsonPrimitive: TypeAlias = str | int | float | bool | None  # in case user wants to distinguish obj vs. primitive
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

_T: TypeVar = TypeVar("_T", bound=JsonValue)

_DEFAULT_FILE_ENCODING: str = "utf-8"

def load_json(path: Path, expected: type[_T], fallback: bool = False) -> _T:
    """
    Attempts to load a JSON resource, constrained to top-level type, or type's default on fallback

    On failure, if fallback is False: hands off exceptions from json.load to caller.
    On failure, if fallback is True: logs exceptions, calls & returns expected.
    On success, if loaded JSON is not of expected type, raises ValueError.

    :param path: Path to the JSON resource
    :param expected: Enforced top-level loaded data type; called & returned as fallback
    :param fallback: If True, on load failure: log instead of raise, then call & return expected
    :return: Loaded JSON object on load success, or call & return expected if fallback is True
    """
    try:
        with path.open("r", encoding=_DEFAULT_FILE_ENCODING) as f:
            data: JsonValue = json.load(f)
            if not isinstance(data, expected):
                raise ValueError(f"JSON load type mismatch, expected: "
                                 f"{expected.__name__}, got {type(data).__name__}, path: {path}")
            return data
    except ValueError: raise  # ValueError cannot be handled whatsoever
    except FileNotFoundError as e:
        if not fallback: raise
        logger.info(f"JSON resource could not be found at path: {path}")
    except Exception as e:
        if not fallback: raise
        logger.warning(f"JSON resource '{path}' failed to load: {e}")
    return expected()


class JsonStore(MutableResource[str, JsonValue], JsonWrappable):
    _DEFAULT_FILE_EXT: str = "json"

    def __init__(self, file_stem: str, dir_path: Optional[Path | str] = None) -> None:
        """
        :param file_stem: Name of the file, excluding file extension
        :param dir_path: (Optional) Relative path, from the root, to the resource's directory
        """
        super().__init__(file_stem, dir_path)

    def load(self) -> None:
        """
        Attempts to load the JSON resource from the storage medium

        Raises an error if the file is not found, on file
        reading error(s), or if the file has malformed / invalid data.
        """
        self._data = load_json(self.file_path, dict, True)

    def save(self) -> None:
        """
        Saves the JSON resource to the storage medium
        """
        with self.file_path.open("w", encoding = _DEFAULT_FILE_ENCODING) as f:
            json.dump(self._data, f, indent = 4, ensure_ascii = False)
