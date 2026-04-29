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

import pickle

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Callable
from time import time as unix_time
from logging import getLogger, Logger

from io.project_info import get_project_root

logger: Logger = getLogger(__name__)


@dataclass
class CachePolicy:
    ttl: Optional[int]  # Seconds for the data to persist for
    fetcher: Callable[[Any], Optional[Any]]  # fetcher(key) -> value


@dataclass
class _DatabaseEntry:
    data: Any
    expires: Optional[int]


class LocalCache:
    _DEFAULT_DB_FILE_EXT: str = "pkl"
    
    def __init__(self, file_basename: str, dir_path: Optional[str] = None, file_ext: Optional[str] = None) -> None:
        """
        Constructs a key/value cache, which is manually savable to the storage medium
        
        :param file_basename: Filename of the database to cache response data
        :param dir_path: Directory path to save the database in, default: $CWD
        :param file_ext: Extension for the database (excluding dot), default: pkl
        """
        if file_ext is None: file_ext = self._DEFAULT_DB_FILE_EXT
        self.__file_name: str = f"{file_basename}.{file_ext}"
        self.__file_path: Path = self._get_path(dir_path)
        self.__db: dict[Any, _DatabaseEntry] = self._load_database()
        
    def fetch(self, key: Any, policy: CachePolicy) -> Optional[Any]:
        """
        Retrieves the value associated with the specified key in the database
        
        If no such key exists, or the pairing has become stale, a new value is generated.
        Pairings become stale when their time-to-live (TTL) has been exceeded (None: Never Stale).
        Generated values are created using the fetcher provided in the CachePolicy instance.
        If the fetcher returns None, the lookup is considered to have failed, thus returns None.
        
        :param key: Key to retrieve, or generate new value for if stale
        :param policy: Fetching / Cleaning policy used for generating new values
        """
        ts: int = int(unix_time())
        entry: Optional[_DatabaseEntry] = self.__db.get(key)
        if entry is not None:
            if entry.expires is not None and entry.expires <= ts:
                logger.debug(f"cached key has expired: key={key}, expires={entry.expires}, ts={ts}")
                del self.__db[key]  # Eject stale entry
            else: return entry.data
        data: Optional[Any] = policy.fetcher(key)
        if data is not None:
            expires: Optional[int] = None if policy.ttl is None else ts + policy.ttl
            self.__db[key] = _DatabaseEntry(data, expires)
        return data
            
    def clean(self) -> None:
        """
        Ejects stale entries from the db.
        
        Called on load or on-demand. Entries with 'expires' as 'None' are not removed
        """
        ts: int = int(unix_time())
        stale: set[Any] = {
            k for k, v in self.__db.items()
            if v.expires is not None and v.expires <= ts
        }
        for k in stale:  
            del self.__db[k]  # Clean up expired keys in the db

    def save(self) -> None:
        """
        Saves all loaded requests to a local database
        """
        with open(self.__file_path, "wb") as f:
            pickle.dump(self.__db, f)

    @property
    def file_name(self) -> str: return self.__file_name
    @property
    def file_path(self) -> Path: return self.__file_path
    
    def _get_path(self, directory: Optional[str]=None) -> Path:
        path: Path = (get_project_root() if directory is None else Path(directory)).resolve()
        if not path.exists(): raise ValueError(f"directory path does not exist: {path}")
        if not path.is_dir(): raise ValueError(f"path is not a valid directory: {path}")
        return path / self.__file_name
        
    def _load_database(self) -> dict[Any, _DatabaseEntry]:
        if self.__file_path.exists():
            with open(self.__file_path, "rb") as f:
                return pickle.load(f)
        return dict()
