#  Copyright (C) 2026  Kevin Tyrrell
# GUI-driven WoW profession analyzer for material aggregation, cost calculation, and optimized crafting sequences
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

from requests import post as submit, Response, Session
from typing import Optional, Iterator
from logging import getLogger, Logger
from pathlib import Path

from io.project_info import get_project_root
from wow_recipe_calc.util.throttle import Throttle
from wow_recipe_calc.util.json_wrapper import wrap_json, JSO
from io.resources.local_cache import TTLCache, CachePolicy

logger: Logger = getLogger(__name__)


class _TSMAuth:
    _ENDPOINT_URL: str = "https://auth.tradeskillmaster.com/oauth2/token"
    _REQUEST_KEY: str = "token"  # "token": "<YOUR_API_KEY>"
    _POST_PAYLOAD: dict[str, str] = {  # In most cases these do not change
        "client_id": "c260f00d-1071-409a-992f-dda2e5498536",
        "grant_type": "api_token",
        "scope": "app:realm-api app:pricing-api",
    }
    
    def __init__(self, api_key: str, throttle: Throttle) -> None:
        self.__throttle: Throttle = throttle
        payload: dict[str, str] = self._POST_PAYLOAD.copy()
        payload[self._REQUEST_KEY] = api_key
        self.__payload: dict[str, str] = payload
    
    def authorize(self) -> str:
        logger.debug("requesting TSM API access_token")
        self.__throttle.tick()
        response: Response = submit(self._ENDPOINT_URL, json=self.__payload)
        response.raise_for_status()  # Raise error if not status ~200
        data = wrap_json(response.json())
        return data.access_token


class TSMClient:
    _LOCAL_DB_NAME: str = "tsm_db"
    _LOCAL_DB_DIR_PATH: str = "cache"
    _CACHE_DB_KEY: str = "REALM_MARKET_VALUE_PRICES"
    _API_REALM_URL: str = "https://realm-api.tradeskillmaster.com"
    _API_PRICE_URL: str = "https://pricing-api.tradeskillmaster.com"
    _FAKE_API_KEY: str = "a3f9c7d2-b6e1-9c2a-f7d1-3b8e4a91c6d2"  # stand-in
    _DEFAULT_AUCTION_HOUSE: int = 4
    _DEFAULT_PRICING_STALE: int = 3 * 60 * 60  # 3 hours before pricing becomes stale
    
    def __init__(self) -> None:
        self.auction_house: int = self._DEFAULT_AUCTION_HOUSE
        self.__api_key: str = self._FAKE_API_KEY
        dir_path: Path = get_project_root() / self._LOCAL_DB_DIR_PATH
        self.__cache: TTLCache = TTLCache(self._LOCAL_DB_NAME, str(dir_path))
        self.__session: Session = Session()
        self.__policy: CachePolicy = CachePolicy(
            self._DEFAULT_PRICING_STALE, self._refresh_auction_house)
        self.__throttle: Throttle = Throttle.Builder().add(1, 2).build()

    def authorize(self, api_key: str) -> None:
        """
        Attempts to request an access token from the TSM API

        :param api_key: TSM API key, provided from the user's TSM account page
        """
        auth: _TSMAuth = _TSMAuth(api_key, self.__throttle)
        self.__api_key = api_key
        self.__session.headers.update({ "Authorization": f"Bearer {auth.authorize()}" })
        
    def _refresh_auction_house(self, _) -> dict[int, int]:
        ah_jso = wrap_json(self.auction_data(self.auction_house))
        price_by_id: dict[int, int] = dict()
        for item_jso in ah_jso:
            if item_jso.itemId is not None:
                if item_jso.marketValue is not None:
                    price_by_id[item_jso.itemId] = item_jso.marketValue
                else: logger.warning(f"TSM API item has no market value, item ID: {item_jso.itemId}")
            else: logger.warning(f"TSM API reported null item ID, 'petSpeciesId'={item_jso.petSpeciesId}")
        return price_by_id
        
    def get_price(self, item_id: int) -> Optional[int]:
        price_by_id: dict[int, int] = self.__cache.fetch(self._CACHE_DB_KEY, self.__policy)
        return price_by_id.get(item_id)
        
    def auction_data(self, auction_house_id: int) -> list[dict[str, Optional[int]]]:
        """
        Note: This function may only be called 100 times per day
        See: https://support.tradeskillmaster.com/en_US/api-documentation/tsm-public-web-api
        
        :param auction_house_id: TSM auction house ID, provided by the TSM realm API
        :return: JSON data of all items in the auction house when scanned
        """
        logger.info(f"requesting entire auction house data for AH ID: {auction_house_id}")
        self.__throttle.tick()
        response: Response = self.__session.get(f"{self._API_PRICE_URL}/ah/{auction_house_id}")
        response.raise_for_status()
        return response.json()
    
    def regions(self) -> Iterator[tuple[str, str, int]]:
        """
        Tuple format: (Realm Group Name, Geographic Region Name, Region ID)
        
        :return: Iterator of all known World of Warcraft regions
        """
        logger.debug(f"requesting TSM API region data")
        self.__throttle.tick()
        response: Response = self.__session.get(f"{self._API_REALM_URL}/regions")
        response.raise_for_status()
        jso = wrap_json(response.json())
        return ((e.gameVersion, e.name, e.regionId) for e in jso.items)
        
    def realms(self, region_id: int) -> Iterator[tuple[str, int, JSO]]:
        """
        Tuple format: (Realm Name, Realm ID, Auction House Table)
        
        :return: Iterator of all known World of Warcraft regions
        """
        logger.debug(f"requesting TSM API realm data for region ID: {region_id}")
        self.__throttle.tick()
        response: Response = self.__session.get(f"{self._API_REALM_URL}/regions/{region_id}/realms")
        response.raise_for_status()
        jso = wrap_json(response.json())
        return ((e.name, e.realmId, e.auctionHouses) for e in jso.items)
        
    def save(self) -> None:
        """
        Saves TSM data to the storage medium
        """
        self.__cache.save()
