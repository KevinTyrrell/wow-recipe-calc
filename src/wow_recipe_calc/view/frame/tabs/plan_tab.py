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

from typing import Optional, Callable

from PySide6.QtWidgets import QWidget

from wow_recipe_calc.crafts.craft_planner import CraftPlan


class PlanTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.__strategy: Callable[[], None] = self.__no_op
        self.__plan: Optional[CraftPlan] = None

    def invalidate(self, plan: CraftPlan) -> None:
        """
        Marks this tab's data as invalid, scheduling a rebuild

        :param plan: Updated crafting plan to replace current data
        """
        self.__plan = plan
        self.__strategy = self.__do_rebuild

    def refresh(self) -> None:
        """
        Notifies the tab that it is currently being selected

        This method should be called whenever the tab is selected.
        """
        self.__strategy()

    def _rebuild(self, plan: CraftPlan) -> None:
        """Reconstructs the content of the tab, must be implemented"""
        raise NotImplementedError

    def __no_op(self) -> None: pass

    def __do_rebuild(self) -> None:
        assert self.__plan is not None
        self._rebuild(self.__plan)
        self.__strategy = self.__no_op
