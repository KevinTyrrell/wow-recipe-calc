# Copyright (C) 2026 Kevin Tyrrell
# GUI-driven WoW profession analyzer for material aggregation, cost calculation, and optimized crafting sequences
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>

from __future__ import annotations
from enum import Enum
from typing import Self, NamedTuple, Optional
from collections.abc import Iterator


class ExpansionData(NamedTuple):
    ordinal: int
    label: str
    navigation: str
    portal: str


_expac_reverse: dict[int, Expansion] = dict()


class Expansion(Enum):
    CLASSIC = ExpansionData(1, "World of Warcraft", "classic", "data/classic")
    BURNING_CRUSADE = ExpansionData(2, "The Burning Crusade", "tbc", "data/tbc")
    WRATH = ExpansionData(3, "Wrath of the Lich King", "wotlk", "data/wotlk")
    CATACLYSM = ExpansionData(4, "Cataclysm", "cata", "data/cata")
    MISTS = ExpansionData(5, "Mists of Pandaria", "mop-classic", "data/mop-classic")
    WARLORDS = ExpansionData(6, "Warlords of Draenor", "retail", "data/retail")
    LEGION = ExpansionData(7, "Legion", "retail", "data/retail")
    BATTLE_FOR_AZEROTH = ExpansionData(8, "Battle for Azeroth", "retail", "data/retail")
    SHADOWLANDS = ExpansionData(9, "Shadowlands", "retail", "data/retail")
    DRAGONFLIGHT = ExpansionData(10, "Dragonflight", "retail", "data/retail")
    WAR_WITHIN = ExpansionData(11, "The War Within", "retail", "data/retail")
    MIDNIGHT = ExpansionData(12, "Midnight", "retail", "data/retail")
    LAST_TITAN = ExpansionData(13, "The Last Titan", "retail", "data/retail")

    def __init__(self, *_):  # ignore args
        # Setup reverse mapping via ordinal
        _expac_reverse[self.value.ordinal - 1] = self

    @classmethod
    def _missing_(cls, value: object) -> Optional[Self]:  # reverse lookup by ordinal
        if not isinstance(value, int): return None
        return _expac_reverse.get(value - 1)

    # "Shim" methods to avoid needing to call .value
    @property
    def ordinal(self) -> int: return self.value.ordinal
    @property
    def label(self) -> str: return self.value.label
    @property
    def navigation(self) -> str: return self.value.navigation
    @property
    def portal(self) -> str: return self.value.portal


class ProfessionData(NamedTuple):
    ordinal: int
    label: str
    resource: str
    portal: str  # web portal entry-point
    expansion: int  # expansion ID of introduction


_prof_reverse: dict[int, Profession] = dict()


class Profession(Enum):
    ALCHEMY = ProfessionData(1, "Alchemy", "alchemy", "professions/alchemy", 1)
    BLACKSMITHING = ProfessionData(2, "Blacksmithing", "blacksmithing", "professions/blacksmithing", 1)
    COOKING = ProfessionData(3, "Cooking", "cooking", "secondary-skills/cooking", 1)
    ENCHANTING = ProfessionData(4, "Enchanting", "enchanting", "professions/enchanting", 1)
    ENGINEERING = ProfessionData(5, "Engineering", "engineering", "professions/engineering", 1)
    INSCRIPTION = ProfessionData(6, "Inscription", "inscription", "professions/inscription", 3)
    JEWELCRAFTING = ProfessionData(7, "Jewelcrafting", "jewelcrafting", "professions/jewelcrafting", 2)
    LEATHERWORKING = ProfessionData(8, "Leatherworking", "leatherworking", "professions/leatherworking", 1)
    TAILORING = ProfessionData(9, "Tailoring", "tailoring", "professions/tailoring", 1)

    def __init__(self, data: ProfessionData):
        # Setup reverse mapping via ordinal
        _prof_reverse[data.ordinal] = self

    @classmethod
    def _missing_(cls, value: object) -> Optional[Self]:  # reverse lookup by ordinal
        if not isinstance(value, int): return None
        return _prof_reverse.get(value - 1)

    @classmethod
    def available_in(cls, expansion: Expansion) -> Iterator[Profession]:
        """
        :param expansion: Expansion to query
        :return: Professions which existed in the expansion
        """
        return (p for p in cls if expansion.ordinal >= p.expansion)

    # "Shim" methods to avoid needing to call .value
    @property
    def ordinal(self) -> int: return self.value.ordinal
    @property
    def label(self) -> str: return self.value.label
    @property
    def resource(self) -> str: return self.value.resource
    @property
    def portal(self) -> str: return self.value.portal
    @property
    def introduction(self) -> int: return self.value.expansion
