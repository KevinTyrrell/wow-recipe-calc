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
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from typing import Any, TypeAlias
from abc import ABC
from collections.abc import Mapping
from copy import deepcopy


class _JsonObject:
    def __init__(self, jso: Mapping[str, Any]):
        self.__data: dict[str, Any] = dict()
        for key, value in jso.items():
            if isinstance(value, (dict, list)):
                value = _JsonObject(value) if isinstance(value, dict) else _JsonArray(value)
            self.__data[key] = value

    def __getattr__(self, name: str):  # safer alternative to setattr
        try: return self.__data[name]
        except KeyError: raise AttributeError(name)

    def __getitem__(self, item): return self.__data[item]
    def __iter__(self): yield from iter(self.__data.items())
    def __len__(self): return len(self.__data)
    def __repr__(self):
        return f"JSO({repr(self.__data)})"


class _JsonArray:
    def __init__(self, jso: list):
        self.__data = [
            _JsonObject(item) if isinstance(item, dict)
            else _JsonArray(item) if isinstance(item, list)
            else item for item in jso
    ]

    def __getitem__(self, index: int): return self.__data[index]
    def __iter__(self): yield from iter(self.__data)
    def __len__(self): return len(self.__data)
    def __repr__(self):
        return f"JSO({repr(self.__data)})"

JSO: TypeAlias = _JsonObject | _JsonArray


class JsonWrappable(ABC, Mapping[str, Any]):  # must be ABC to avoid needing to implement mapping
    @staticmethod
    def wrap(obj: Mapping[str, Any] | list[Any]) -> JSO:
        """
        :param obj: Object to be wrapped as a JSO
        :return: Nested objects/list structure to enable field retrieval by attribute
        """
        return _JsonObject(obj) if isinstance(obj, Mapping) else _JsonArray(obj)

    def jso(self) -> JSO:
        """
        :return: JSO instance, backed by a deep copy of the mapping
        """
        return self.wrap(deepcopy(dict(self)))
