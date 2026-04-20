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

from typing import Optional
from pathlib import Path


class StyleLoader:
    _DEFAULT_STYLE_PATH: str = "src/view/styles/"
    _DEFAULT_STYLE_EXT: str = "qss"
    _DEFAULT_ENCODING: str = "utf-8"

    def __init__(self, path: Optional[str] = None, ext: Optional[str] = None,
                 encoding: Optional[str] = None) -> None:
        """
        :param path: (Optional) Path to the directory containing the stylesheets, default: /src/view/styles
        :param ext: (Optional) Extension of the stylesheets to-be loaded, default: qss
        :param encoding: (Optional) Encoding of the stylesheet files, default: utf-8
        """
        self.__path: Path = Path(path or self._DEFAULT_STYLE_PATH)
        self.__encoding: str = encoding or self._DEFAULT_ENCODING
        if not self.__path.is_dir():
            raise NotADirectoryError(f"stylesheet directory does not exist: {self.__path}")
        if ext is not None:
            self.__ext: str = ext.lstrip(".").lower()
        else: self.__ext: str = self._DEFAULT_STYLE_EXT

    def load(self) -> str:
        """
        :return: Concatenation of all stylesheets in the specified directory
        """
        styles: list[str] = [
            file.read_text(encoding="utf-8")
            for file in self.__path.iterdir()
            if file.is_file() and file.suffix == f".{self.__ext}"
        ]

        if not styles:
            raise FileNotFoundError(
                f"no such stylesheet extension (.{self.__ext}) found in path: {self.__path}")
        return "\n".join(styles)
