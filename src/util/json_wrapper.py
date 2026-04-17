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
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from json.decoder import JSONArray
from typing import Any, TypeAlias, Mapping


class _JsonObject:
    def __init__(self, jso: Mapping[str, Any]):
        self.__data: dict[str, Any] = dict()
        for key, value in jso.items():
            if isinstance(value, (dict, list)):
                value = _JsonObject(value) if isinstance(value, dict) else _JsonArray(value)
            self.__data[key] = value
            setattr(self, key, value)  # Treat key as a class attribute

    def __getitem__(self, item): return self.__data[item]
    def __iter__(self): yield from iter(self.__data.items())
    def __len__(self): return len(self.__data)
    def __repr__(self): return f"{self.__dict__}"


class _JsonArray:
    def __init__(self, jso: list):
        self.__data = [_JsonObject(item) if isinstance(item, dict) else item for item in jso]

    def __getitem__(self, index: int): return self.__data[index]
    def __iter__(self): yield from iter(self.__data)
    def __len__(self): return len(self.__data)
    def __repr__(self): return repr(self.__data)

JSO: TypeAlias = _JsonObject | _JsonArray

def wrap_json(jso: Mapping[str, Any] | list) -> JSO:
    """
    :param jso: JSON object to be wrapped
    :return: Nested objects/list structure to enable field retrieval by members
    """
    return _JsonObject(jso) if isinstance(jso, Mapping) else _JsonArray(jso)
