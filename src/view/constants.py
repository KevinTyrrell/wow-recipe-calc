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

class Window:
    WIDTH: int = 504
    HEIGHT: int = 912
    MARGINS: tuple[int, int, int, int] = (12, 12, 12, 12)
    SPACING: int = 10


class Tab:
    EDIT_NAME: str = "Edit Manifest"
    BOM_NAME: str = "Bill of Materials"
    ROUTE_NAME: str = "Crafting Route"
    COST_NAME: str = "Cost Breakdown"


class Banner:
    TITLE: str = "WoW Recipe Calculator"
    HANDLE: str = "banner"
    MARGINS: tuple[int, int, int, int] = (12, 0, 12, 0)
    BUTTON_WIDTH: int = 32
    BUTTON_HEIGHT: int = 24
