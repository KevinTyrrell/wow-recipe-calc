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
from importlib.resources import files
from importlib.resources.abc import Traversable


class StyleLoader:
    _DEFAULT_STYLE_EXT: str = "qss"
    _DEFAULT_ENCODING: str = "utf-8"

    def __init__(self, style_dir_importlib_res_path: str, ext: Optional[str] = None) -> None:
        """
        Path to stylesheet directory must be an importlib resource path.
        e.g.: "wow_recipe_calc.view.styles"
        Each section must be a valid package, excluding the last.

        :param style_dir_importlib_res_path: importlib resource path
        :param ext: (Optional) Extension of the stylesheets to-be loaded, default: qss
        """
        self.__trav: Traversable = files(style_dir_importlib_res_path)
        if not self.__trav.is_dir():
            raise NotADirectoryError(f"stylesheet directory does not exist: {self.__trav}")
        if ext is not None:
            self.__ext: str = ext.lstrip(".").lower()
        else: self.__ext: str = self._DEFAULT_STYLE_EXT

    def load(self) -> str:
        """
        :return: Concatenation of all stylesheets in the specified directory
        """
        styles: list[str] = list(self._walk_styles(self.__trav))
        if not styles: raise FileNotFoundError(
            f"no such stylesheet extension (.{self.__ext}) found in path: {self.__path}")
        return "\n".join(styles)

    def _walk_styles(self, t: Traversable) -> Generator[str, None, None]:
        if t.is_file():
            if t.name.endswith(self.__ext): yield t.read_text()
        elif t.is_dir():  # sort so that loading becomes deterministic
            for child in sorted(t.iterdir(), key = lambda x: x.name):
                yield from self._walk_styles(child)
