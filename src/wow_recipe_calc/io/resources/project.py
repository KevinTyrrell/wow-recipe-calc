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

from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, MutableMapping
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Generic, Optional, TypeVar, overload, runtime_checkable, Protocol

_KT: TypeVar = TypeVar("_KT")  # key of each pairing
_VT: TypeVar = TypeVar("_VT")  # value of each pairing

_T: TypeVar = TypeVar("_T")  # # Needed for wild-card param of MutableMapping.pop
_POP_SENTINEL: object = object()  # distinguishes between 'None' 2nd param and missing 2nd param

_TOML_CONFIG_BASENAME: str = "pyproject.toml"
_TOML_CONFIG_NAME: str = "name"
_TOML_CONFIG_VERSION: str = "version"
_TOML_CONFIG_KEY: str = "project"
_ROOT_LANDMARKS: list[str] = [
    "LICENSE", "src", "pyproject.toml", ".git", ".idea", "setup.py", "setup.cfg", ".vscode" ]


class Project(Enum):
    APP = "APP"  # Singleton enum

    @staticmethod
    @cache
    def root() -> Path:
        """
        :return: Path to the root folder of the project, detected by landmark files
        """
        for parent in Path(__file__).parents:
            if any((parent / lm).exists() for lm in _ROOT_LANDMARKS):
                return parent
        raise FileNotFoundError("project root could not be ascertained")

    @staticmethod
    @cache
    def name() -> str:
        """
        :return: Name of the project, via the pyproject.toml configuration file
        """
        return Project._read_pyproject(_TOML_CONFIG_NAME)

    @staticmethod
    @cache
    def version() -> str:
        """
        :return: Version of the project, via the pyproject.toml configuration file
        """
        return Project._read_pyproject(_TOML_CONFIG_VERSION)

    @staticmethod
    def resource(relative: str) -> Path:
        """
        Resolves a path relative to the project root folder

        :param relative: Relative path to be resolved from root
        :return: Resolved path to the resource
        """
        return (Project.root() / relative).resolve()

    @staticmethod
    @cache
    def _read_pyproject(key: str) -> str:
        try: import tomllib
        except ImportError:  # check older python version's name
            import tomli as tomllib    # type: ignore[no-redef]
        pyproject: Path = Project.root() / _TOML_CONFIG_BASENAME
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        return data[_TOML_CONFIG_KEY][key]


@runtime_checkable
class Loadable(Protocol):
    def load(self) -> None: ...


@runtime_checkable
class Saveable(Protocol):
    def save(self) -> None: ...


class Resource(ABC, Loadable, Mapping[_KT, _VT], Generic[_KT, _VT]):
    _DEFAULT_FILE_EXT: str  # subclasses must declare; omitting raises AttributeError on init

    def __init__(self, file_stem: str,
                 dir_path: Optional[Path | str] = None, file_ext: Optional[str] = None) -> None:
        """
        :param file_stem: Name of the file, excluding file extension
        :param dir_path: (Optional) Relative path, from the root, to the resource's directory
        :param file_ext: (Optional) File extension, classes defined default if not provided
        """
        ext: str = file_ext or self._DEFAULT_FILE_EXT
        self.__file_path: Path = self._resolve_path(file_stem, dir_path, ext)
        self._data: dict[_KT, _VT] = dict()

    @abstractmethod
    def load(self) -> None:
        """
        Loads the resource from the storage medium
        """

    # Mapping implementation
    def __getitem__(self, key: _KT) -> _VT: return self._data[key]
    def __iter__(self) -> Iterator[_KT]: return iter(self._data)
    def __len__(self) -> int: return len(self._data)
    def __contains__(self, key: _KT) -> bool: return key in self._data
    def keys(self): return self._data.keys()
    def items(self): return self._data.items()
    def values(self): return self._data.values()

    @property
    def file_path(self) -> Path:
        """
        :return: Resolved path to the resource
        """
        return self.__file_path

    @staticmethod
    def _resolve_path(file_stem: str, directory: Optional[Path | str], ext: str) -> Path:
        dir_path: Path = Project.root() if directory is None else Path(directory).resolve()
        if not dir_path.exists():
            raise ValueError(f"directory does not exist: {dir_path}")
        if not dir_path.is_dir():
            raise ValueError(f"path is not a directory: {dir_path}")
        return dir_path / f"{file_stem}.{ext}"


class MutableResource(Saveable, Resource[_KT, _VT], MutableMapping[_KT, _VT]):
    def __init__(self, file_stem: str,
                 dir_path: Optional[Path | str] = None, file_ext: Optional[str] = None) -> None:
        Resource.__init__(self, file_stem, dir_path, file_ext)

    @abstractmethod
    def save(self) -> None:
        """
        Saves the resource to the storage medium
        """

    # MutableMapping implementation
    def __setitem__(self, key: _KT, value: _VT) -> None: self._data[key] = value
    def __delitem__(self, key: _KT) -> None: del self._data[key]
    def popitem(self) -> tuple[_KT, _VT]: return self._data.popitem()
    def clear(self) -> None: self._data.clear()

    @overload
    def pop(self, key: _KT) -> _VT: ... # overloads needed in order to annotate default param correctly
    @overload
    def pop(self, key: _KT, default: _T) -> _T | _VT: ...  # noqa / pylint: disable=...
    def pop(self, key, default = _POP_SENTINEL):
        if default is _POP_SENTINEL:  # confirmation that default was not passed in
            return self._data.pop(key)
        return self._data.pop(key, default)

    def update(self, other: Mapping[_KT, _VT] = (), **kwargs: _VT) -> None:
        for key, value in (other.items() if isinstance(other, Mapping) else other):
            self[key] = value
        for key, value in kwargs.items():
            self[key] = value  # type: ignore[assignment]

    def setdefault(self, key: _KT, default: _VT = None) -> _VT:
        if default is None:  # TODO: implement NoneType as value pairing, as dict allows it
            raise ValueError(f"resource value of NoneType is not supported, where key: {key}")
        if key not in self._data:
            self._data[key] = default
        return self._data[key]
