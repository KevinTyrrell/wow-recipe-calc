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

from src.util.log_manager import LogManager
from src.crafts.recipe.recipe_state import RecipeStateCore
from src.crafting_app import CraftingApp
from src.view.frame.window_banner import WindowBanner
from src.view.frame.tabs.edit_tab import EditTab

logger: logging.Logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    def __init__(self, craft_app: CraftingApp, state: RecipeStateCore, logs: LogManager) -> None:
        """
        :param craft_app: Entry-point to crafting, recipe, material, and cost information
        :param state: Observable mapping of selected recipes -> desired number of products
        :param logs: Log history buffer, for retrieving logging prior to GUI being displayed
        """
        super().__init__()
        self.__craft_app: CraftingApp = craft_app
        self.__state: RecipeStateCore = state
        self._configure_window()
        self._setup_ui()
        self._setup_logging(logs)

    def _configure_window(self) -> None:
        """Initializes the main window frame properties"""
        self.setWindowTitle(C.Banner.TITLE)
        self.resize(C.Window.WIDTH, C.Window.HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)

    def _setup_ui(self) -> None:
        """Builds the layout and initializes all child widgets"""
        self.__layout: QVBoxLayout = QVBoxLayout(self)
        self.__layout.setContentsMargins(*C.Window.MARGINS)
        self.__layout.setSpacing(C.Window.SPACING)
        # Header
        self.__banner: WindowBanner = WindowBanner(self)
        self.__layout.addWidget(self.__banner)
        # Content (Tabs)
        self.__tabs: QTabWidget = self._create_tab_widget()
        self.__layout.addWidget(self.__tabs)
        # Footer (Console)
        self.__console: QPlainTextEdit = QPlainTextEdit()
        self.__console.setReadOnly(True)
        self.__console.setMaximumBlockCount(C.Console.MAX_LINES)
        self.__console.setObjectName(C.Console.HANDLE)
        self.__console.setFixedHeight(C.Console.HEIGHT)
        self.__layout.addWidget(self.__console)

    def _create_tab_widget(self) -> QTabWidget:
        """Configures and returns the central tab navigation"""
        tabs: QTabWidget = QTabWidget()
        tabs.setTabPosition(QTabWidget.South)
        self.__edit_tab: EditTab = EditTab(self.__craft_app, self.__state)
        tabs.addTab(self.__edit_tab, C.Tab.EDIT_NAME)
        return tabs

    def _setup_logging(self, logs: LogManager) -> None:
        """Hooks the Python logging system into the console widget"""
        self.__log_handler: LogEmitter = LogEmitter(self.__console)
        for record in logs.history:
            self.__log_handler.emit(record)
        logs.stop_buffering()  # stop saving logs to ram
        logger.addHandler(self.__log_handler)
        logger.setLevel(logging.INFO)


class LogEmitter(logging.Handler):
    _LOG_FMT: str = "[%(asctime)s] (%(levelname)s) [%(name)s] %(message)s"
    _TIME_FMT: str = "%I:%M:%S %p"

    def __init__(self, widget: QPlainTextEdit):
        super().__init__()
        self.__editor: QPlainTextEdit = widget
        self.setFormatter(logging.Formatter(self._LOG_FMT, datefmt=self._TIME_FMT))

    def emit(self, record: logging.LogRecord):
        msg: str = self.format(record)
        self.__editor.appendPlainText(msg)
