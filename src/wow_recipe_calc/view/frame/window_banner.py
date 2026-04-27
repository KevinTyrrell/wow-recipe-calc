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

from typing import Callable

from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout

import wow_recipe_calc.view.constants as C


class WindowBanner(QWidget):
    def __init__(self, window_ref: QWidget) -> None:
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName(C.Banner.HANDLE)
        self.setFixedHeight(C.Banner.HEIGHT)
        title: QLabel = self.make_title()
        buttons: QWidget = self.make_buttons(window_ref)
        self.install_layout(title, buttons)
        dragger: WindowDragMover = WindowDragMover(window_ref, self)
        self.installEventFilter(dragger)  # Allow banner to be dragged

    def install_layout(self, title: QLabel, buttons: QWidget) -> None:
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(*C.Banner.MARGINS)
        spacer = QWidget()  # exists so title remains centered
        spacer.setFixedWidth(buttons.sizeHint().width())
        layout.addWidget(spacer)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(buttons)

    def make_buttons(self, window_ref: QWidget) -> QWidget:
        container: QWidget = QWidget()
        layout: QHBoxLayout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        hide: MinimizeButton = MinimizeButton(window_ref,
            C.Control.HIDE_NAME, C.Control.HIDE_SYMBOL, C.Control.WIDTH, C.Control.HEIGHT)
        close: BannerPushButton = CloseButton(window_ref,
            C.Control.CLOSE_NAME, C.Control.CLOSE_SYMBOL, C.Control.WIDTH, C.Control.HEIGHT)
        layout.addWidget(hide)
        layout.addWidget(close)
        return container

    def make_title(self) -> QLabel:
        label: QLabel = QLabel(C.Banner.TITLE)
        label.setAlignment(Qt.AlignCenter)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        return label


class BannerPushButton(QPushButton):
    def __init__(self, window_ref: QWidget, name: str, symbol: str, width: int, height: int) -> None:
        super().__init__(symbol)
        self._window_ref: QWidget = window_ref
        self.setObjectName(name)
        self.setFixedHeight(height)
        self.setFixedWidth(width)
        self.clicked.connect(self.button_clicked)

    def button_clicked(self) -> None:
        raise NotImplementedError


class CloseButton(BannerPushButton):
    def button_clicked(self) -> None:
        self._window_ref.close()


class MinimizeButton(BannerPushButton):
    def button_clicked(self) -> None:
        self._window_ref.showMinimized()


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

    def _mouse_released(self, _: QEvent) -> bool:
        self.__dragging = False
        return False
