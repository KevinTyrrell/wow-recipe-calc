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

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                               QListView, QLabel, QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex
from PySide6.QtGui import QIntValidator

from src.crafting_app import CraftingApp
from src.crafts.item_db import ItemDB
from src.crafts.recipe.recipe_state import RecipeStateCore
from src.crafts.recipe.recipe import Recipe

import src.view.constants as C


class EditTab(QWidget):
    DEFAULT_ITEM_CRAFT_COUNT: int = 1

    def __init__(self, craft_app: CraftingApp, state: RecipeStateCore) -> None:
        super().__init__()
        self.__app = craft_app
        self.__state = state
        self.__contents: dict[Recipe, RecipeRow] = dict()
        self._setup_frames()
        self._setup_connections()

    def _setup_frames(self) -> None:
        self.setObjectName(C.EditTab.HANDLE)
        layout: QVBoxLayout = QVBoxLayout(self)

        self.__search_bar: QLineEdit = QLineEdit()
        self.__search_bar.setPlaceholderText(C.EditTab.SearchBar.PROMPT)
        self.__search_bar.setObjectName(C.EditTab.SearchBar.HANDLE)

        # 2. Recipe List (Model/View)
        self.__filter_model = RecipeFilterModel(self.__app.item_db, self.__state)
        self.__filter_view: QListView = QListView()
        self.__filter_view.setModel(self.__filter_model)

        # 3. Selected Items Scroll Area
        self.__scroll_frame: QScrollArea = QScrollArea()
        self.__scroll_frame.setObjectName(C.EditTab.SelectList.HANDLE)
        self.__scroll_frame.setWidgetResizable(True)
        self.__scroll_frame.setFrameShape(QFrame.StyledPanel)

        self.__select_frame: QWidget = QWidget()
        self.__select_frame.setObjectName(C.EditTab.SelectList.BOX_HANDLE)
        self.__select_layout = QVBoxLayout(self.__select_frame)
        self.__select_layout.setAlignment(Qt.AlignTop)
        self.__scroll_frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.__select_layout.setSpacing(0)
        self.__select_layout.setContentsMargins(*C.EditTab.SelectList.MARGINS)

        self.__scroll_frame.setWidget(self.__select_frame)

        layout.addWidget(self.__search_bar)
        layout.addWidget(self.__filter_view)
        layout.addWidget(self.__scroll_frame)

    def _setup_connections(self) -> None:
        self.__search_bar.textChanged.connect(self.__filter_model.filter_text)
        self.__filter_view.clicked.connect(self._on_recipe_selected)
        # Listen for state changes to sync UI rows
        self.__state.listen(self._update_rows)
        for recipe in self.__state: self._add_row(recipe)

    def _on_recipe_selected(self, index: QModelIndex) -> None:
        """Handle adding a recipe from the list to the state"""
        recipe: Recipe = self.__filter_model.recipe_at(index.row())
        self.__state[recipe] = self.DEFAULT_ITEM_CRAFT_COUNT

    def _update_rows(self, recipe: Recipe, _: Optional[int]) -> None:
        len_old, len_new = len(self.__contents), len(self.__state)
        if len_old < len_new: self._add_row(recipe).focus()
        elif len_old > len_new: self._remove_row(recipe)

    def _add_row(self, recipe: Recipe) -> RecipeRow:
        widget: RecipeRow = RecipeRow(recipe, self.__app.item_db, self.__state)
        self.__contents[recipe] = widget
        self.__select_layout.addWidget(widget)
        return widget

    def _remove_row(self, recipe: Recipe) -> None:
        widget: RecipeRow = self.__contents.pop(recipe)
        self.__select_layout.removeWidget(widget)
        widget.deleteLater()


class RecipeRow(QWidget):
    _MAX_QTY: int = 10 ** 9

    def __init__(self, recipe: Recipe, item_db: ItemDB, state: RecipeStateCore) -> None:
        super().__init__()
        self.__recipe: Recipe = recipe
        self.__state: RecipeStateCore = state
        self._setup_frames(item_db)
        self._setup_connections()

    def _setup_frames(self, item_db: ItemDB) -> None:
        self.setObjectName(C.EditTab.SelectList.Row.HANDLE)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(*C.EditTab.SelectList.Row.MARGINS)

        name: str = item_db.by_recipe[self.__recipe].item_name
        self.__label: QLabel = QLabel(name)
        self.__label.setObjectName(C.EditTab.SelectList.Row.NAME_HANDLE)
        self.__label.setCursor(Qt.PointingHandCursor)
        self.__label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.__edit: QLineEdit = QLineEdit(str(self.__state[self.__recipe]))
        self.__edit.setObjectName(C.EditTab.SelectList.Row.QTY_HANDLE)
        self.__edit.setValidator(QIntValidator(1, self._MAX_QTY))
        self.__edit.setAlignment(Qt.AlignCenter)
        self.__edit.setFixedWidth(C.EditTab.SelectList.Row.QTY_WIDTH)

        layout.addWidget(self.__label)
        layout.addWidget(self.__edit)

    def focus(self) -> None:
        self.__edit.setFocus()
        self.__edit.selectAll()

    def _setup_connections(self) -> None:
        self.__edit.textChanged.connect(self._quantity_changed_cb)
        # Enable mouse press to show 'pressed' css styling
        self.__label.mousePressEvent = lambda _: self._mouse_pressed_cb(True)
        # Enable mouse press to eject recipe rows
        self.__label.mouseReleaseEvent = lambda _: self.__state.pop(self.__recipe, None)

    def _quantity_changed_cb(self, text: str) -> None:
        if text.isdigit(): self.__state[self.__recipe] = int(text)

    def _mouse_pressed_cb(self, is_pressed: bool) -> None:
        """Updates the CSS 'pressed' property and refreshes styling"""
        self.setProperty(C.EditTab.SelectList.Row.PRESS_PROPERTY, is_pressed)
        for obj in (self, self.__label):
            obj.style().unpolish(obj)
            obj.style().polish(obj)

    def _remove(self) -> None:
        if self.__recipe in self.__state:  # removing from state will eject this row
            del self.__state[self.__recipe]


class RecipeFilterModel(QAbstractListModel):
    def __init__(self, item_db: ItemDB, state: RecipeStateCore) -> None:
        super().__init__()
        self.__item_db: ItemDB = item_db
        self.__state: RecipeStateCore = state
        self.__filter_text: str = str()
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

    def filter_text(self, text: str) -> None:
        self.__filter_text = text.lower()
        self._recompute()

    def recipe_at(self, row: int) -> Recipe:
        return self.__visible[row]

    def _recompute(self) -> None:
        self.beginResetModel()
        self.__visible = [recipe for recipe in self.__item_db.by_recipe.keys()
                          if recipe not in self.__state and self._search_match(recipe)]
        self.endResetModel()

    def _search_match(self, recipe: Recipe) -> bool:
        name: str = self.__item_db.by_recipe[recipe].item_name
        return self.__filter_text in name.lower()

    def _on_state_change(self, __: Recipe, _: Optional[int]) -> None:
        if len(self.__visible) != len(self.__state):
            self._recompute()
