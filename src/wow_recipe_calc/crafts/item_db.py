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
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Callable
from types import MappingProxyType as ReadOnlyMap
from dataclasses import dataclass
from collections.abc import Mapping

from wow_recipe_calc.crafts.recipe.recipe import Recipe


@dataclass(frozen=True)
class ItemEntry:
    item_id: int
    item_name: str


@dataclass(frozen=True)
class RecipeEntry(ItemEntry):
    recipe: Recipe


class ItemDB:
    _DEFAULT_ITEM_DB_NAME: str = "item_db"

    def __init__(self, item_requester: Callable[[int], Optional[str]], db_name: Optional[str] = None,
                 dir_path: Optional[str] = None, file_ext: Optional[str] = None) -> None:
        """
        :param item_requester: Callback to translate item_id -> item_name
        :param file_basename: Filename of the database to cache response data
        :param dir_path: Directory path to save the database in, default: CWD
        :param file_ext: Extension for the database, default: json
        """
        self.__by_name: dict[str, ItemEntry] = dict()
        self.__by_id: dict[int, ItemEntry] = dict()
        self.__by_recipe: dict[Recipe, RecipeEntry] = dict()
        self.__by_name_ro: Mapping[str, ItemEntry] = ReadOnlyMap(self.__by_name)
        self.__by_id_ro: Mapping[int, ItemEntry] = ReadOnlyMap(self.__by_id)
        self.__by_recipe_ro: Mapping[Recipe, RecipeEntry] = ReadOnlyMap(self.__by_recipe)
        
    def register(self, recipe: Recipe) -> None:
        if recipe in self.__by_recipe: return  # no duplicates'
        for mat_id in recipe.reagents:
            if mat_id not in self.__by_id:  # Don't overwrite recipes with items
                self._add_item_entry(mat_id)
        self._add_recipe_entry(recipe)
        
    def save(self) -> None:
        pass
        
    def _add_item_entry(self, item_id: int) -> None:
        e: ItemEntry = ItemEntry(item_id, self._item_name(item_id))
        self.__by_name[e.item_name], self.__by_id[item_id] = e, e
    
    def _add_recipe_entry(self, r: Recipe) -> None:
        e: RecipeEntry = RecipeEntry(r.product, self._item_name(r.product), r)
        self.__by_name[e.item_name], self.__by_id[e.item_id], self.__by_recipe[r] = e, e, e
    
    def _item_name(self, item_id: int) -> str:
        item_name: Optional[str] = self.__db.fetch(item_id, self.__policy)
        if item_name is None: 
            raise KeyError(f"item name could not be resolved: {item_id}")
        return item_name
    
    @property
    def by_name(self) -> Mapping[str, ItemEntry]: return self.__by_name_ro
    @property
    def by_id(self) -> Mapping[int, ItemEntry]: return self.__by_id_ro
    @property
    def by_recipe(self) -> Mapping[Recipe, RecipeEntry]: return self.__by_recipe_ro
