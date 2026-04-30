#  Copyright (C) 2026  Kevin Tyrrell
# GUI-driven WoW profession analyzer for material aggregation, cost calculation, and optimized crafting sequences
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

import pickle

from time import time as unix_time
from logging import getLogger, Logger
from typing import TypeVar, Generic, Callable, Iterator
from dataclasses import dataclass

from wow_recipe_calc.io.resources.project import MutableResource

logger: Logger = getLogger(__name__)

_CKT: TypeVar = TypeVar("_CKT")
_CVT: TypeVar = TypeVar("_CVT")


@dataclass(frozen=True)
class CachePolicy(Generic[_CKT, _CVT]):
    ttl: int  # seconds until the entire cache is considered stale
    fetcher: Callable[[], dict[_CKT, _CVT]]  # called with no args, returns fresh data


class TTLCache(MutableResource[_CKT, _CVT], Generic[_CKT, _CVT]):
    _DEFAULT_FILE_EXT = "pkl"
    _DEFAULT_CACHE_DIR: str = "cache"

    def __init__(self, file_stem: str, policy: CachePolicy[_CKT, _CVT]) -> None:
        super().__init__(file_stem, self._DEFAULT_CACHE_DIR, self._DEFAULT_FILE_EXT)
        self.__policy: CachePolicy[_CKT, _CVT] = policy
        self.__expires: int = 0  # unix time in which the cache becomes stale

    @property
    def policy(self) -> CachePolicy[_CKT, _CVT]:
        """
        :return: Current caching policy for the mapping
        """
        return self.__policy

    @policy.setter
    def policy(self, value: CachePolicy[_CKT, _CVT]) -> None:
        """
        :param value: Replacement caching policy for the mapping
        """
        self.__policy = value

    def _check_ttl(self) -> None:
        """Purges and refetches data if the cache has gone stale"""
        ts: int = int(unix_time())
        if ts >= self.__expires:
            self._data.clear()
            logger.debug(f"TTL cache data expired, fetching new data")
            self._data.update(self.__policy.fetcher())
            self.__expires = ts + self.__policy.ttl

    # Freshness checks must take place on every read operation
    def __getitem__(self, key: _CKT) -> _CVT:
        self._check_ttl()
        return self._data.__getitem__(key)
    def __iter__(self) -> Iterator[_CKT]:
        self._check_ttl()
        return self._data.__iter__()
    def __len__(self) -> int:
        self._check_ttl()
        return self._data.__len__()
    def __contains__(self, key: _CKT) -> bool:
        self._check_ttl()
        return self._data.__contains__(key)

    def save(self) -> None:
        """
        Saves the environment to the storage medium
        """
        with self.file_path.open("wb") as f:
            pickle.dump((self._data, self.__expires), f)

    def load(self) -> None:
        """
        Attempts to load the cache from the storage medium

        Raises an error if cache file is not found, on file
        reading error(s), or if the file has malformed / invalid data.
        """
        with self.file_path.open("rb") as f:
            self._data, self.__expires = pickle.load(f)
