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

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget,
                               QListWidgetItem, QListView, QStyledItemDelegate, QAbstractItemView)
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, Signal
from PySide6.QtGui import QIntValidator

from src.crafting_app import CraftingApp
from src.crafts.item_db import ItemDB
from src.crafts.recipe.recipe_state import RecipeStateCore
from src.crafts.recipe.recipe import Recipe

import src.view.constants as C


class EditTab(QWidget):
    DEFAULT_ITEM_CRAFT_COUNT: int = 1  # starting quantities for selected items

    def __init__(self, craft_app: CraftingApp, state: RecipeStateCore) -> None:
        """
        :param craft_app: Entry-point to crafting, recipe, material, and cost information
        :param state: Observable mapping of selected recipes -> desired number of products
        """
        super().__init__()
        self.setObjectName(C.EditTab.NAME)

        search_box: QLineEdit = QLineEdit()
        search_box.setPlaceholderText(C.EditTab.FILTER_PROMPT)
        search_box.setObjectName(C.EditTab.SEARCH_HANDLE)

        filter_model: FilteredRecipeModel = FilteredRecipeModel(craft_app.item_db, state)
        search_box.textChanged.connect(filter_model.set_search_text)
        def on_recipe_clicked(index: QModelIndex) -> None:
            recipe: Recipe = filter_model.recipe_at(index.row())
            state[recipe] = self.DEFAULT_ITEM_CRAFT_COUNT

        filtered_recipes: QListView = QListView()
        filtered_recipes.clicked.connect(on_recipe_clicked)
        filtered_recipes.setModel(filter_model)
        filtered_recipes.show()

        select_model: SelectedRecipeModel = SelectedRecipeModel(craft_app.item_db, state)
        selected_recipes: QListView = QListView()
        def on_clicked(index: QModelIndex) -> None:
            recipe: Recipe = index.data(Qt.UserRole)
            del state[recipe]
        delegate: QuantityDelegate = QuantityDelegate(selected_recipes)
        selected_recipes.setItemDelegate(delegate)
        selected_recipes.clicked.connect(lambda index: selected_recipes.edit(index))
        select_model.focus_signal.connect(delegate.set_focus_row)
        selected_recipes.clicked.connect(on_clicked)
        selected_recipes.setModel(select_model)
        selected_recipes.show()

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(search_box)
        layout.addWidget(filtered_recipes)
        layout.addWidget(selected_recipes)


class QuantityDelegate(QStyledItemDelegate):
    _INF: int = 10 ** 9

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.__focus_row: Optional[int] = None

    def set_focus_row(self, row: int) -> None:
        self.__focus_row = row

    def createEditor(self, parent, option, index: QModelIndex) -> QLineEdit:
        editor: QLineEdit = QLineEdit(parent)
        editor.setValidator(QIntValidator(1, self._INF, editor))
        return editor

    def setEditorData(self, editor: QLineEdit, index: QModelIndex) -> None:
        value: int = index.model().data(index, Qt.EditRole)
        editor.setText(str(value))
        if self.__focus_row is not None and index.row() == self.__focus_row:
            editor.setFocus()  # seize focus upon a new element being inserted
            editor.selectAll()
            self.__focus_row = None

    def setModelData(self, editor: QLineEdit, model, index: QModelIndex) -> None:
        text: str = editor.text()
        if not text.isdigit(): return  # only allow digit inputs
        value: int = int(text)
        model.setData(index, value, Qt.EditRole)


class SelectedRecipeModel(QAbstractListModel):
    focus_signal = Signal(int)

    def __init__(self, item_db: ItemDB, state: RecipeStateCore) -> None:
        super().__init__()
        self.__item_db: ItemDB = item_db
        self.__state: RecipeStateCore = state
        self.__visible: list[Recipe] = list(state)
        self.__state.listen(self._on_state_change)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.__visible)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[str | int | Recipe]:
        if not index.isValid(): return None
        recipe: Recipe = self.__visible[index.row()]
        if role == Qt.DisplayRole:  # caller wants the recipe name
            name: str = self.__item_db.by_recipe[recipe].item_name
            quantity: int = self.__state[recipe]
            return name
        if role == Qt.EditRole: return self.__state[recipe]  # caller wants the quantity
        if role == Qt.UserRole: return recipe  # caller wants the recipe instance
        return None

    def setData(self, index: QModelIndex, value: int, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid(): return False
        recipe: Recipe = self.__visible[index.row()]
        self.__state[recipe] = int(value)
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def recipe_at(self, row: int) -> Recipe:
        return self.__visible[row]

    def _on_state_change(self, recipe: Recipe, new_quantity: Optional[int]) -> None:
        prev_len: int = len(self.__visible)
        self.beginResetModel()
        self.__visible = list(self.__state)
        self.endResetModel()
        if new_quantity is not None and len(self.__visible) > prev_len:
            self.focus_signal.emit(self.__visible.index(recipe))


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

    def _on_state_change(self, __: Recipe, _: Optional[int]) -> None:
        if len(self.__visible) != len(self.__state):
            self._recompute()  # avoid redraw on value changes
