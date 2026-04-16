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
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QPushButton,
    QLineEdit, QFrame)

from typing import cast


import src.view.constants as C


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(C.Banner.TITLE)
        self.resize(C.Window.WIDTH, C.Window.HEIGHT)
        self.setWindowFlags(Qt.FramelessWindowHint)  # remove window dressing

        # --- Drag state ---
        self._dragging = False
        self._drag_pos = None

        root_layout: QVBoxLayout = QVBoxLayout(self)
        root_layout.setContentsMargins(*C.Window.MARGINS)
        root_layout.setSpacing(0)

        # =========================
        # Banner
        # =========================
        banner_frame = QWidget()
        banner_frame.setObjectName(C.Banner.HANDLE)
        banner_frame.setFixedHeight(48)

        title: QLabel = QLabel(C.Banner.TITLE)
        title.setAlignment(Qt.AlignCenter)
        title.setAttribute(Qt.WA_TransparentForMouseEvents)

        btn_min = QPushButton("—")
        btn_close = QPushButton("✕")
        for btn in (btn_min, btn_close):
            btn.setFixedSize(C.Banner.BUTTON_WIDTH, C.Banner.BUTTON_HEIGHT)
        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.close)
        btn_min.setObjectName("secondary")
        btn_close.setObjectName("close")

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(btn_min)
        button_layout.addWidget(btn_close)

        left_spacer = QWidget()  # exists so title remains centered
        left_spacer.setFixedWidth(button_container.sizeHint().width())

        banner_layout = QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(*C.Banner.MARGINS)
        banner_layout.addWidget(left_spacer)
        banner_layout.addStretch()
        banner_layout.addWidget(title)
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

        # =========================
        # Assemble
        # =========================
        root_layout.addWidget(banner_frame)
        root_layout.addWidget(content)

        self._drag_widget = banner_frame

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

    # =========================
    # Dragging logic
    # =========================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._drag_widget.geometry().contains(event.position().toPoint()):
                self._dragging = True
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False