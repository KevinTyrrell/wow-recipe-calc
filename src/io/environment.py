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

from typing import Any, Optional
from pathlib import Path


class Environment:
    _DEFAULT_FILE_EXT = "env"
    
    def __init__(self, file_basename: str, dir_path: Optional[str]=None, file_ext: Optional[str]=None) -> None:
        """
        Defines a key/value file, which is loadable/saveable from the storage medium
        
        :param file_basename: Filename name to save/load the environment as
        :param dir_path: Directory path to save the environment in, default: $CWD
        :param file_ext: Extension for the file (excluding dot), default: env
        """
        if file_ext is None: file_ext = self._DEFAULT_FILE_EXT
        self.__file_name: str = f"{file_basename}.{file_ext}"
        self.__file_path: Path = self._get_path(dir_path)
        
    def load(self) -> dict[str, str | int | float | bool]:
        """
        Throws an error on file not found, read errors, or malformed env
        
        Loads the environment from the storage medium
        
        :return: Loaded map of key/value pairs
        """
        env: dict[str, str | int | float | bool] = dict()
        with open(self.__file_path, "r") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Allow for comments
                if "=" not in line:
                    raise ValueError(f"Env '{self.__file_name}' is malformed. Line '{line_no}': {line}")
                key, value = line.split("=", 1)
                env[key] = self._parse_env_variable(value)
        return env
        
    def save(self, data: dict[Any, Any]) -> None:
        """
        Saves the environment to the storage medium
        
        :param data: Map of key/value pairs to be saved to the environment
        """
        str_by_key: dict[Any, str] = { k: str(k) for k in data }
        keys: list[str] = sorted(str_by_key.values(), key = lambda x: str_by_key[x])
        lines: list[str] = [
            f"{str_by_key[key]}={data[key]}" for key in
            sorted(data.keys(), key = lambda x: str_by_key[x])
        ]
        self.__file_path.write_text("\n".join(lines) + "\n")
                
    @staticmethod
    def _parse_env_variable(value: str) -> str | int | float | bool:
        try: return int(value) 
        except ValueError: pass
        try: return float(value) 
        except ValueError: pass
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        return value
        
    def _get_path(self, directory: Optional[str]=None) -> Path:
        path: Path = Path.cwd() if directory is None else Path(directory)
        if not path.exists(): raise ValueError(f"directory path does not exist: {path}")
        if not path.is_dir(): raise ValueError(f"path is not a valid directory: {path}")
        return path / self.__file_name
