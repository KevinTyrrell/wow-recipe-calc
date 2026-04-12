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

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QPushButton,
    QLineEdit, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.view.constants import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(WindowConfig.name)
        self.resize(WindowConfig.width, WindowConfig.height)

        # --- Frameless window ---
        self.setWindowFlags(Qt.FramelessWindowHint)

        # --- Drag state ---
        self._dragging = False
        self._drag_pos = None

        # --- Root layout ---
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(0)

        # --- Main container ---
        container = QWidget()
        container.setObjectName("container")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # =========================
        # Top Bar
        # =========================
        top_bar = QWidget()
        top_bar.setObjectName("topbar")
        top_bar.setFixedHeight(48)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 0, 12, 0)

        title = QLabel(WindowConfig.name)
        title.setFont(QFont("Arial", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setAttribute(Qt.WA_TransparentForMouseEvents)

        btn_min = QPushButton("—")
        btn_close = QPushButton("✕")
        for btn in (btn_min, btn_close):
            btn.setFixedSize(32, 24)
        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.close)
        btn_min.setObjectName("secondary")
        btn_close.setObjectName("close")

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(btn_min)
        button_layout.addWidget(btn_close)

        left_spacer = QWidget()
        left_spacer.setFixedWidth(button_container.sizeHint().width())
        top_layout.addWidget(left_spacer)
        top_layout.addStretch()
        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(button_container)

        # =========================
        # Content Area
        # =========================
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
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
        container_layout.addWidget(top_bar)
        container_layout.addWidget(content)
        root.addWidget(container)

        self._drag_widget = top_bar

        # =========================
        # Global Styling
        # =========================
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #dddddd;
                font-family: Arial;
            }
            QWidget#topbar > QWidget {
                background-color: transparent;
            }
            QWidget#container {
                background-color: #2b2b2b;
                border-radius: 10px;
            }
            QWidget#topbar QLabel {
                background-color: transparent;
                border: none;
            }
            QWidget#topbar {
                background-color: #2f2f2f;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #3a3a3a;
            }

            QWidget#panel {
                background-color: #333333;
                border-radius: 8px;
                border: 1px solid #3f3f3f;
            }

            QPushButton {
                background-color: #2d79c7;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }

            QPushButton:hover {
                background-color: #3c8ee6;
            }

            QPushButton:pressed {
                background-color: #1f5a96;
            }

            QPushButton#secondary {
                background-color: #444;
            }

            QPushButton#secondary:hover {
                background-color: #555;
            }

            QPushButton#close:hover {
                background-color: #c94a4a;
            }

            QLineEdit {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px;
            }

            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                background: #2a2a2a;
            }
        """)

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