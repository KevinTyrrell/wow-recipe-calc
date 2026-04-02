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

import requests

from typing import Optional
from re import Match, search
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from src.util.throttle import Throttle


class ItemClient:
    _RE_TITLE_PATTERN: str = r"^(.+?)\s*-\s*Item"
    _BASE_URL_WH: str = "https://www.wowhead.com/tbc/"
    _PART_URL_WH_FMT: str = "item={}"
    
    def __init__(self, throttle: Throttle) -> None:
        self.__throttle: Throttle = throttle
        
    def get_item_name(self, item_id: int) -> Optional[str]:
        self.__throttle.tick()
        url: str = urljoin(self._BASE_URL_WH, self._PART_URL_WH_FMT.format(item_id))
        response: requests.Response = requests.get(url)
        response.raise_for_status()  # Raise error if not status ~200
        soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
        if soup.title and soup.title.string:
            title: str = soup.title.string.strip()
            matcher: Optional[Match[str]] = search(self._RE_TITLE_PATTERN, title)
            if matcher: return matcher.group(1)
        return None
