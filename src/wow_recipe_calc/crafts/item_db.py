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

from typing import Optional
from types import MappingProxyType as ReadOnlyMap
from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path
from logging import getLogger, Logger

from wow_recipe_calc.io.resources.json_store import JsonStore
from wow_recipe_calc.io.resources.project import Saveable
from wow_recipe_calc.client.item_client import ItemClient
from wow_recipe_calc.crafts.recipe.recipe import Recipe

logger: Logger = getLogger(__name__)


@dataclass(frozen=True)
class ItemEntry:
    item_id: int
    item_name: str


@dataclass(frozen=True)
class RecipeEntry(ItemEntry):
    recipe: Recipe


class ItemDB(Saveable):
    _RESOURCE: Path = Path("data/items/item_db")

    def __init__(self, client: ItemClient) -> None:
        """
        :param client: Web requester used for requesting missing item names
        """
        self.__client: ItemClient = client
        self.__database: JsonStore = JsonStore(self._RESOURCE.stem, self._RESOURCE.parent)
        self.__transpose: dict[int, str] = dict()  # reverse pairing view of JsonStore
        self.__by_name: dict[str, ItemEntry] = dict()
        self.__by_id: dict[int, ItemEntry] = dict()
        self.__by_recipe: dict[Recipe, RecipeEntry] = dict()
        self.__by_name_ro: Mapping[str, ItemEntry] = ReadOnlyMap(self.__by_name)
        self.__by_id_ro: Mapping[int, ItemEntry] = ReadOnlyMap(self.__by_id)
        self.__by_recipe_ro: Mapping[Recipe, RecipeEntry] = ReadOnlyMap(self.__by_recipe)
        self._initialize_db()
        
    def register(self, recipe: Recipe) -> None:
        """
        :param recipe: Recipe to register along with its material
        """
        if recipe in self.__by_recipe: return  # no duplicates'
        for mat_id in recipe.reagents:
            if mat_id not in self.__by_id:  # Don't overwrite recipes with items
                self._add_item_entry(mat_id)
        self._add_recipe_entry(recipe)

    @property
    def by_name(self) -> Mapping[str, ItemEntry]: return self.__by_name_ro
    @property
    def by_id(self) -> Mapping[int, ItemEntry]: return self.__by_id_ro
    @property
    def by_recipe(self) -> Mapping[Recipe, RecipeEntry]: return self.__by_recipe_ro

    def save(self) -> None:
        """
        Save the database to the storage medium
        """
        self.__database.save()

    def _initialize_db(self) -> None:
        try:  # attempts to load the database
            self.__database.load()
            self.__transpose.update({v: k for k, v in self.__database.items()})
        except FileNotFoundError:
            logger.info(f"no existing cache file found at: {self.__database.file_path}")
        except Exception as e:
            logger.critical(str(e))
            raise  # raise the original exception
        
    def _add_item_entry(self, item_id: int) -> None:
        e: ItemEntry = ItemEntry(item_id, self._item_name(item_id))
        self.__by_name[e.item_name], self.__by_id[item_id] = e, e
    
    def _add_recipe_entry(self, r: Recipe) -> None:
        e: RecipeEntry = RecipeEntry(r.product, self._item_name(r.product), r)
        self.__by_name[e.item_name], self.__by_id[e.item_id], self.__by_recipe[r] = e, e, e
    
    def _item_name(self, item_id: int) -> str:
        """Retrieve or request the name of an item by ID"""
        name: Optional[str] = self.__transpose.get(item_id)
        if name is None:
            name = self.__client.get_item_name(item_id)
            if name is None:
                raise KeyError(f"item name could not be resolved: {item_id}")
            self.__database[name] = item_id  # new element to be saved to storage medium
            self.__transpose[item_id] = name  # cache the transposition
        return name
