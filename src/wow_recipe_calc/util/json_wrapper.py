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
from typing import TypeAlias
from abc import ABC
from collections.abc import Mapping, Iterator
from copy import deepcopy

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
JsonList: TypeAlias = list[JsonValue]
JsonObject: TypeAlias = dict[str, JsonValue]
JsonContainer: TypeAlias = JsonObject | JsonList


class _JsonObjectWrapper:
    _DATA_ATTR: str = self._DATA_ATTR

    def __init__(self, jso: Mapping[str, JsonValue]) -> None:
        data: dict[str, JsonValue] = dict()
        for key, value in jso.items():
            if isinstance(value, dict):   value = _JsonObjectWrapper(value)
            elif isinstance(value, list): value = _JsonListWrapper(value)
            data[key] = value
        object.__setattr__(self, self._DATA_ATTR, data)  # bypass __getattr__ entirely

    def __getattr__(self, name: str) -> JsonValue:
        data: dict[str, JsonValue] = object.__getattribute__(self, self._DATA_ATTR)
        try:
            return data[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def __getitem__(self, item: str) -> JsonValue:
        return object.__getattribute__(self, self._DATA_ATTR)[item]
    def __iter__(self) -> Iterator[str]:
        return iter(object.__getattribute__(self, self._DATA_ATTR))  # keys only, dict-consistent
    def __len__(self) -> int:
        return len(object.__getattribute__(self, self._DATA_ATTR))
    def __contains__(self, item: object) -> bool:
        return item in object.__getattribute__(self, self._DATA_ATTR)
    def __repr__(self) -> str:
        return f"JSO({object.__getattribute__(self, self._DATA_ATTR)!r})"
    def items(self):
        return object.__getattribute__(self, self._DATA_ATTR).items()
    def keys(self):
        return object.__getattribute__(self, self._DATA_ATTR).keys()
    def values(self):
        return object.__getattribute__(self, self._DATA_ATTR).values()


class _JsonListWrapper:
    def __init__(self, jso: list) -> None:
        self._data: list[JsonValue] = [
            _JsonObjectWrapper(item) if isinstance(item, dict)
            else _JsonListWrapper(item) if isinstance(item, list)
            else item for item in jso ]

    def __getitem__(self, index: int) -> JsonValue:
        return self._data[index]
    def __iter__(self) -> Iterator[JsonValue]:
        return iter(self._data)
    def __len__(self) -> int:
        return len(self._data)
    def __repr__(self) -> str:
        return f"JSL({self._data!r})"


JSW: TypeAlias = _JsonObjectWrapper | _JsonListWrapper


def wrap_json(container: JsonContainer) -> JSW:
    if isinstance(container, dict): return _JsonObjectWrapper(container)
    if isinstance(container, list): return _JsonListWrapper(container)
    raise ValueError(f"unsupported type cannot be JSON wrapped: {type(container).__name__}")


class JsonWrappable(ABC, Mapping[str, JsonValue]):  # must be ABC to avoid needing to implement mapping
    @staticmethod
    def wrap(obj: JsonContainer) -> JSW:
        """
        :param obj: Object to be wrapped as a JSO
        :return: Nested objects/list structure to enable field retrieval by attribute
        """
        return wrap_json(obj)

    def jso(self) -> JSW:
        """
        :return: JSON object wrapper instance, backed by a deep copy of the mapping
        """
        return self.wrap(deepcopy(dict(self)))
