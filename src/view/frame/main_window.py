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

        btn_min = QPushButton(C.Control.HIDE_SYMBOL)
        btn_close = QPushButton(C.Control.CLOSE_SYMBOL)
        for btn in (btn_min, btn_close):
            btn.setFixedSize(C.Control.WIDTH, C.Control.HEIGHT)
        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.close)
        btn_min.setObjectName(C.Control.HIDE_NAME)
        btn_close.setObjectName(C.Control.CLOSE_NAME)

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

        # =========================
        # Content Area
        # =========================
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 12, 0, 0)
        content_layout.setSpacing(12)

        # --- Panel 1 (Tabs) ---
        panel1 = self._make_panel()
        panel1_layout = QVBoxLayout(panel1)

        tabs = QTabWidget()
        panel1_layout.addWidget(tabs)

        # --- Panel 2 (Controls row) ---
        panel2 = self._make_panel()
        panel2_layout = QHBoxLayout(panel2)

        btn1 = QPushButton("Action 1")
        btn2 = QPushButton("Action 2")
        btn2.setObjectName("secondary")

        panel2_layout.addWidget(btn1)
        panel2_layout.addWidget(btn2)
        panel2_layout.addStretch()

        # --- Panel 3 (Input row) ---
        panel3 = self._make_panel()
        panel3_layout = QHBoxLayout(panel3)

        input_box = QLineEdit()
        input_box.setPlaceholderText("Enter something...")

        submit = QPushButton("Submit")

        panel3_layout.addWidget(input_box)
        panel3_layout.addWidget(submit)

        # Add panels
        content_layout.addWidget(panel1)
        content_layout.addWidget(panel2)
        content_layout.addWidget(panel3)

        root_layout.addWidget(banner_frame)
        root_layout.addWidget(content)

        dragger: WindowDragMover = WindowDragMover(self, banner_frame)
        banner_frame.installEventFilter(dragger)  # Allow window to be dragged

    # =========================
    # Panel helper
    # =========================
    def _make_panel(self):
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        return panel

def make_ctrl_button(name: str, symbol: str, width: int, height: int,
                     click: Callable[[Optional[bool]], Optional[bool]]) -> QPushButton:
    btn: QPushButton = QPushButton(symbol)
    btn.setFixedSize(width, height)
    btn.setObjectName(name)
    btn.clicked.connect(click)
    return btn


class WindowDragMover(QObject):
    def __init__(self, window: QWidget, draggable: QWidget):
        super().__init__(window)
        self.__window = window
        self.__draggable = draggable
        self.__dragging: bool = False
        self.__drag_pos: Optional[QPoint] = None
        self.__handlers: dict[QEvent.Type, Callable[[QEvent], bool]] = {
            QEvent.Type.MouseButtonPress: self._mouse_pressed,
            QEvent.Type.MouseMove: self._mouse_moved,
            QEvent.Type.MouseButtonRelease: self._mouse_released,
        }

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # override
        if not obj is self.__draggable: return False
        handler: Callable[[QEvent], bool] = self.__handlers.get(event.type(), None)
        return handler(event) if handler else False

    def _mouse_pressed(self, event: QEvent):
        if event.button() == Qt.LeftButton:
            self.__dragging = True
            self.__drag_pos = event.globalPosition().toPoint() - self.__window.frameGeometry().topLeft()
            event.accept()
            return True
        return False

    def _mouse_moved(self, event: QEvent) -> bool:
        if self.__dragging:
            self.__window.move(event.globalPosition().toPoint() - self.__drag_pos)
            event.accept()
            return True
        return False

    def _mouse_released(self, event: QEvent) -> bool:
        self.__dragging = False
        return False
