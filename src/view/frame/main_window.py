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

from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QPushButton,
    QLineEdit, QFrame)

from typing import cast, Callable

import src.view.constants as C


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(C.Banner.TITLE)
        self.resize(C.Window.WIDTH, C.Window.HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)  # remove window dressing

        root_layout: QVBoxLayout = QVBoxLayout(self)
        root_layout.setContentsMargins(*C.Window.MARGINS)
        root_layout.setSpacing(0)

        banner_frame = QWidget()
        banner_frame.setObjectName(C.Banner.HANDLE)
        banner_frame.setFixedHeight(C.Banner.HEIGHT)

        lbl_title: QLabel = QLabel(C.Banner.TITLE)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setAttribute(Qt.WA_TransparentForMouseEvents)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        btn_min: QPushButton = make_ctrl_button(C.Control.HIDE_NAME,
            C.Control.HIDE_SYMBOL, C.Control.WIDTH, C.Control.HEIGHT, lambda _: self.showMinimized())
        btn_close: QPushButton = make_ctrl_button(C.Control.CLOSE_NAME,
            C.Control.CLOSE_SYMBOL, C.Control.WIDTH, C.Control.HEIGHT, lambda _: self.close())
        button_layout.addWidget(btn_min)
        button_layout.addWidget(btn_close)

        left_spacer = QWidget()  # exists so title remains centered
        left_spacer.setFixedWidth(button_container.sizeHint().width())

        banner_layout = QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(*C.Banner.MARGINS)
        banner_layout.addWidget(left_spacer)
        banner_layout.addStretch()
        banner_layout.addWidget(lbl_title)
        banner_layout.addStretch()
        banner_layout.addWidget(button_container)
        root_layout.addWidget(banner_frame)

        dragger: WindowDragMover = WindowDragMover(self, banner_frame)
        banner_frame.installEventFilter(dragger)  # Allow banner to be dragged

        root_layout.addStretch()


def make_ctrl_button(name: str, symbol: str, width: int, height: int,
                     click: Callable[[Optional[bool]], Optional[bool]]) -> QPushButton:
    btn: QPushButton = QPushButton(symbol)
    btn.setFixedSize(width, height)
    btn.setObjectName(name)
    btn.clicked.connect(click)
    return btn



