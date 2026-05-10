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

from typing import Optional
from math import floor

from wow_recipe_calc.crafts.recipe.recipe import Recipe


class CraftSkiller:
    _INF: int = 10 ** 18  # Inf
    _DEFAULT_SKILL_LEVEL: int = 1
    
    def __init__(self, skill_lvl: Optional[int] = None, bound: Optional[int] = None) -> None:
        """
        :param skill_lvl: (Optional) Initial skill level, defaults to 1
        :param bound: (Optional) Level cap for the skill, defaults to INF
        """
        self.__history: list[tuple[int, int, Recipe]] = list()
        if bound is not None:
            if bound < 1: raise ValueError(f"skiller bound must be positive: {bound}")
            self.__bound: int = bound
        else: self.__bound: int = self._INF
        if skill_lvl is not None:
            if skill_lvl < 1:
                raise ValueError(f"skiller starting skill must be positive: {skill_lvl}")
            self.__skill: float = skill_lvl
        else: self.__skill: float = self._DEFAULT_SKILL_LEVEL
        if self.__skill > self.__bound:
            raise ValueError(f"skiller starting skill exceeds bound: {self.__skill} [1, {self.__bound}]")

    def advance(self, skill_lvl: int) -> None:
        """
        :param skill_lvl: Skill level to advance internally to, ignoring skill-ups
        """
        if skill_lvl < floor(self.__skill):
            raise ValueError(f"skill level to advance to is less than current: {skill_lvl} -> {floor(self.__skill)}")
        self.__skill = skill_lvl

    def craft(self, recipe: Recipe) -> None:
        """
        Crafts the item, adding it to the history

        Skill Up Chance Formula:
        chance = (greySkill - yourSkill) / (greySkill - yellowSkill)

        :param recipe: Recipe to be crafted
        """
        if self.__skill < recipe.learned:
            raise ValueError(f"recipe level requirement is not met: "
                             f"{floor(self.__skill)} -> [{recipe.learned}] {recipe.name}")
        skill_before: int = floor(self.__skill)
        if recipe.yellow != recipe.gray:
            chance: float = (recipe.gray - self.__skill) / (recipe.gray - recipe.yellow)
            self.__skill += max(0.0, min(1.0, chance))
        self.__history.append((skill_before, floor(self.__skill), recipe))

    def history(self) -> tuple[tuple[int, int, Recipe, int], ...]:
        """
        Formats the crafting history into the following:
        (A, B, Recipe, Count)
        - Where [A, B] is the level range of the crafts
        - Where Recipe is the Recipe instance of what was crafted
        - Where Count is the amount of crafts of the Recipe in this section

        :return: Tuple of the craft history
        """
        if not self.__history: return tuple()
        runs: list[tuple[int, int, Recipe, int]] = list()

        skill_before, skill_after, current = self.__history[0]
        domain_start: int = skill_before
        domain_end: int = skill_after
        count: int = 1

        for i in range(1, len(self.__history)):
            skill_before, skill_after, recipe = self.__history[i]
            if recipe != current or skill_before > domain_end + 1:
                runs.append((domain_start, domain_end, current, count))
                domain_start, domain_end, current, count = skill_before, skill_after, recipe, 1
            else:
                domain_end = max(domain_end, skill_after)
                count += 1
        runs.append((domain_start, domain_end, current, count))
        return tuple(runs)

    @property
    def skill(self) -> int:
        return floor(self.__skill)
