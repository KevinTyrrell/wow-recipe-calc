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
        self.app = craft_app
        self.state = state
        self.row_widgets: dict[Recipe, RecipeRow] = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Initialize UI components and layout."""
        self.setObjectName(C.EditTab.NAME)
        layout = QVBoxLayout(self)

        # 1. Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(C.EditTab.FILTER_PROMPT)
        self.search_box.setObjectName(C.EditTab.SEARCH_HANDLE)

        # 2. Recipe List (Model/View)
        self.filter_model = FilteredRecipeModel(self.app.item_db, self.state)
        self.recipe_view = QListView()
        self.recipe_view.setModel(self.filter_model)

        # 3. Selected Items Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName(C.EditTab.SELECT_LIST_HANDLE)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.StyledPanel)

        self.selected_container = QWidget()
        self.selected_container.setObjectName(C.EditTab.SELECT_BOX_HANDLE)
        self.selected_layout = QVBoxLayout(self.selected_container)
        self.selected_layout.setAlignment(Qt.AlignTop)
        self.selected_layout.setSpacing(0)
        self.selected_layout.setContentsMargins(5, 5, 5, 5)

        self.scroll_area.setWidget(self.selected_container)

        # Assemble main layout
        layout.addWidget(self.search_box)
        layout.addWidget(self.recipe_view)
        layout.addWidget(self.scroll_area)

    def _connect_signals(self) -> None:
        """Wire up reactivity."""
        self.search_box.textChanged.connect(self.filter_model.set_search_text)
        self.recipe_view.clicked.connect(self._on_recipe_selected)

        # Listen for state changes to sync UI rows
        self.state.listen(lambda *_: self.sync_selected_rows())
        self.sync_selected_rows()

    def _on_recipe_selected(self, index: QModelIndex) -> None:
        """Handle adding a recipe from the list to the state."""
        recipe = self.filter_model.recipe_at(index.row())
        self.state[recipe] = self.DEFAULT_ITEM_CRAFT_COUNT

    def sync_selected_rows(self) -> None:
        """Synchronizes the RecipeRow widgets with the current state."""
        # Remove stale widgets (recipes no longer in state)
        for recipe in list(self.row_widgets.keys()):
            if recipe not in self.state:
                widget = self.row_widgets.pop(recipe)
                self.selected_layout.removeWidget(widget)
                widget.deleteLater()

        # Add new widgets (recipes added to state)
        last_added = None
        for recipe in self.state:
            if recipe not in self.row_widgets:
                widget = RecipeRow(recipe, self.app.item_db, self.state)
                self.row_widgets[recipe] = widget
                self.selected_layout.addWidget(widget)
                last_added = widget

        if last_added:
            last_added.focus_edit()


class RecipeRow(QWidget):
    _INF: int = 10 ** 9

    def __init__(self, recipe: Recipe, item_db: ItemDB, state: RecipeStateCore) -> None:
        super().__init__()
        self.setObjectName(C.EditTab.ROW_HANDLE)
        self.setAttribute(Qt.WA_StyledBackground, True)  # enables css bg/hover

        self.__recipe: Recipe = recipe
        self.__state: RecipeStateCore = state

        name: str = item_db.by_recipe[recipe].item_name

        self.__label: QLabel = QLabel(name)
        self.__label.setObjectName(C.EditTab.ROW_NAME_HANDLE)
        self.__label.setCursor(Qt.PointingHandCursor)
        self.__label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


        self.__edit: QLineEdit = QLineEdit(str(state[recipe]))
        self.__edit.setObjectName(C.EditTab.ROW_QTY_HANDLE)
        self.__edit.setValidator(QIntValidator(1, self._INF))
        self.__edit.setAlignment(Qt.AlignCenter)
        self.__edit.setFixedWidth(C.EditTab.ROW_QTY_WIDTH)

        def on_text_changed(text: str) -> None:
            if text.isdigit():
                state[recipe] = int(text)

        self.__edit.textChanged.connect(on_text_changed)
        self.__label.mousePressEvent = lambda e: self._set_pressed(True)
        self.__label.mouseReleaseEvent = lambda e: self._remove()
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(self.__label)
        layout.addWidget(self.__edit)

    def focus_edit(self) -> None:
        self.__edit.setFocus()
        self.__edit.selectAll()

    def _set_pressed(self, pressed: bool) -> None:
        self.setProperty("pressed", pressed)
        self.style().unpolish(self)
        self.style().polish(self)
        self.__label.style().unpolish(self.__label)
        self.__label.style().polish(self.__label)

    def _remove(self) -> None:
        self._set_pressed(False)
        del self.__state[self.__recipe]


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