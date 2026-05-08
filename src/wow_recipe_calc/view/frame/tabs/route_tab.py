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

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt

from wow_recipe_calc.crafts.craft_planner import CraftPlan
from wow_recipe_calc.crafts.recipe.recipe import Recipe
from wow_recipe_calc.view.frame.tabs.plan_tab import PlanTab
from wow_recipe_calc.crafts.item_db import ItemDB

import wow_recipe_calc.view.constants as C


class RouteTab(PlanTab):
    def __init__(self, item_db: ItemDB) -> None:
        """
        :param item_db: Item DB used for item/recipe name requests
        """
        super().__init__()
        self.__item_db: ItemDB = item_db
        self._setup_frames()

    def _setup_frames(self) -> None:
        self.setObjectName(C.RouteTab.NAME)
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__scroll_frame: QScrollArea = QScrollArea()
        self.__scroll_frame.setObjectName(C.RouteTab.List.HANDLE)
        self.__scroll_frame.setWidgetResizable(True)
        self.__scroll_frame.setFrameShape(QFrame.StyledPanel)
        self.__scroll_frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.__list_frame: QWidget = QWidget()
        self.__list_frame.setObjectName(C.RouteTab.List.BOX_HANDLE)
        self.__list_layout: QVBoxLayout = QVBoxLayout(self.__list_frame)
        self.__list_layout.setAlignment(Qt.AlignTop)
        self.__list_layout.setSpacing(0)
        self.__list_layout.setContentsMargins(*C.RouteTab.List.MARGINS)

        self.__scroll_frame.setWidget(self.__list_frame)
        layout.addWidget(self.__scroll_frame)

    def _rebuild(self, plan: CraftPlan) -> None:
        while self.__list_layout.count():
            child = self.__list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        steps = plan.craft_order  # tuple of (from, to, recipe, count)
        for i, (start, skill_to, recipe, count) in enumerate(steps):
            self.__list_layout.addWidget(_Divider())  # top divider

            # Resolve material names and quantities
            materials: list[tuple[str, int]] = []
            for item_id, quantity in recipe.reagents.items():
                item_name: str = self.__item_db.by_id[item_id].item_name
                total_qty: int = quantity * count
                materials.append((item_name, total_qty))

            step = CraftRouteStep(
                start = start,
                stop = skill_to,
                name = recipe.name,
                casts = count,
                materials = materials,
            )
            self.__list_layout.addWidget(step)
        if steps: self.__list_layout.addWidget(_Divider())  # bottom divider


class _Divider(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName(C.RouteTab.List.DIVIDER_HANDLE)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setFixedHeight(C.RouteTab.List.DIVIDER_HEIGHT)


class CraftRouteStep(QWidget):
    def __init__(self, start: int, stop: int, name: str, casts: int, materials: list[tuple[str, int]]) -> None:
        super().__init__()
        self.setObjectName(C.RouteTab.List.Step.HANDLE)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(*C.RouteTab.List.Step.MARGINS)
        layout.setSpacing(C.RouteTab.List.Step.INNER_SPACING)

        # ── Header row: skill range + recipe ──────────────────────────────
        header_layout: QHBoxLayout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(C.RouteTab.List.Step.HEADER_SPACING)

        skill_range_label: QLabel = QLabel(f"[{start}, {stop}]")
        skill_range_label.setObjectName(C.RouteTab.List.Step.RANGE_HANDLE)
        skill_range_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        recipe_label: QLabel = QLabel(f"{casts} x {name}")
        recipe_label.setObjectName(C.RouteTab.List.Step.RECIPE_HANDLE)
        recipe_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        header_layout.addWidget(skill_range_label)
        header_layout.addWidget(recipe_label)
        layout.addLayout(header_layout)

        # ── Material rows ─────────────────────────────────────────────────
        for mat_name, mat_qty in materials:
            mat_label: QLabel = QLabel(f"{mat_qty} x {mat_name}")
            mat_label.setObjectName(C.RouteTab.List.Step.MAT_HANDLE)
            layout.addWidget(mat_label)
