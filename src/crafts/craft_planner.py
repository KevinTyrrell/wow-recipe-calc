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
from types import MappingProxyType as RO
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import ceil

from src.crafts.recipe import Recipe
from src.crafts.item_db import *
from src.crafts.price_manager import PriceManager
from src.util.graph import Node, Graph
from src.util.heap import Heap


@dataclass(frozen=True)
class CraftPlan:
    craft_counts: Mapping[Recipe, int]
    craft_order: tuple[tuple[Recipe, int], ...]
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
        graph: _RecipeGraph = _RecipeGraph(item_db.by_recipe.keys())
        self.__order = [
            entry.recipe for node in reversed(graph.topological_sort())
            if isinstance(entry := item_db.by_id[node.payload], RecipeEntry) ]
        self.__demand: defaultdict[Recipe, int] = defaultdict(lambda: 0)
        
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
            recipe = entry.recipe
        else: recipe = item
        self.__demand[recipe] += quantity
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
        order: tuple[Recipe, ...] = self._plan_order(crafts.keys())
        return CraftPlan(crafts, order, None, None)
        
    def _plan_order(self, recipes: Iterable[Recipe]) -> tuple[Recipe, ...]:
        if len(recipes) <= 0: return tuple()
        events = sorted({e.learned for e in recipes} | {e.levels[-1] for e in recipes})
        actives: tuple[int, int, list[Recipe]] = list()
        for i in range(len(events) - 1):
            L, R = events[i], events[i + 1]
            actives.append((L, R, [e for e in recipes if e.learned <= L < e.levels[-1]]))
        
        for t in actives:
            print(f"({t[0]}, {t[1]},): {[e.name for e in t[2]]}")
        # MAKE GRAPH OF RECIPES
        # MAKE RECIPE GRAPH CLASS EXTEND GRAPH
        
        
        
        
        
        
        
        def cmp(a, b) -> int: # Comparator [-1, 0, 1]
            return (a > b) - (a < b)
        min_learned: Heap = Heap(True, recipes, lambda a, b: cmp(a.learned, b.learned))
        min_gray: Heap = Heap(True, recipes, lambda a, b: cmp(a.levels[-1], b.levels[-1]))
        skill: int = min_learned.peek().learned  # Start of skill domain
        
        
        
        while min_learned.peek() is not None:
            e: Recipe = min_learned.pop()
            print(f"recipe={e.name}, learned={e.learned}")
        
        
        #print(f"recipe={min_gray.peek().name}, grey={min_gray.peek.levels[-1]}")
        
        
        
        
        return tuple() # pass
        
    def _plan_crafts(self, materials: defaultdict[int, int]) -> Mapping[Recipe, int]:
        demand: defaultdict[Recipe, int] = self.__demand.copy()
        crafts: dict[Recipe, int] = dict()
        for recipe in self.__order:
            # Max heap can be used here for O(k log k) iteration instead of O(n),
            # where k is the demanded recipes & n is every-defined recipe.
            # However, this can backfire in heavy crafts such that O(k log k) > O(n)
            item_demand: int = demand[recipe]
            if item_demand <= 0: continue # ignore undesired recipes
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
        return RO(crafts) 
