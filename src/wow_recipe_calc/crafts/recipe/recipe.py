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
from dataclasses import dataclass
from typing import Mapping, Optional
from types import MappingProxyType as ReadOnlyMap
from logging import getLogger, Logger

logger: Logger = getLogger(__name__)


@dataclass(frozen=True)
class RecipeJson:
    name: str
    learned: int
    yellow: int
    gray: int
    reagents: list[list[int]]
    product: int
    produces: float
    sources: list[int]
    specialization: Optional[str] = None


@dataclass(frozen=True)
class Recipe:
    name: str
    learned: int
    yellow: int
    gray: int
    reagents: Mapping[int, int]
    product: int
    produces: float
    sources: tuple[int, ...]
    specialization: Optional[str] = None

    def __hash__(self) -> int:
        return hash((
            self.name,
            self.learned,
            self.yellow,
            self.gray,
            # sorting ensures consistent hashes
            tuple(sorted(self.reagents.items())),
            self.product,
            self.produces,
            tuple(self.sources),
            self.specialization))

    @classmethod
    def from_json(cls, r: RecipeJson) -> Recipe:
        logger.debug(f"parsing json recipe {r}")
        if not r.name: raise ValueError("name must not be empty")
        if not (r.learned > 0 and r.yellow > 0 and r.gray > 0):
            raise ValueError(f"learned, yellow, gray must all be positive, received: {r.learned}, {r.yellow}, {r.gray}")
        if not (r.learned <= r.yellow <= r.gray):
            raise ValueError(f"skill levels cannot be a non-monotonic sequence: {r.learned}, {r.yellow}, {r.gray}")
        if not r.reagents: raise ValueError("reagents must not be empty")
        for pair in r.reagents:
            if len(pair) < 2:
                raise ValueError(f"reagent entry must be a pair of [item_id, quantity], received: {pair}")
            if pair[0] <= 0 or pair[1] <= 0:
                raise ValueError(f"reagent item ID and quantity must be positive, received: {pair}")
        if r.product <= 0: raise ValueError(f"product must be positive, received: {r.product}")
        if r.produces < 1:
            raise ValueError(f"produces must be >= 1, received: {r.produces}")
        if not r.sources: raise ValueError("sources must not be empty")
        if any(s < 0 for s in r.sources): raise ValueError("source IDs must be positive")
        if r.specialization is not None and not r.specialization:
            raise ValueError("specialization must not be empty string")
        return cls(
            name=r.name,
            learned=r.learned,
            yellow=r.yellow,
            gray=r.gray,  # reagents: read only dict
            reagents=ReadOnlyMap({pair[0]: pair[1] for pair in r.reagents}),
            product=r.product,
            produces=r.produces,
            sources=tuple(r.sources),
            specialization=r.specialization,
        )
