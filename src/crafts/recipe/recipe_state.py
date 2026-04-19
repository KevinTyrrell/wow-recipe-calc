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

from collections.abc import MutableMapping, Mapping, Iterator
from typing import Optional, Callable
from types import MappingProxyType as ReadOnlyMap

from src.crafts.recipe import Recipe
from src.io.environment import Environment


class _RecipeState:
    def __init__(self, data: Optional[Mapping[Recipe, int]] = None) -> None:
        self._data: dict[Recipe, int] = dict(data or { })
        self._data_ro: Mapping[Recipe, int] = ReadOnlyMap(self._data)


class RecipeStateObserver(_RecipeState):
    def __init__(self, data: Optional[Mapping[Recipe, int]] = None) -> None:
        super().__init__(data)
        self.__listeners: set[Callable[[Recipe, Optional[int]], None]] = set()

    def listen(self, callback: Callable[[Recipe, Optional[int]], None]) -> None:
        self.__listeners.add(callback)

    def ignore(self, callback: Callable[[Recipe, Optional[int]], None]) -> None:
        self.__listeners.discard(callback)

    def _fire_listeners(self, recipe: Recipe, quantity: int) -> None:
        for listener in self.__listeners:
            listener(recipe, quantity)


class RecipeStateViewer(RecipeStateObserver, Mapping[Recipe, int]):
    def __init__(self, data: Optional[Mapping[Recipe, int]] = None) -> None:
        super().__init__(data)

    @property
    def state(self) -> Mapping[Recipe, int]:
        return self._data_ro

    def get(self, recipe: Recipe, default: int = 0) -> Optional[int]:
        return self._data.get(recipe, default)
    def __getitem__(self, key: Recipe) -> int: return self._data[key]
    def __iter__(self) -> Iterator[Recipe]: return iter(self._data)
    def __len__(self) -> int: return len(self._data)
    def __contains__(self, key: object) -> bool: return key in self._data


class RecipeStateCore(RecipeStateViewer, MutableMapping[Recipe, int]):
    def __init__(self, data: Optional[Mapping[Recipe, int]] = None) -> None:
        super().__init__(data)

    def pop(self, key: Recipe, default: object = ...) -> object:
        if key in self._data:
            return self._delete(key)
        if default is ...: raise KeyError(key)
        return default

    def __delitem__(self, key: Recipe) -> None: self._deleter(key)
    def __setitem__(self, key: Recipe, value: int) -> None:
        if value <= 0:
            self._deleter(key)
        else: self._setter(key, value)

    def _deleter(self, key: Recipe) -> int:
        value: int = self._data.pop(key)  # allow KeyError
        self._notify(key, None)
        return value

    def _setter(self, key: Recipe, value: int) -> None:
        self._data[key] = value
        self._notify(key, value)
