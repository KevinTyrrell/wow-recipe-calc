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

from pathlib import Path
from functools import lru_cache

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt

from wow_recipe_calc.io.resources.project import Project
from wow_recipe_calc.crafts.craft_planner import CraftPlan
from wow_recipe_calc.crafts.recipe.recipe import Recipe
from wow_recipe_calc.view.frame.tabs.plan_tab import PlanTab

import wow_recipe_calc.view.constants as C


def _copper_to_str(copper: int) -> str:
    g, remainder = divmod(copper, 10_000)
    s, c = divmod(remainder, 100)
    parts = []
    if g: parts.append(f"{g}g")
    if s: parts.append(f"{s}s")
    if c or not parts: parts.append(f"{c}c")
    return " ".join(parts)


class CostTab(PlanTab):
    def __init__(self) -> None:
        super().__init__()
        self._setup_frames()

    def _setup_frames(self) -> None:
        self.setObjectName(C.CostTab.NAME)
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Total cost summary header ──────────────────────────────────────
        self.__header: QWidget = QWidget()
        self.__header.setObjectName(C.CostTab.Header.HANDLE)
        self.__header.setAttribute(Qt.WA_StyledBackground, True)
        header_layout: QHBoxLayout = QHBoxLayout(self.__header)
        header_layout.setContentsMargins(*C.CostTab.Header.MARGINS)

        header_title: QLabel = QLabel(C.CostTab.Header.LABEL)
        header_title.setObjectName(C.CostTab.Header.LABEL_HANDLE)

        self.__total_label: QLabel = QLabel()
        self.__total_label.setObjectName(C.CostTab.Header.TOTAL_HANDLE)
        self.__total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addWidget(header_title)
        header_layout.addWidget(self.__total_label)
        layout.addWidget(self.__header)

        # ── Per-recipe scrollable list ─────────────────────────────────────
        self.__scroll_frame: QScrollArea = QScrollArea()
        self.__scroll_frame.setObjectName(C.CostTab.List.HANDLE)
        self.__scroll_frame.setWidgetResizable(True)
        self.__scroll_frame.setFrameShape(QFrame.StyledPanel)
        self.__scroll_frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.__list_frame: QWidget = QWidget()
        self.__list_frame.setObjectName(C.CostTab.List.BOX_HANDLE)
        self.__list_layout: QVBoxLayout = QVBoxLayout(self.__list_frame)
        self.__list_layout.setAlignment(Qt.AlignTop)
        self.__list_layout.setSpacing(0)
        self.__list_layout.setContentsMargins(*C.CostTab.List.MARGINS)

        self.__scroll_frame.setWidget(self.__list_frame)
        layout.addWidget(self.__scroll_frame)

    def _rebuild(self, plan: CraftPlan) -> None:
        self.__total_label.setText(Currency.format_coins(plan.cost, 16))

        while self.__list_layout.count():
            child = self.__list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Sort by total recipe cost descending, ties broken by name
        rows: list[tuple[str, int, int, int]] = []  # name, count, per-cast, total
        for recipe, cost_per_cast in plan.craft_costs.items():
            count: int = plan.craft_counts[recipe]
            rows.append((recipe.name, count, cost_per_cast, cost_per_cast * count))
        rows.sort(key=lambda r: (-r[3], r[0]))

        for name, count, cost_per_cast, total_cost in rows:
            row: CostRow = CostRow(name, count, cost_per_cast, total_cost)
            self.__list_layout.addWidget(row)


class CostRow(QWidget):
    def __init__(self, name: str, count: int, cost_per_cast: int, total_cost: int) -> None:
        super().__init__()
        self.setObjectName(C.CostTab.List.Row.HANDLE)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(*C.CostTab.List.Row.MARGINS)

        name_label: QLabel = QLabel(f"{count}x  {name}")
        name_label.setObjectName(C.CostTab.List.Row.NAME_HANDLE)
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        per_cast_label: QLabel = QLabel(_copper_to_str(cost_per_cast))
        per_cast_label.setObjectName(C.CostTab.List.Row.PER_CAST_HANDLE)
        per_cast_label.setFixedWidth(C.CostTab.List.Row.PER_CAST_WIDTH)
        per_cast_label.setAlignment(Qt.AlignCenter)

        total_label: QLabel = QLabel(_copper_to_str(total_cost))
        total_label.setObjectName(C.CostTab.List.Row.TOTAL_HANDLE)
        total_label.setFixedWidth(C.CostTab.List.Row.TOTAL_WIDTH)
        total_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(name_label)
        layout.addWidget(per_cast_label)
        layout.addWidget(total_label)


class Currency:
    _RESOURCE: Path = Path("res/coins")
    _EXTENSION: str = "png"
    #  f'COINS<img src="{coin_path.as_posix()}" width="SIZE" height="SIZE">'
    _COIN_SRC_FMT: str = 'img src="{}"'
    _COIN_ICON_FMT: str = '{{0}}<{0} width="{{1}}" height="{{1}}">'
    _COPPER, _SILVER, _GOLD = "copper", "silver", "gold"
    _COPPER_PER_GOLD, _COPPER_PER_SILVER = 100 * 100, 100

    @classmethod
    def format_coins(cls, coins: int, size: int) -> str:
        sections: list[str] = list()
        change: int = coins % cls._COPPER_PER_GOLD
        gold: int = coins // cls._COPPER_PER_GOLD
        silver: int = change // cls._COPPER_PER_SILVER
        copper: int = change % cls._COPPER_PER_SILVER
        if gold > 0:
            sections.append(cls._get_coin_fmt(cls._GOLD).format(gold, size))
        if silver > 0:
            sections.append(cls._get_coin_fmt(cls._SILVER).format(silver, size))
        sections.append(cls._get_coin_fmt(cls._COPPER).format(copper, size))
        return str().join(sections)

    @classmethod
    @lru_cache(maxsize = 3)
    def _get_coin_fmt(cls, name: str) -> str:
        path: Path = Project.resource(name, cls._RESOURCE, cls._EXTENSION)
        src: str = cls._COIN_SRC_FMT.format(path.as_posix())
        return cls._COIN_ICON_FMT.format(src)

