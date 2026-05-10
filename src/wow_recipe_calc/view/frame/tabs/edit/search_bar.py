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

from PySide6.QtWidgets import QLineEdit, QToolButton
from PySide6.QtCore import Qt

import wow_recipe_calc.view.constants as C


class RecipeSearchBar(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setPlaceholderText(C.EditTab.SearchBar.PROMPT)
        self.setObjectName(C.EditTab.SearchBar.HANDLE)
        self._setup_clear_button()
        self.textChanged.connect(self._on_text_changed)

    def _setup_clear_button(self) -> None:
        self.__clear_btn: QToolButton = QToolButton(self)
        self.__clear_btn.setText(C.EditTab.SearchBar.ClearButton.TEXT)
        self.__clear_btn.setObjectName(C.EditTab.SearchBar.ClearButton.HANDLE)
        self.__clear_btn.setCursor(Qt.ArrowCursor)
        self.__clear_btn.setVisible(False)
        self.__clear_btn.clicked.connect(self.clear)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_clear_btn()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._reposition_clear_btn()

    def _on_text_changed(self, text: str) -> None:
        self.__clear_btn.setVisible(bool(text))
        self._reposition_clear_btn()

    def _reposition_clear_btn(self) -> None:
        m: int = C.EditTab.SearchBar.ClearButton.MARGIN
        btn_size: int = self.height() - m * 2  # simulate an outer margin
        self.__clear_btn.setFixedSize(btn_size, btn_size)
        self.__clear_btn.move(self.width() - btn_size - m, m)
