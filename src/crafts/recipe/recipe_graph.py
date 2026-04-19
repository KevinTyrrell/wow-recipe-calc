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

from typing import Optional, Iterable, Callable, TypeVar

from src.util.graph import Graph, Frontier
from src.util.heap import Heap
from src.crafts.recipe.recipe import Recipe
from src.crafts.item_db import ItemDB, RecipeEntry

_T = TypeVar("_T")

def _cmp_recipe(a: Recipe, b: Recipe) -> int:
    a_grey: int = a.levels[-1]
    b_grey: int = b.levels[-1]
    if a_grey < b_grey: return -1
    if a_grey > b_grey: return 1
    return 0


class _GrayRecipeQueue(Frontier[Recipe]):
    def __init__(self, recipes: Iterable[Recipe]) -> None:
        # shouldn't this be a max heap? since we're outputting in reverse order
        self.__heap: Heap[Recipe] = Heap(True, recipes, _cmp_recipe) 
    def push(self, element: Recipe) -> None:
        self.__heap.push(element)
    def pop(self) -> Recipe:
        return self.__heap.pop()
    def __bool__(self) -> bool:
        return bool(self.__heap)


class RecipeGraph(Graph[Recipe]):
    def __init__(self, item_db: ItemDB, recipes: Optional[Iterable[Recipe]]=None,
                frontier_factory: Optional[Callable[[Iterable[_T]], Frontier[_T]]] = None) -> None:
        """
        :param item_db: Item database used for recipe lookups
        :param recipes: (Optional) Initial set of recipes
        :param frontier_factory: (Optional) Frontier factory for topological sort
        """
        super().__init__(frontier_factory = frontier_factory)
        self.__db: ItemDB = item_db
        if recipes is not None:
            self.integrate(recipes)
                
    def integrate(self, recipes: Iterable[Recipe]) -> None:
        """
        :param recipes: Recipe to be added, along with nested recipes
        """
        evaluated: set[Recipe] = set()  # Trim explored paths
        for recipe in recipes: self._integrate(recipe, evaluated)
                
    def _integrate(self, recipe: Recipe, evaluated: set[Recipe]) -> None:
        self.add(recipe)
        evaluated.add(recipe)
        for requirement in (entry.recipe for req_id in recipe.reagents
                            if isinstance(entry := self.__db.by_id[req_id], RecipeEntry)):
            self.requires(recipe, requirement)
            if requirement not in evaluated:
                self._integrate(requirement, evaluated)   


class GrayPriortyRecipeGraph(RecipeGraph):
    def __init__(self, item_db: ItemDB, recipes: Optional[Iterable[Recipe]]=None):
        super().__init__(item_db, recipes, lambda elements: _GrayRecipeQueue(elements))
