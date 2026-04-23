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

from typing import Any, Optional, Mapping, Iterator
from pathlib import Path
from types import MappingProxyType as ReadOnlyMap
from collections.abc import MutableMapping

EnvValue = str | int | float | bool


class Environment(MutableMapping[str, EnvValue]):
    _DEFAULT_FILE_EXT = "env"

    def __init__(self, file_basename: str, dir_path: Optional[str] = None, file_ext: Optional[str] = None) -> None:
        """
        Defines a key/value file, which is loadable/savable from the storage medium

        :param file_basename: Filename name to save/load the environment as
        :param dir_path: Directory path to save the environment in, default: $CWD
        :param file_ext: Extension for the file (excluding dot), default: env
        """
        if file_ext is None: file_ext = self._DEFAULT_FILE_EXT
        self.__file_name: str = f"{file_basename}.{file_ext}"
        self.__file_path: Path = self._get_path(dir_path)
        self.__data: dict[str, EnvValue] = dict()
        self.__data_ro: Mapping[str, EnvValue] = ReadOnlyMap(self.__data)

    # Required functions for MutableMapping extension
    def __getitem__(self, key: str) -> EnvValue:
        return self.__data[key]
    def __setitem__(self, key: str, value: EnvValue) -> None:
        if not isinstance(key, str):
            raise ValueError(f"environment key must be a str: {key}")
        self._validate_value_type(value)
        self.__data[key] = value
    def __delitem__(self, key: str) -> None:
        raise NotImplementedError("environment does not support deletion")
    def __iter__(self) -> Iterator[str]: return iter(self.__data)
    def __len__(self) -> int: return len(self.__data)
    def update(self, other: Mapping[str, EnvValue] | None = None, **kwargs: EnvValue) -> None:
        if other:
            for k, v in other.items(): self[k] = v
        for k, v in kwargs.items(): self[k] = v

    def load(self) -> Mapping[str, EnvValue]:
        """
        Attempts to load the environment from the storage medium

        Raises an error if environment file is not found, file reading
        error(s), malformed data, or if existing environment was not empty.

        :return: Read-only mapping of now-loaded key/value pairs
        """
        if self.__data:
            raise RuntimeError("environment already contains data; cannot load into a non-empty environment")
        with open(self.__file_path, "r") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"): continue  # allow for comments
                if "=" not in line:  # line is not a key/value pair
                    raise ValueError(f"env '{self.__file_name}' is malformed, line #{line_no}: {line}")
                key, raw_val = [part.strip() for part in line.split("=", 1)]
                if not raw_val: continue  # ignore empty values
                self.__data[key.lower()] = self._parse_value_from_str(raw_val)
        return self.__data_ro

    def save(self) -> None:
        """
        Saves the environment to the storage medium
        """
        self.__file_path.write_text(  # save key as uppercase, load as lowercase
            "\n".join(f"{k.upper()}={self.__data[k]}" for k in sorted(self.__data)) + "\n")

    @property
    def data(self) -> Mapping[str, EnvValue]:
        """
        Provides a read-only view of the environment data

        :return: Read-only mapping of internal data
        """
        return self.__data_ro

    @staticmethod
    def _validate_value_type(value: Any) -> None:
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"environment value's type is invalid: {value}")

    @staticmethod
    def _parse_value_from_str(value: str) -> EnvValue:
        value: str = value.strip()
        try: return int(value)  # test if integer
        except ValueError: pass
        try: return float(value)  # test if float
        except ValueError: pass
        if value.lower() in ("true", "false"):  # test if bool
            return value.lower() == "true"
        return value

    def _get_path(self, directory: Optional[str] = None) -> Path:
        path: Path = Path.cwd() if directory is None else Path(directory)
        if not path.exists(): raise ValueError(f"directory path does not exist: {path}")
        if not path.is_dir(): raise ValueError(f"path is not a valid directory: {path}")
        return path / self.__file_name
