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
from logging import Logger, getLogger

from PySide6.QtWidgets import QApplication
from sys import exit

from src.crafting_app import CraftingApp
from src.crafts.item_db import ItemEntry, RecipeEntry
from src.view.styles.style_loader import StyleLoader
from src.view.frame.main_window import MainWindow
from src.crafts.recipe.recipe_state import RecipeStateCore
from src.crafts.recipe.recipe import Recipe

logger: Logger = getLogger(__name__)


class UIManager:
    _RECIPE_SELECTION_KEY: str = "RECIPE_SELECTION"
    _RECIPE_SELECTION_SEP: str = ";"

    def __init__(self, app: CraftingApp) -> None:
        self.__craft_app: CraftingApp = app
        self.__view_app: QApplication = QApplication()
        style_loader: StyleLoader = StyleLoader()
        #self.__view_app.setStyleSheet("QWidget { border: 1px solid red; }")
        self.__view_app.setStyleSheet(style_loader.load())
        self.__window: MainWindow = MainWindow(app, self._make_recipe_state())

    def show(self) -> None:
        self.__window.show()
        exit(self.__view_app.exec())

    def _make_recipe_state(self) -> RecipeStateCore:
        state: RecipeStateCore = RecipeStateCore()
        selections: Optional[str] = self.__craft_app.environment.get(self._RECIPE_SELECTION_KEY)
        if selections is not None:
            state.update(self._parse_selected_recipes(selections))
        state.listen(self._on_recipe_select_change)
        return state

    # Parses saved recipe selection ids;quantity into formal Recipe->quantity pairings
    def _parse_selected_recipes(self, raw_selection: str) -> Mapping[Recipe, int]:
        def parse_failure(msg) -> Mapping[Recipe, int]:
            logger.warning(msg); return dict()
        parts: list[str] = raw_selection.split(";") if raw_selection else []
        if not parts or len(parts) % 2:
            return parse_failure("environment's saved recipe selection is malformed")
        try: nums: list[int] = list(map(int, parts))
        except ValueError:
            return parse_failure("environment's saved recipes must contain only integers")
        recipes: dict[Recipe, int] = dict()
        for item_id, quantity in zip(nums[::2], nums[1::2]):  # build tuples for neighboring pairs
            if quantity <= 0:
                return parse_failure("environment's saved recipe quantities must be positive")
            entry: Optional[ItemEntry] = self.__craft_app.item_db.by_id.get(item_id)
            if entry is not None or not isinstance(entry, RecipeEntry):
                return parse_failure(f"environment's saved recipe id is unrecognized: {item_id}")
            recipes[entry.recipe] = quantity
        return recipes

    @staticmethod
    def _on_recipe_select_change(_: object = None, __: object = None) -> None:
        data: Mapping[Recipe, int] = state.state
        self.__craft_app.environment[self._RECIPE_SELECTION_KEY] = (
            self._RECIPE_SELECTION_SEP.join(f"{r.product};{q}" for r, q in data.items()))
