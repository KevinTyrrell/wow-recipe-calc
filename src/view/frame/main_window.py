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
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QTabWidget, QHBoxLayout,
    QSpinBox, QFrame, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys

from src.view.constants import *
from src.view.style_loader import StyleLoader


class Divider(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(4)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255,255,255,0),
                    stop:0.2 rgba(255,255,255,120),
                    stop:0.5 rgba(255,255,255,200),
                    stop:0.8 rgba(255,255,255,120),
                    stop:1 rgba(255,255,255,0)
                );
            }
        """)

class RecipeItem(QWidget):
    def __init__(self, name):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(name)
        self.spin = QSpinBox()
        self.spin.setMinimum(1)
        self.spin.setValue(1)
        self.spin.setFixedWidth(60)

        layout.addWidget(self.label)
        layout.addSpacing(5)
        layout.addWidget(self.spin)
        self.setLayout(layout)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WindowConfig.name)
        self.resize(WindowConfig.width, WindowConfig.height)

        self.all_recipes = [
            "Iron Grenade", "Bronze Framework", "Copper Bolt",
            "Silver Contact", "Rough Blasting Powder"
        ]

        self.selected_recipes = {}

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(10)

        title = QLabel("WoW Recipe Calculator")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: white;")

        main_layout.addWidget(title)
        main_layout.addWidget(Divider())

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.South)

        self.edit_tab = QWidget()
        self.bom_tab = QWidget()
        self.route_tab = QWidget()
        self.cost_tab = QWidget()

        self.tabs.addTab(self.edit_tab, WindowTabs.edit_tab_name)
        self.tabs.addTab(self.bom_tab, WindowTabs.bom_tab_name)
        self.tabs.addTab(self.route_tab, WindowTabs.route_tab_name)
        self.tabs.addTab(self.cost_tab, WindowTabs.cost_tab_name)

        self.setup_edit_tab()

        main_layout.addWidget(self.tabs)
        main_layout.addWidget(Divider())

        self.setLayout(main_layout)

    def setup_edit_tab(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search recipes...")
        self.search.textChanged.connect(self.filter_recipes)

        layout.addWidget(self.search)
        layout.addWidget(Divider())

        self.list_a = QListWidget()
        self.list_a.addItems(self.all_recipes)
        self.list_a.itemClicked.connect(self.add_recipe)

        layout.addWidget(self.list_a)
        layout.addWidget(Divider())

        self.list_b = QListWidget()

        layout.addWidget(self.list_b)

        self.edit_tab.setLayout(layout)

    def filter_recipes(self):
        text = self.search.text().strip().lower()
        self.list_a.clear()
        for r in self.all_recipes:
            if r not in self.selected_recipes and text in r.lower():
                self.list_a.addItem(r)

    def add_recipe(self, item):
        name = item.text()
        self.selected_recipes[name] = 1

        self.filter_recipes()

        widget = RecipeItem(name)
        list_item = QListWidgetItem()
        list_item.setSizeHint(widget.sizeHint())

        self.list_b.addItem(list_item)
        self.list_b.setItemWidget(list_item, widget)

        widget.spin.setFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    style_loader: StyleLoader = StyleLoader()
    app.setStyleSheet(style_loader.load())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
