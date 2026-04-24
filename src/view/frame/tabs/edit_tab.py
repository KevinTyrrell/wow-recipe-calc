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

        scroll_area: QScrollArea = QScrollArea()
        scroll_area.setObjectName("selected-list")          # <-- targeted in QSS
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.StyledPanel)

        selected_container: QWidget = QWidget()
        selected_container.setObjectName("selected-list-container")  # <-- targeted in QSS
        selected_layout: QVBoxLayout = QVBoxLayout(selected_container)
        selected_layout.setAlignment(Qt.AlignTop)
        selected_layout.setSpacing(0)   # 0 so border-bottom acts as the only divider, like QListView
        selected_layout.setContentsMargins(5, 5, 5, 5)
        scroll_area.setWidget(selected_container)

        row_widgets: dict[Recipe, RecipeRow] = {}

        def rebuild_selected() -> None:
            for recipe in list(row_widgets):
                if recipe not in state:
                    widget: RecipeRow = row_widgets.pop(recipe)
                    selected_layout.removeWidget(widget)
                    widget.deleteLater()

            last_added: Optional[RecipeRow] = None
            for recipe in state:
                if recipe not in row_widgets:
                    widget = RecipeRow(recipe, craft_app.item_db, state)
                    row_widgets[recipe] = widget
                    selected_layout.addWidget(widget)
                    last_added = widget

            if last_added is not None:
                last_added.focus_edit()

        state.listen(lambda recipe, qty: rebuild_selected())
        rebuild_selected()

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.addWidget(search_box)
        layout.addWidget(filtered_recipes)
        layout.addWidget(scroll_area)


class RecipeRow(QWidget):
    def __init__(self, recipe: Recipe, item_db: ItemDB, state: RecipeStateCore) -> None:
        super().__init__()
        self.setObjectName("recipe-row")                    # <-- targeted in QSS
        self.setAttribute(Qt.WA_StyledBackground, True)    # required for QWidget bg/hover rules to apply

        self.__recipe: Recipe = recipe
        self.__state: RecipeStateCore = state

        name: str = item_db.by_recipe[recipe].item_name

        label: QLabel = QLabel(name)
        label.setObjectName("recipe-row-label")
        label.setCursor(Qt.PointingHandCursor)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.__edit: QLineEdit = QLineEdit(str(state[recipe]))
        self.__edit.setObjectName("recipe-row-qty")
        self.__edit.setValidator(QIntValidator(1, 10 ** 9))
        self.__edit.setFixedWidth(80)

        def on_text_changed(text: str) -> None:
            if text.isdigit():
                state[recipe] = int(text)

        self.__edit.textChanged.connect(on_text_changed)
        label.mousePressEvent = lambda _: self._remove()

        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(label)
        #layout.addStretch()
        layout.addWidget(self.__edit)

    def focus_edit(self) -> None:
        self.__edit.setFocus()
        self.__edit.selectAll()

    def _remove(self) -> None:
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