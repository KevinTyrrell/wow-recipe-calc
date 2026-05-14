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

from typing import Optional, Iterator
from logging import Logger, getLogger
from importlib.resources.abc import Traversable
from importlib.resources import files

logger: Logger = getLogger(__name__)


class StyleLoader:
    _DEFAULT_STYLE_EXT: str = "qss"
    _DEFAULT_FILE_ENCODING: str = "utf-8"

    def __init__(self, module: str, ext: Optional[str] = None) -> None:
        """
        :param module: Dotted module string pointing to the resource root (e.g. "wow_recipe_calc.resources")
        :param branch: (Optional) Sub-path within the module to the stylesheet directory
        :param ext: (Optional) Target extension to match when loading stylesheets (default: qss)
        """
        self.__parent: Traversable = files(module)
        self.__ext: str = ext.strip().lstrip(".") if ext is not None else self._DEFAULT_STYLE_EXT

    def bundle_styles(self) -> str:
        """
        Bundles stylesheets in the specified stylesheet directory into one stylesheet.

        Stylesheets are sorted lexicographically, making bundling deterministic.
        If no stylesheets are found or could be loaded, returns empty string.

        :return: Concatenation of all stylesheets present in the stylesheet directory
        """
        styles: list[str] = list(self.styles)
        if not styles:
            logger.warning(f"no stylesheets found at path: {self.__parent}")
            return str()
        return "\n".join(styles)

    @property
    def styles(self) -> Iterator[str]:
        for stylesheet in sorted(self._walk(self.__parent), key = lambda p: p.name):
            if not stylesheet.name.endswith(f".{self.__ext}"): continue  # ignore non-stylesheets
            try:
                yield stylesheet.read_text(encoding = self._DEFAULT_FILE_ENCODING)
            except Exception as e:
                logger.error(f"failed to load stylesheet '{stylesheet.name}': {e}")

    def _walk(self, node: Traversable) -> Iterator[Traversable]:  # rglob doesn't work on traversable
        for child in node.iterdir():
            if child.is_dir(): yield from self._walk(child)
            else: yield child

    @property
    def dir_path(self) -> Traversable: return self.__parent
