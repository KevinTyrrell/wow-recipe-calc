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
from PySide6.QtWidgets import QWidget, QVBoxLayout

import src.view.constants as C

from src.view.frame.window_banner import WindowBanner


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(C.Banner.TITLE)
        self.resize(C.Window.WIDTH, C.Window.HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)  # remove window dressing

        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(*C.Window.MARGINS)
        layout.setSpacing(0)

        banner: WindowBanner = WindowBanner(self)
        layout.addWidget(banner)


        layout.addStretch()
