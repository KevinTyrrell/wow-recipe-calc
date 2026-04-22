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

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit

import src.view.constants as C

from src.crafts.recipe.recipe_state import RecipeStateCore
from src.crafting_app import CraftingApp
from src.view.frame.window_banner import WindowBanner
from src.view.frame.tabs.edit_tab import EditTab

logger: logging.Logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    def __init__(self, craft_app: CraftingApp, state: RecipeStateCore):
        super().__init__()

        self.setWindowTitle(C.Banner.TITLE)
        self.resize(C.Window.WIDTH, C.Window.HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(*C.Window.MARGINS)
        layout.setSpacing(C.Window.SPACING)

        # -------------------
        # 1. BANNER
        # -------------------
        banner: WindowBanner = WindowBanner(self)
        layout.addWidget(banner)

        # -------------------
        # 2. TAB PANE
        # -------------------
        tabs: QTabWidget = QTabWidget()
        tabs.setTabPosition(QTabWidget.South)
        edit_tab: EditTab = EditTab(craft_app, state)
        tabs.addTab(edit_tab, C.Tab.EDIT_NAME)
        layout.addWidget(tabs)

        # tabs will later be injected here
        # e.g. self.tabs.addTab(EditTab(...), "Edit")

        # -------------------
        # 3. CONSOLE OUTPUT
        # -------------------
        console: QPlainTextEdit = make_console_window()
        layout.addWidget(console)

        # -------------------
        # LOGGER HOOK
        # -------------------

        handler = LogEmitter(console)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)


def make_console_window() -> QPlainTextEdit:
    console: QPlainTextEdit = QPlainTextEdit()
    console.setReadOnly(True)
    console.setMaximumBlockCount(C.Console.MAX_LINES)  # don't persist text forever
    console.setObjectName(C.Console.HANDLE)
    console.setFixedHeight(C.Console.HEIGHT)
    return console


class LogEmitter(logging.Handler):
    _LOG_FMT: str = "[%(asctime)s] (%(levelname)s) %(message)s"
    _TIME_FMT: str = "%I:%M:%S %p"

    def __init__(self, widget: QPlainTextEdit):
        super().__init__()
        self.__editor: QPlainTextEdit = widget
        self.setFormatter(logging.Formatter(self._LOG_FMT, datefmt=self._TIME_FMT))

    def emit(self, record: logging.LogRecord):
        msg: str = self.format(record)
        self.__editor.appendPlainText(msg)
