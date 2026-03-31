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

from types import MappingProxyType as ReadOnly
from typing import Optional, Mapping, Generator
from dataclasses import dataclass
from collections import defaultdict
from collections.abc import Iterable
from math import ceil

from src.crafts.recipe import Recipe
from src.crafts.craft_skill import CraftSkiller
from src.crafts.item_db import ItemDB, RecipeEntry, ItemEntry
from src.crafts.price_manager import PriceManager
from src.crafts.recipe_graph import RecipeGraph, GrayPriortyRecipeGraph
from src.util.heap import Heap


@dataclass(frozen=True)
class CraftPlan:
    craft_counts: Mapping[Recipe, int]
    craft_order: tuple[tuple[int, int, Recipe, int], ...]
    craft_costs: Mapping[Recipe, int]
    craft_mats: tuple[int, int]


class CraftPlanner:
    def __init__(self, item_db: ItemDB, prices: PriceManager) -> None:
        """
        :param item_db: Item DB to request recipe information
        :param prices: Price manager to request prices of items
        """
        self.__item_db: ItemDB = item_db
        self.__prices: PriceManager = prices
        self.__demands: defaultdict[Recipe, int] = defaultdict(lambda: 0)
        
    def craft(self, item: int | str | Recipe, quantity: Optional[int]=1) -> bool:
        """
        Constructs a specified number of items from a recipe
        
        Note: This does not craft the recipe X number of times.
        For example, if a recipe crafts two items per cast and
        a quantity=2 is provided, only one craft is required.
        
        :param item: Item to be crafted (either by name, id, or Recipe instance)
        :param quantity: (Optional) Quantity to craft, default: 1
        """
        if quantity < 1: 
            raise ValueError(f"recipe craft quantity must be positive: {quantity}")
        if not isinstance(item, Recipe):
            if isinstance(item, int):
                entry = self.__item_db.by_id.get(item)
            else: entry = self.__item_db.by_name.get(item)
            if not isinstance(entry, RecipeEntry):
                return False
            self.__demands[entry.recipe] += quantity
        else: self.__demands[item] += quantity
        return True
        
    def plan(self) -> CraftPlan:
        """
        Constructs a crafting plan from currently-added crafts
        
        craft_counts: Number of crafts required for each resulting recipe
        craft_order: Order in which the aforementioned recipies should be crafted
            craft_costs: Total cost to craft each recipe
            craft_costs: Mapping[Recipe, int]
            craft_mats: tuple[int, int]
        """
        materials: defaultdict[int, int] = defaultdict(lambda: 0)
        crafts: Mapping[Recipe, int] = self._plan_crafts(materials)
        order: tuple[tuple[int, int, Recipe, int], ...] = self._plan_order(crafts.keys())
        return CraftPlan(crafts, order, None, None)
        
    def _plan_order(self, recipes: Iterable[Recipe]) -> tuple[tuple[int, int, Recipe, int], ...]:
        graph: GrayPriortyRecipeGraph = GrayPriortyRecipeGraph(self.__item_db, recipes)
        demands: dict[Recipe, int] = { k: v for k, v in self.__demands.items() if v > 0 }
        skiller: CraftSkiller = CraftSkiller()
        cleaner: _GrayRecipeCleaner = _GrayRecipeCleaner(graph, skiller, demands)
        for section in self._calc_skill_sections(graph):
            L, R, active = section
            if skiller.skill < L: skiller.advance(L)  # jump over impassible sections
            while active:  # as long as craftable recipes exist
                while True:  # craft a single item, repeat until one is crafted
                    recipe: Recipe = active.pop()
                    # Only craft if we have yet to meet demand
                    demand: int = demands[recipe]
                    if demand > 0:
                        skiller.craft(recipe)
                        demands[recipe] = demand - 1
                        if demand <= 1:  # We just finished crafting last of this item
                            cleaner.clean(recipe)
                    elif not active: break
                if skiller.skill >= R:  # entered a new crafting skill section
                    cleaner.schedule(active)  # schedule gray recipes we've yet to craft
                    break  # current section is now inefficient, exit
        return skiller.history()

    # Determines the total number of crafts required per recipe, including nested recipes
    def _plan_crafts(self, materials: defaultdict[int, int]) -> Mapping[Recipe, int]:
        demand: defaultdict[Recipe, int] = self.__demands.copy()
        graph: RecipeGraph = RecipeGraph(self.__item_db, (k for k, v in demand.items() if v > 0))
        crafts: dict[Recipe, int] = dict()
        for recipe in reversed(list(graph.topo)):
            item_demand: int = demand[recipe]
            # Determine how many times we have to craft to meet total demand
            count: int = ceil(item_demand / recipe.produces)
            crafts[recipe] = count
            for reagent, quantity in recipe.reagents.items():
                entry: ItemEntry = self.__item_db.by_id[reagent]
                if isinstance(entry, RecipeEntry):
                    if entry.recipe in crafts:
                        child: RecipeEntry = self.__item_db.by_recipe[recipe]
                        raise RuntimeError(
                            f"invariant violation: '{entry.item_name}' depends on "
                            f"'{child.item_name}', which has already been processed")
                    demand[entry.recipe] += count * quantity
                else: materials[reagent] += count * quantity
        return ReadOnly(crafts)

    @staticmethod
    def _calc_skill_sections(graph: RecipeGraph) -> Generator[tuple[int, int, list[Recipe]]]:
        # List of unique levels in which a recipe either becomes learnable or no longer grants skill-ups
        events: list[int] = sorted({e.learned for e in graph} | {e.levels[-1] for e in graph})
        for i in range(len(events) - 1):
            L, R = events[i], events[i + 1]
            active: list[Recipe] = [e for e in graph.topo if e.learned <= L < e.levels[-1]]  # slow, can be optimized
            yield L, R, active


class _GrayRecipeCleaner:
    def __init__(self, graph: RecipeGraph, skiller: CraftSkiller, demands: dict[Recipe, int]) -> None:
        self.__graph: RecipeGraph = graph
        self.__skiller: CraftSkiller = skiller
        self.__order: Heap[Recipe] = Heap(True, cmp = graph.topo.cmp)
        self.__container: set[Recipe] = set()
        self.__demands: dict[Recipe, int] = demands

    # Checks recipes for any gray recipes yet to be crafted, then sets to craft them later on
    def schedule(self, recipes: Iterable[Recipe]) -> None:
        for recipe in recipes:
            if self.__skiller.skill >= recipe.levels[-1] and recipe not in self.__container:
                self.__order.push(recipe)
                self.__container.add(recipe)

    # Attempts to clean any gray recipes, reference: most recent skill-gaining recipe
    def clean(self, reference: Recipe) -> None:
        while self.__order:
            ref_h: int = self.__graph.topo.index(self.__order.peek())
            ref_i: int = self.__graph.topo.index(reference)
            if ref_h <= ref_i + 1:  # If gray recipe is topologically craftable
                recipe: Recipe = self.__order.pop()
                for i in range(self.__demands[recipe]):
                    self.__skiller.craft(recipe)  # Craft all of this gray recipe
                self.__container.remove(recipe)  # Mark as removed
            else: return  # Most craftable gray recipe is still waiting for a requirement to be met
