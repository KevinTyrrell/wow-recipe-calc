#  Copyright (C) 2026  Kevin Tyrrell
# GUI-driven WoW profession analyzer for material aggregation, cost calculation, and optimized crafting sequences
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

STYLE_RESOURCE_PATH: str = "wow_recipe_calc.view.styles"


class Window:
    WIDTH: int = 504
    HEIGHT: int = 912
    MARGINS: tuple[int, int, int, int] = (12, 12, 12, 12)
    SPACING: int = 10


class Control:
    CLOSE_SYMBOL: str = "✕"
    HIDE_SYMBOL: str = "—"
    CLOSE_NAME: str = "close"
    HIDE_NAME: str = "minimize"
    WIDTH: int = 32
    HEIGHT: int = 24


class Banner:
    TITLE: str = "WoW Recipe Calculator"
    HANDLE: str = "banner"
    MARGINS: tuple[int, int, int, int] = (12, 0, 12, 0)
    HEIGHT: int = 48


class EditTab:
    NAME: str = "Edit Manifest"
    HANDLE: str = "manifest"
    class SearchBar:
        HANDLE: str = "edit-search-bar"
        PROMPT: str = "Search Recipes..."
    class SelectList:
        HANDLE: str = "selected-list"
        BOX_HANDLE: str = "selected-list-container"
        MARGINS: tuple[int, int, int, int] = (5, 5, 5, 5)
        class Row:
            HANDLE: str = "recipe-row"
            NAME_HANDLE: str = "recipe-row-label"
            QTY_HANDLE: str = "recipe-row-qty"
            PRESS_PROPERTY: str = "pressed"
            MARGINS: tuple[int, int, int, int] = (0, 2, 4, 2)
            QTY_WIDTH: int = 60


class BomTab:
    NAME: str = "Bill of Materials"
    HANDLE: str = "bom"
    class List:
        HANDLE: str = "bom-list"
        BOX_HANDLE: str = "bom-list-container"
        MARGINS: tuple[int, int, int, int] = (5, 5, 5, 5)
        class Row:
            HANDLE: str = "bom-row"
            NAME_HANDLE: str = "bom-row-name"
            QTY_HANDLE: str = "bom-row-qty"
            QTY_WIDTH: int = 50
            MARGINS: tuple[int, int, int, int] = (0, 2, 4, 2)


class RouteTab:
    NAME: str = "Crafting Route"


class CostTab:
    NAME: str = "Cost Breakdown"


class Console:
    HANDLE: str = "console"
    HEIGHT: int = 100
    MAX_LINES: int = 500
