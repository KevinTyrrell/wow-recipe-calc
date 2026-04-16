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

from PySide6.QtWidgets import QApplication
from sys import exit

from src.crafting_app import CraftingApp
from src.view.style_loader import StyleLoader
from src.view.frame.main_window import MainWindow

class UIManager:
    def __init__(self, app: CraftingApp) -> None:
        self.__craft_app: CraftingApp = app
        self.__view_app: QApplication = QApplication()
        style_loader: StyleLoader = StyleLoader()
        #   self.__view_app.setStyleSheet("QWidget { border: 1px solid red; }")
        self.__view_app.setStyleSheet(style_loader.load())
        self.__window: MainWindow = MainWindow()

    def show(self) -> None:
        self.__window.show()
        exit(self.__view_app.exec())
