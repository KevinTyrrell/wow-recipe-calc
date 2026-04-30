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
#  along with this program.  If not, see <https://www.gnu.org/licenses/>

from typing import Optional
from logging import Logger, getLogger

from PySide6.QtWidgets import QApplication
from sys import exit

import wow_recipe_calc.view.constants as C

from wow_recipe_calc.util.log_manager import LogManager
from wow_recipe_calc.crafting_app import CraftingApp
from wow_recipe_calc.crafts.item_db import ItemEntry, RecipeEntry
from wow_recipe_calc.view.styles.style_loader import StyleLoader
from wow_recipe_calc.view.frame.main_window import MainWindow
from wow_recipe_calc.crafts.recipe.recipe_state import RecipeStateCore
from wow_recipe_calc.crafts.recipe.recipe import Recipe

logger: Logger = getLogger(__name__)


class UIManager:
    _RECIPE_SELECTION_KEY: str = "recipe_selection"
    _RECIPE_SELECTION_SEP: str = ";"

    def __init__(self, app: CraftingApp, logs: LogManager) -> None:
        """
        :param app: Entry-point to crafting, recipe, material, and cost information
        :param logs: Log history buffer, for retrieving logging prior to GUI being displayed
        """
        self.__craft_app: CraftingApp = app
        self.__view_app: QApplication = QApplication()
        self.__window: MainWindow = MainWindow(app, self._make_recipe_state(), logs)
        stylesheet: StyleLoader = StyleLoader(C.STYLE_RESOURCE_PATH)
        self.__view_app.setStyleSheet(stylesheet.load())

    def show(self) -> None:
        self.__window.show()
        exit(self.__view_app.exec())

    def _make_recipe_state(self) -> RecipeStateCore:
        """Creates mapping of currently-selected recipes & their quantities"""
        state: RecipeStateCore = RecipeStateCore()
        selections: Optional[str] = self.__craft_app.environment.get(self._RECIPE_SELECTION_KEY)
        if selections is not None:  # attempt to load last selection(s) from saved environment
            state.update(self._parse_selected_recipes(selections))
        def on_recipe_select_changed(_: Recipe, __: Optional[int]) -> None:
            self.__craft_app.environment[self._RECIPE_SELECTION_KEY] = (
                self._RECIPE_SELECTION_SEP.join(f"{r.product};{q}" for r, q in state.items()))
        state.listen(on_recipe_select_changed)
        return state

    def _parse_selected_recipes(self, raw_selection: str) -> Mapping[Recipe, int]:
        """Parses saved recipe selection ids;quantity into formal Recipe->quantity pairings"""
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
            if entry is None or not isinstance(entry, RecipeEntry):
                return parse_failure(f"environment's saved recipe id is unrecognized: {item_id}")
            recipes[entry.recipe] = quantity
        return recipes
