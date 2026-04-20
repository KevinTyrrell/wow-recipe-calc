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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit

import logging

import src.view.constants as C

from src.crafts.recipe.recipe_state import RecipeStateCore
from src.crafting_app import CraftingApp
from src.view.frame.window_banner import WindowBanner


class LogEmitter(logging.Handler):
    def __init__(self, widget: QPlainTextEdit):
        super().__init__()
        self.__editor: QPlainTextEdit = widget

    def emit(self, record):
        msg: str = self.format(record)
        self.__editor.appendPlainText(msg)


class MainWindow(QWidget):
    def __init__(self, craft_app: CraftingApp, state: RecipeStateCore):
        super().__init__()

        self.setWindowTitle(C.Banner.TITLE)
        self.resize(C.Window.WIDTH, C.Window.HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(*C.Window.MARGINS)
        layout.setSpacing(C.Window.SPACING)

        # -------------------
        # 1. BANNER
        # -------------------
        banner = WindowBanner(self)
        layout.addWidget(banner)

        # -------------------
        # 2. TAB PANE
        # -------------------
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # tabs will later be injected here
        # e.g. self.tabs.addTab(EditTab(...), "Edit")

        # -------------------
        # 3. CONSOLE OUTPUT
        # -------------------
        console: QPlainTextEdit = QPlainTextEdit()
        console.setReadOnly(True)
        console.setObjectName(C.Console.HANDLE)
        console.setFixedHeight(C.Console.HEIGHT)

        layout.addWidget(console)

        # -------------------
        # LOGGER HOOK
        # -------------------

        from PySide6.QtCore import QTimer
        from datetime import datetime
        import logging
        handler = LogEmitter(console)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

        def _log_time():
            logging.info(datetime.now().strftime("%H:%M:%S"))

        self._timer = QTimer(self)
        self._timer.timeout.connect(_log_time)
        self._timer.start(1000)
