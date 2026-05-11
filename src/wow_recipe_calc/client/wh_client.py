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

import json

from typing import Optional, Iterator
from functools import cached_property
from re import Match, search, compile
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from logging import getLogger, Logger
from functools import reduce
from requests import Response, get as query
from dataclasses import asdict

from wow_recipe_calc.crafts.recipe.recipe import RecipeJson
from wow_recipe_calc.util.json_wrapper import JsonList, JSW, wrap_json
from wow_recipe_calc.io.enums import Expansion, Profession
from wow_recipe_calc.util.throttle import Throttle

logger: Logger = getLogger(__name__)


class WHClient:
    _RE_ITEM_TITLE: str = r"^(.+?)\s*-\s*Item"
    _RE_SPELL_TABLE: str = r"var listviewspells ="
    _RE_CAPTURE: str = r" (.+?);"
    _SOUP_LOCATE_TAG: str = "script"
    _SOUP_PARSER_TYPE: str = "html.parser"
    
    def __init__(self, throttle: Throttle, expac: Expansion, prof: Profession) -> None:
        """
        :param throttle: Throttle for web requests
        """
        self.__throttle: Throttle = throttle
        self.__url: _WHURLDirector = _WHURLDirector(expac)
        self.__prof: Profession = prof

    def get_item_name(self, item_id: int) -> Optional[str]:
        """
        :param item_id: Item ID to query
        :return: Name of the item, if it can be ascertained, else None
        """
        logger.info(f"requesting web information for item ID: {item_id}")
        soup: BeautifulSoup = self._request(self.__url.item(item_id))
        if soup.title and soup.title.string:
            title: str = soup.title.string.strip()
            matcher: Optional[Match[str]] = search(self._RE_ITEM_TITLE, title)
            if matcher: return matcher.group(1)
        return None

    def get_prof_data(self, prof: Optional[Profession] = None) -> JsonList:
        """
        :param prof: Profession to query recipe data
        :return: List of all recipes in the profession for the set expansion
        """
        profession: Profession = prof or self.__prof
        logger.info(f"requesting web information for profession: {profession.name}")
        soup: BeautifulSoup = self._request(self.__url.recipes(profession))
        table: Optional[str] = self._find_table_script(soup)
        if table is None:
            raise RuntimeError(f"table data could not be located for profession: {profession.name}")
        parser: _JsonTableParser = _JsonTableParser(table)
        # Clean the json objects and prepare them for saving to storage & recipe loading
        return [ asdict(e) for jsw in parser.elements if (e := parser.parse(jsw)) is not None ]

    def _find_table_script(self, soup: BeautifulSoup) -> Optional[str]:
        """Attempts to locate the script which populates html rows with profession data"""
        # noinspection PyTypeChecker
        script: Optional[Tag] = soup.find(self._SOUP_LOCATE_TAG, string=compile(self._RE_SPELL_TABLE))
        if script is not None:
            match: Optional[Match] = search(self._RE_SPELL_TABLE + self._RE_CAPTURE, script.string)
            if match: return match.group(1)
        return None

    def _request(self, url: str) -> BeautifulSoup:
        """Requests from a specified url, obeying throttles, and souping"""
        self.__throttle.tick()
        response: Response = query(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, self._SOUP_PARSER_TYPE)


class _JsonTableParser:
    def __init__(self, raw_table: str) -> None:
        # protect json loading from non-quoted strings
        raw_table = raw_table.replace("popularity:", "\"popularity\":")
        raw_table = raw_table.replace("quality:", "\"quality\":")
        self.__table: JsonList = json.loads(raw_table)

    @property
    def elements(self) -> Iterator[JSW]:
        """Iterates over all table data as wrapped JSON objects"""
        for data in self.__table:
            yield wrap_json(data)

    def parse(self, jso: JSW) -> Optional[RecipeJson]:
        """Parses a JSON-wrapped data table into a formal recipe JSON entry"""
        try:  # attempt to weed out 'fake' recipes
            _, _ = jso.colors, jso.reagents
        except AttributeError: return None  # silent
        try:  # failure here implies it is not a real recipe
            return RecipeJson(
                jso.name,  # name of the recipe
                jso.learnedat,  # level learned at
                jso.colors[1],  # yellow level
                jso.colors[3],  # gray level
                list(list(e) for e in jso.reagents),  # nested reagents
                jso.creates[0],  # product item id
                self._get_avg_net_produced(jso),  # avg yield
                self._get_sources(jso),  # how to obtain the recipe
                self._get_specialization(jso))  # required specialization (nullable)
        except AttributeError as e:
            logger.error(f"failed to parse wrapped recipe: {e}")
            logger.debug(f"(cont.) failed to parse recipe payload: {jso}")
        return None

    @staticmethod
    def _get_specialization(jso: JSW) -> Optional[str]:
        try:  # e.g. Spellfire Tailor, Tribal Leatherworking
            return jso.specialization
        except AttributeError: return None

    @staticmethod
    def _get_sources(jso: JSW) -> list[int]:
        try:  # 2: Drop, 4: Quest, 5: Vendor, 6: Trainer, 16: Fishing?, 21: Pickpocketing?
            return list(jso.source)
        except AttributeError: return [6]  # trainer

    @staticmethod
    def _get_avg_net_produced(jso: JSW) -> float:
        if len(jso.creates) <= 2: return float(jso.creates[1])
        return (jso.creates[1] + jso.creates[2]) / 2.0


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
