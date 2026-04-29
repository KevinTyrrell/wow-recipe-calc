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

from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping, MutableMapping
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Generic, Optional, TypeVar

_KT: TypeVar = TypeVar("_KT")
_VT: TypeVar = TypeVar("_VT")

_ROOT_LANDMARKS: list[str] = [
    "LICENSE", "src", "pyproject.toml", ".git", ".idea", "setup.py", "setup.cfg", ".vscode"
]


class Project(Enum):
    APP = "APP"  # Singleton enum

    @staticmethod
    @cache
    def root() -> Path:
        for parent in Path(__file__).parents:
            if any((parent / lm).exists() for lm in _ROOT_LANDMARKS):
                return parent
        raise FileNotFoundError("project root could not be ascertained")

    @staticmethod
    @cache
    def name() -> str:
        return Project._read_pyproject("name", fallback="unknown")

    @staticmethod
    @cache
    def version() -> str:
        return Project._read_pyproject("version", fallback="0.0.0")

    @staticmethod
    def resource(relative: str) -> Path:
        """Resolve a path relative to the project root."""
        return Project.root() / relative

    @staticmethod
    def _read_pyproject(key: str, *, fallback: str) -> str:
        try: import tomllib  # stdlib from 3.11
        except ImportError:
            try: import tomli as tomllib  # type: ignore[no-redef]
            except ImportError: return fallback
        pyproject: Path = Project.root() / "pyproject.toml"
        if not pyproject.exists():
            return fallback
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get(key, fallback)


# ------------------------------------------------------------------
# Base class #1 — read-only persistent resource
# ------------------------------------------------------------------

class Resource(ABC, Mapping[_KT, _VT], Generic[_KT, _VT]):
    """
    A read-only mapping backed by a fixed location on disk.

    Owns path resolution and the load contract only.
    Subclasses pin _KT and _VT and implement load().
    """

    _DEFAULT_FILE_EXT: str  # subclasses must declare; omitting raises AttributeError on init

    def __init__(
        self,
        file_basename: str,
        dir_path: Optional[Path | str] = None,
        file_ext: Optional[str] = None,
    ) -> None:
        ext = file_ext or self._DEFAULT_FILE_EXT
        self._file_path: Path = self._resolve_path(file_basename, dir_path, ext)
        self._data: dict[_KT, _VT] = {}

    @abstractmethod
    def load(self) -> None:
        """Deserialize from disk into self._data."""

    # Mapping — subclasses inherit these for free
    def __getitem__(self, key: _KT) -> _VT:
        return self._data[key]

    def __iter__(self) -> Iterator[_KT]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    @property
    def file_path(self) -> Path:
        return self._file_path

    # Path resolution — one place, forever
    def _resolve_path(
        self,
        basename: str,
        directory: Optional[Path | str],
        ext: str,
    ) -> Path:
        dir_path = Path(directory) if directory is not None else self._default_dir()
        dir_path = dir_path.resolve()
        if not dir_path.exists():
            raise ValueError(f"directory does not exist: {dir_path}")
        if not dir_path.is_dir():
            raise ValueError(f"path is not a directory: {dir_path}")
        return dir_path / f"{basename}.{ext}"

    def _default_dir(self) -> Path:
        """Override to change the default directory (e.g. Path.cwd())."""
        return Project.root()


# ------------------------------------------------------------------
# Base class #2 — read-write persistent resource
# ------------------------------------------------------------------

class MutableResource(Resource[_KT, _VT], MutableMapping[_KT, _VT]):
    """
    A mutable mapping backed by a fixed location on disk.

    Adds write operations and the save contract.
    Subclasses may override __setitem__ / __delitem__ to enforce
    type constraints or disallow deletion.
    """

    @abstractmethod
    def save(self) -> None:
        """Serialize self._data back to disk at self._file_path."""

    def __setitem__(self, key: _KT, value: _VT) -> None:
        self._data[key] = value

    def __delitem__(self, key: _KT) -> None:
        del self._data[key]