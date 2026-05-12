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

from typing import Callable

from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout

import wow_recipe_calc.view.constants as C


class WindowBanner(QWidget):
    def __init__(self, window: QWidget) -> None:
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName(C.Banner.HANDLE)
        self.setFixedHeight(C.Banner.HEIGHT)
        pin, buttons = self.make_buttons(window)
        self.install_layout(self.make_title(), pin, buttons)
        dragger: WindowDragMover = WindowDragMover(window, self)
        self.installEventFilter(dragger)  # Allow banner to be dragged

    def install_layout(self, title: QLabel, pin_button: QWidget, buttons: QWidget) -> None:
        layout: QHBoxLayout = QHBoxLayout(self)
        layout.setContentsMargins(*C.Banner.MARGINS)
        layout.addWidget(pin_button)
        spacer: QWidget = QWidget()
        spacer.setFixedWidth(C.Banner.OFFSET)
        layout.addWidget(spacer)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(buttons)

    def make_buttons(self, window: QWidget) -> tuple[QWidget, QWidget]:
        container: QWidget = QWidget()
        layout: QHBoxLayout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        pin: PinButton = PinButton(window, C.Banner.Button.WIDTH, C.Banner.Button.HEIGHT)
        hide: MinimizeButton = MinimizeButton(window, C.Banner.Button.WIDTH, C.Banner.Button.HEIGHT)
        close: CloseButton = CloseButton(window, C.Banner.Button.WIDTH, C.Banner.Button.HEIGHT)
        pin.setToolTip(C.Banner.Button.Pin.TOOLTIP)
        layout.addWidget(hide)
        layout.addWidget(close)
        return pin, container

    def make_title(self) -> QLabel:
        label: QLabel = QLabel(C.Banner.TITLE)
        label.setAlignment(Qt.AlignCenter)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)
        return label


class BannerPushButton(QPushButton):
    def __init__(self, window: QWidget, name: str, symbol: str, width: int, height: int) -> None:
        super().__init__(symbol)
        self._window: QWidget = window
        self.setObjectName(name)
        self.setFixedHeight(height)
        self.setFixedWidth(width)
        self.clicked.connect(self.button_clicked)

    def button_clicked(self) -> None: raise NotImplementedError


class CloseButton(BannerPushButton):
    def __init__(self, window: QWidget, width: int, height: int) -> None:
        super().__init__(window, C.Banner.Button.Close.HANDLE, C.Banner.Button.Close.SYMBOl, width, height)
    def button_clicked(self) -> None:
        self._window.close()


class MinimizeButton(BannerPushButton):
    def __init__(self, window: QWidget, width: int, height: int) -> None:
        super().__init__(window, C.Banner.Button.Minimize.HANDLE, C.Banner.Button.Minimize.SYMBOL, width, height)
    def button_clicked(self) -> None:
        self._window.showMinimized()


class PinButton(BannerPushButton):
    def __init__(self, window: QWidget, width: int, height: int) -> None:
        super().__init__(window, C.Banner.Button.Pin.HANDLE_OFF, C.Banner.Button.Pin.SYMBOL, width, height)
        self.__pinned: bool = False
        self._refresh_style()

    def button_clicked(self) -> None:
        self.__pinned = not self.__pinned
        flags: Qt.WindowFlags = self._window.windowFlags()
        if self.__pinned: self._window.setWindowFlags(flags | Qt.WindowStaysOnTopHint)  # disable
        else: self._window.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)  # enable
        self._window.show()  # required — setWindowFlags hides the window
        self._refresh_style()

    def _refresh_style(self) -> None:
        # Swap object name so QSS can target pinned vs unpinned state
        self.setObjectName(C.Banner.Button.Pin.HANDLE_ON if self.__pinned else C.Banner.Button.Pin.HANDLE_OFF)
        self.style().unpolish(self)  # Force QSS to refresh the frame
        self.style().polish(self)


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
