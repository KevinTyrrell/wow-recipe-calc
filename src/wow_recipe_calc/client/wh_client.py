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

from typing import Optional
from functools import cached_property
from re import Match, search
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from logging import getLogger, Logger
from functools import reduce
from requests import Response, get as query

from wow_recipe_calc.io.enums import Expansion, Profession
from wow_recipe_calc.util.throttle import Throttle

logger: Logger = getLogger(__name__)


class WHClient:
    _RE_TITLE_PATTERN: str = r"^(.+?)\s*-\s*Item"
    _PARSER_TYPE: str = "html.parser"
    
    def __init__(self, throttle: Throttle, expac: Expansion, prof: Profession) -> None:
        """
        :param throttle: Throttle for web requests
        """
        self.__throttle: Throttle = throttle
        self.__url: _WHURLDirector = _WHURLDirector(expac)
        self.__prof: Profession = prof

    def request(self, url: str) -> BeautifulSoup:
        """Requests from a specified url, obeying throttles, and souping"""
        self.__throttle.tick()
        response: Response = query(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, self._PARSER_TYPE)

    def get_item_name(self, item_id: int) -> Optional[str]:
        """
        :param item_id: Item ID to request
        :return: Item name, if it can be ascertained
        """
        logger.info(f"requesting web information for item ID: {item_id}")
        soup: BeautifulSoup = self.request(self.__url.item(item_id))
        if soup.title and soup.title.string:
            title: str = soup.title.string.strip()
            matcher: Optional[Match[str]] = search(self._RE_TITLE_PATTERN, title)
            if matcher: return matcher.group(1)
        return None


class _WHURLDirector:
    _BASE_URL: str = "https://www.wowhead.com/"
    _RECIPES_SUB_DOMAIN: str = "spells/"
    _ITEM_GET_FMT: str = "item={}"

    def __init__(self, expansion: Expansion) -> None:
        self.__expac: Expansion = expansion

    def item(self, item_id: int) -> str:
        """Retrieves the url for item name information"""
        return urljoin(self.realm_url, self._ITEM_GET_FMT.format(item_id))

    def recipes(self, prof: Profession) -> str:
        """Retrieves the url for the recipe data table"""
        if prof.expansion > self.__expac.ordinal:
            raise ValueError(f"'{prof.name}' recipes cannot be requested as "
                             f"profession did not exist in '{self.__expac.name}'")
        return reduce(urljoin, (self._RECIPES_SUB_DOMAIN, prof.portal), self.realm_url)

    @cached_property
    def realm_url(self) -> str:
        """Entry-point to all URL navigation"""
        if self.__expac.portal is None:
            return self._BASE_URL  # retail has no sub-domain
        return urljoin(self._BASE_URL, f"{self.__expac.portal}/")
