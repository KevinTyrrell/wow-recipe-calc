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

from dataclasses import dataclass
from typing import Any

def _pred_non_neg_int(x: Any) -> bool:
    return isinstance(x, int) and x >= 0
def _pred_positive_int(x: Any) -> bool:
    return isinstance(x, int) and x > 0
def _pred_positive_float(x: Any) -> bool:
    return isinstance(x, float) and x > 0


@dataclass(frozen=True)
class Recipe:
    name: str
    learned: int
    levels: list[int]
    reagents: dict[int, int]
    product: int
    produces: float
    
    def __hash__(self) -> int:
        return hash((
            self.name,
            self.learned,
            tuple(self.levels),
            tuple(sorted(self.reagents.items())),
            self.product,
            self.produces,
        ))
    
    def __validate_name(self):
        if not isinstance(self.name, str):
            raise ValueError(f"recipe name is invalid: {self.name}")
    def __validate_levels(self):
        if not isinstance(self.levels, list):
            raise ValueError(f"recipe '{self.name}' levels are invalid: {self.levels}")
        last_level = 0
        for value in self.levels:
            if not _pred_non_neg_int(value):
                raise ValueError(f"recipe '{self.name}' levels must be a non-negative integer: {value} | {self.levels}")
            if value < last_level:
                raise ValueError(f"recipe '{self.name}' levels are non-monotonic: [{last_level}, {value}]")
            last_level = value
    def __validate_reagents(self):
        if not isinstance(self.reagents, dict):
            raise ValueError(f"recipe '{self.name}' reagents are invalid: {self.reagents}")
        for k, v in self.reagents.items():
            if not _pred_positive_int(k):
                raise ValueError(f"recipe '{self.name}' reagent's ID must be a positive integer: {k}")
            if not _pred_positive_int(v):
                raise ValueError(f"recipe '{self.name}' reagent's quantity must be a positive integer: {v}")
    def __validate_product(self):
        if not _pred_positive_int(self.product):
            raise ValueError(f"recipe '{self.name}' product must be a positive integer: {self.product}")
    def __validate_produces(self):
        if not _pred_positive_float(self.produces):
            raise ValueError(f"recipe '{self.name}' produces amount must be a positive float: {self.produces}")
    
    def __post_init__(self):
        self.__validate_name()
        self.__validate_levels()
        self.__validate_reagents()
        self.__validate_product()
        self.__validate_produces()
