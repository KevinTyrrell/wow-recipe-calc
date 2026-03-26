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

from src.crafts.Recipe import Recipe


class CraftSkiller:
    _INF: int = 10 ** 18  # Inf
    _DEFAULT_SKILL_LEVEL: int = 1
    
    def __init__(self, skill_lvl: Optional[int] = None, bound: Optional[int] = None) -> None:
        if bound is not None:
            if bound < 1: raise ValueError(f"skiller bound must be positive: {bound}")
            self.__bound: int = bound
        else: self.__bound: int = self._INF
        if skill_lvl is not None:
            if skill_lvl < 1:
                raise ValueError(f"skiller starting skill must be positive: {skill_lvl}")
            self.__skill: float = skill_lvl
        else: self.__skill: float = self._DEFAULT_SKILL_LEVEL
        if self.__skill < self.__bound:
            raise ValueError(f"skiller starting skill exceeds bound:
                             f"{self.__skill} [1, {self.__bound}]")
    
    #def craft(self, recipe: Recipe) -> None:
