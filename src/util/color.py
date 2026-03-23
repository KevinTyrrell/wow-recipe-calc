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

from enum import Enum
from typing import Optional, Iterable
from dataclasses import dataclass

# Offset standard color -> bright color
_BRIGHT_OFFSET: int = 60
# Offset foreground color -> background color
_BACKGROUND_OFFSET: int = 10

# ANSI Style Codes
_STYLE_CODES: dict[str, int] = {
    "BOLD": 1,
    "FAINT": 2,
    "ITALIC": 3,
    "UNDERLINE": 4,
    "STRIKEOUT": 9,
}


@dataclass(frozen=True)
class _ColorCode:
    code: int
    bright: bool = False
    
    def get_code(self) -> int:
        return self.code + (_BRIGHT_OFFSET if self.bright else 0)


class _ColorInstance:
    def __init__(self, fg: _ColorCode, bg: Optional[_ColorCode]=None,
                    styles: Optional[Iterable[int]]=None) -> None:
        self.__fg: _ColorCode = fg
        self.__bg: Optional[_ColorCode] = bg
        if styles is not None:
            self.__styles: frozenset[int] = frozenset(styles)
        else: self.__styles: frozenset[int] = frozenset()
        
    @property
    def BRIGHT(self) -> _ColorInstance:
        if self.__fg.bright: return self
        return _ColorInstance(
            _ColorCode(self.__fg.code, True), self.__bg, self.__styles)
        
    def __getattr__(self, name: str) -> _ColorInstance:
        style: str = name.upper()
        code: Optional[int] = _STYLE_CODES.get(style)
        if code is None:
            raise ValueError(f"ANSI style does not exist or is not supported: {style}")
        if code in self.__styles: return self
        return _ColorInstance(self.__fg, self.__bg, self.__styles | { code })
        
    def __call__(self, text: str) -> str:
        codes: list[int] = [ self.__fg.get_code() ]
        if self.__bg is not None:
            codes.append(self.__bg.get_code() + _BACKGROUND_OFFSET)
        codes.extend(self.__styles)
        section: str = ";".join(str(code) for code in codes)
        return f"\033[{section}m{text}\033[0m"
        
    @property
    def fg(self) -> _ColorCode: return self.__fg
    @property
    def bg(self) -> _ColorCode: return self.__bg
    @property
    def styles(self) -> frozenset[int]: return self.__styles
    def __get__(self, instance, owner): return self  # Descriptor
    

class Color(Enum):
    BLACK = _ColorInstance(_ColorCode(30))
    RED = _ColorInstance(_ColorCode(31))
    GREEN = _ColorInstance(_ColorCode(32))
    YELLOW = _ColorInstance(_ColorCode(33))
    BLUE = _ColorInstance(_ColorCode(34))
    MAGENTA = _ColorInstance(_ColorCode(35))
    CYAN = _ColorInstance(_ColorCode(36))
    WHITE = _ColorInstance(_ColorCode(37))
    
    def of(fg: _ColorInstance, bg: _ColorInstance) -> _ColorInstance:
        """
        Note: If the fg has a bg or the bg has a fg,
        both are unused in the final color instance.
        
        :param fg: Color to be used in the foreground
        :param bg: Color to be used in the background
        :return: New multi-colored instance
        """
        return _ColorInstance(fg.fg, bg.fg, fg.styles)
