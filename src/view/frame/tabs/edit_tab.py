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

from typing import Dict, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QListView
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex

from src.crafting_app import CraftingApp
from src.crafts.item_db import ItemDB
from src.crafts.recipe.recipe_state import RecipeStateCore, RecipeStateViewer
from src.crafts.recipe.recipe import Recipe
from src.crafts.item_db import RecipeEntry


class EditTab(QWidget):
    DEFAULT_ITEM_CRAFT_COUNT: int = 1  # starting quantities for selected items

    def __init__(self, craft_app: CraftingApp, state: RecipeStateCore) -> None:
        """
        :param craft_app: Entry-point to crafting, recipe, material, and cost information
        :param state: Observable mapping of selected recipes -> desired number of products
        """
        super().__init__()
        self.__craft_app: CraftingApp = craft_app
        self.__state: RecipeStateCore = state

        search_box: QLineEdit = QLineEdit()
        search_box.setPlaceholderText("Search recipes...")
        filtered_recipes: QListView = QListView()

        # -------------------
        # Wiring
        # -------------------

        model: FilteredRecipeModel = FilteredRecipeModel(self.__craft_app.item_db, state)
        def _on_recipe_clicked(index: QModelIndex) -> None:
            recipe: Recipe = model.recipe_at(index.row())
            state[recipe] = self.DEFAULT_ITEM_CRAFT_COUNT
        filtered_recipes.clicked.connect(_on_recipe_clicked)
        filtered_recipes.setModel(model)
        filtered_recipes.show()

        search_box.textChanged.connect(model.set_search_text)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(search_box)
        layout.addWidget(filtered_recipes)


class FilteredRecipeModel(QAbstractListModel):
    def __init__(self, item_db: ItemDB, state: RecipeStateCore) -> None:
        super().__init__()
        self.__item_db: ItemDB = item_db
        self.__state: RecipeStateCore = state
        self.__filter_text: str = ""
        self.__visible: list[Recipe] = list()
        self.__state.listen(self._on_state_change)
        self._recompute()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.__visible)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str]:
        if not index.isValid(): return None
        if role != Qt.DisplayRole: return None
        recipe: Recipe = self.__visible[index.row()]
        name: str = self.__item_db.by_recipe[recipe].item_name
        return name

    def set_search_text(self, text: str) -> None:
        self.__filter_text = text.lower()
        self._recompute()

    def recipe_at(self, row: int) -> Recipe:
        return self.__visible[row]

    def _recompute(self) -> None:
        self.beginResetModel() #  prepare next frame of the UI
        self.__visible = [ recipe for recipe in self.__item_db.by_recipe.keys()
                           if recipe not in self.__state and self._search_match(recipe) ]
        self.endResetModel()  # allow next frame to process

    def _search_match(self, recipe: Recipe) -> bool:
        name: str = self.__item_db.by_recipe[recipe].item_name
        return self.__filter_text in name.lower()

    def _on_state_change(self, __: Recipe, _: int | None) -> None:
        self._recompute()
