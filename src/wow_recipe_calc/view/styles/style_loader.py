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
from pathlib import Path
from logging import Logger, getLogger

from wow_recipe_calc.io.resources.project import Project

logger: Logger = getLogger(__name__)


class StyleLoader:
    _DEFAULT_STYLE_EXT: str = "qss"
    _DEFAULT_FILE_ENCODING: str = "utf-8"

    def __init__(self, branch: Optional[Path] = None, ext: Optional[str] = None) -> None:
        """
        :param branch: (Optional) Relative path, from the root, to the stylesheet directory
        :param ext: (Optional) Target extension to match when loading stylesheets (default: qss)
        """
        self.__parent: Path = Project.resource(branch = branch)
        if ext is not None:
            self.__ext: str = ext.strip().lstrip(".")
        else: self.__ext: str = self._DEFAULT_STYLE_EXT

    def bundle_styles(self) -> str:
        """
        Bundles stylesheets in the specified stylesheet directory into one stylesheet.

        Stylesheets are sorted lexicographically, making bundling deterministic.
        If no stylesheets are found or could be loaded, returns empty string.

        :return: Concatenation of all stylesheets present in the stylesheet directory
        """
        styles: list[str] = list(self.styles)
        if not styles:
            logger.warning(f"no stylesheets found at path: {self.dir_path}")
            return str()
        return "\n".join(styles)


    @property
    def styles(self) -> Iterator[str]:
        for stylesheet in sorted(self.__parent.rglob(f"*.{self.__ext}")):
            try:
                yield stylesheet.read_text(encoding = self._DEFAULT_FILE_ENCODING)
            except Exception as e:
                logger.error(f"failed to load stylesheet '{stylesheet}': {e}")

    @property
    def dir_path(self) -> Path: return self.__parent
