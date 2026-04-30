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
from wow_recipe_calc.view.frame.tabs.plan_tab import PlanTab

import wow_recipe_calc.view.constants as C


class BomTab(PlanTab):
    def __init__(self) -> None:
        super().__init__()
        self._setup_frames()

    def _setup_frames(self) -> None:
        self.setObjectName(C.BomTab.NAME)
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.__scroll_frame: QScrollArea = QScrollArea()
        self.__scroll_frame.setObjectName(C.BomTab.List.HANDLE)
        self.__scroll_frame.setWidgetResizable(True)
        self.__scroll_frame.setFrameShape(QFrame.StyledPanel)
        self.__scroll_frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.__list_frame: QWidget = QWidget()
        self.__list_frame.setObjectName(C.BomTab.List.BOX_HANDLE)
        self.__list_layout: QVBoxLayout = QVBoxLayout(self.__list_frame)
        self.__list_layout.setAlignment(Qt.AlignTop)
        self.__list_layout.setSpacing(0)
        self.__list_layout.setContentsMargins(*C.BomTab.List.MARGINS)

        self.__scroll_frame.setWidget(self.__list_frame)
        layout.addWidget(self.__scroll_frame)

    def _rebuild(self, plan: CraftPlan) -> None:
        while self.__list_layout.count():
            child = self.__list_layout.takeAt(0)
            if child.widget():  # cleanup existing content
                child.widget().deleteLater()
        for item_id, item_name in plan.materials:
            quantity: int = plan.craft_mats[item_id]
            row: BomRow = BomRow(item_name, quantity)
            self.__list_layout.addWidget(row)


class BomRow(QWidget):
    def __init__(self, name: str, quantity: int) -> None:
        super().__init__()
        self.setObjectName(C.BomTab.List.Row.HANDLE)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(*C.BomTab.List.Row.MARGINS)

        name_label: QLabel = QLabel(name)
        name_label.setObjectName(C.BomTab.List.Row.NAME_HANDLE)
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        qty_label: QLabel = QLabel(str(quantity))
        qty_label.setObjectName(C.BomTab.List.Row.QTY_HANDLE)
        qty_label.setFixedWidth(C.BomTab.List.Row.QTY_WIDTH)
        qty_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(name_label)
        layout.addWidget(qty_label)
