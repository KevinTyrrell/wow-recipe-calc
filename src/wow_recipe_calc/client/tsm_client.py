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

from requests import post as submit, Response, Session
from typing import Optional, Iterator
from logging import getLogger, Logger

from wow_recipe_calc.io.resources.project import Saveable
from wow_recipe_calc.util.throttle import Throttle
from wow_recipe_calc.util.json_wrapper import wrap_json, JSO
from io.resources.ttl_cache import TTLCache, CachePolicy

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
        response: Response = submit(self._ENDPOINT_URL, json = self.__payload)
        response.raise_for_status()  # Raise error if not status ~200
        data = wrap_json(response.json())
        return data.access_token


class TSMClient(Saveable):
    _API_REALM_URL: str = "https://realm-api.tradeskillmaster.com"
    _API_PRICE_URL: str = "https://pricing-api.tradeskillmaster.com"
    _HEADER_KEY: str = "Authorization"
    _HEADER_FMT: str = "Bearer {}"
    _KEY_MASK_CHARS: int = 4  # Number of characters of the key to reveal for logging
    _KEY_MASK_SYMBOL: str = "*"
    _ENDPOINTS: JSO = wrap_json({
        "realms": "{}/regions/{}/realms",  # realm url, region id
        "regions": "{}/regions",  # realm url
        "auctions": "{}/ah/{}",  # price url, auction house id
    })

    def __init__(self) -> None:
        self.__session: Session = Session()
        self.__throttle: Throttle = Throttle.Builder().add(1, 2).build()
        # API key and auction house both come from user, only access via _get calls
        self.__auth: Optional[_TSMAuth] = None
        self.__auction_house: Optional[int] = None

    def set_auction_house(self, auction_house_id: int) -> None:
        """
        This field must be initialized before pricing data can be requested

        :param auction_house_id: TSM auction house ID provided by other TSM API calls
        """
        self.__auction_house = auction_house_id

    def authorize(self, api_key: str) -> None:
        """
        Attempts to request an access token from the TSM API

        Authorization must be acquired before pricing data can be requested

        :param api_key: TSM API key, provided from the user's TSM account page
        """
        self.__auth = _TSMAuth(api_key, self.__throttle)
        logger.info(f"TSM API key loaded: {self._mask_api_key(api_key)}")
        self._authorize()
        
    def market_value(self, item_id: int) -> Optional[int]:
        """
        :param item_id: Item ID to retrieve pricing information
        :return: Market value of the item, in copper, if present
        """
        return self.__cache.get(item_id)
        
    def auction_data(self, auction_house_id: int) -> JSO:
        """
        Note: This function may only be called 100 times per day
        See: https://support.tradeskillmaster.com/en_US/api-documentation/tsm-public-web-api
        
        :param auction_house_id: TSM auction house ID, provided by the TSM realm API
        :return: JSON data of all items in the auction house when scanned
        """
        logger.info(f"requesting entire auction house data for AH ID: {auction_house_id}")
        return self._request(self._ENDPOINTS.auctions.format(self._API_PRICE_URL, auction_house_id))

    def regions(self) -> Iterator[tuple[str, str, int]]:
        """
        Tuple format: (Realm Group Name, Geographic Region Name, Region ID)
        
        :return: Iterator of all known World of Warcraft regions
        """
        logger.debug(f"requesting TSM API region data")
        jso: JSO = self._request(self._ENDPOINTS.regions.format(self._API_REALM_URL))
        return ((e.gameVersion, e.label, e.regionId) for e in jso.items)
        
    def realms(self, region_id: int) -> Iterator[tuple[str, int, JSO]]:
        """
        Tuple format: (Realm Name, Realm ID, Auction House Table)
        
        :return: Iterator of all known World of Warcraft regions
        """
        logger.debug(f"requesting TSM API realm data for region ID: {region_id}")
        jso: JSO = self._request(self._ENDPOINTS.realms.format(self._API_REALM_URL, region_id))
        return ((e.label, e.realmId, e.auctionHouses) for e in jso.items)

    def _authorize(self) -> None:  # call this method to reauthorize if token expires
        assert self.__auth is not None
        self.__session.headers[self._HEADER_KEY] = self._HEADER_FMT.format(self._get_auth().authorize())

    def _get_auth(self) -> _TSMAuth:
        if self.__auth is None:
            raise RuntimeError("missing TSM API key, provide api key to: authorize()")
        return self.__auth

    def _get_auction_house(self) -> int:
        if self.__auction_house is None:
            raise RuntimeError("missing auction house ID, provide id to: set_auction_house()")
        return self.__auction_house

    def _request(self, url: str) -> JSO:
        """Requests information from the TSM API, requesting twice if no authorization"""
        self.__throttle.tick()
        response: Response = self.__session.get(url)
        if response.status_code == 401:  # invalid access token
            logger.warning("TSM API access token rejected (401) — re-authorizing and retrying")
            self._authorize()  # attempt to retrieve a fresh auth token
            response = self.__session.get(url)
        response.raise_for_status()
        return wrap_json(response.json())

    @classmethod
    def _mask_api_key(cls, key: str) -> str:
        """Returns a masked variant of an API key, only revealing some characters"""
        section_len: int = cls._KEY_MASK_CHARS + cls._KEY_MASK_CHARS
        if len(key) < section_len + section_len:
            logger.warning("TSM API key is atypically short, check for bad key")
        dx: int = len(key) - section_len - cls._KEY_MASK_CHARS
        suffix: str = key[len(key) - min(dx, cls._KEY_MASK_CHARS):]
        return suffix.rjust(section_len + section_len, cls._KEY_MASK_SYMBOL)

    def _refresh_auction_house(self) -> dict[int, int]:
        """Requests auction house data from the TSM API"""
        ah_data: JSO = self.auction_data(self._get_auction_house())
        price_by_id: dict[int, int] = dict()
        for item_jso in ah_data:
            if item_jso.itemId is not None:
                if item_jso.marketValue is not None:
                    price_by_id[item_jso.itemId] = item_jso.marketValue
                else: logger.warning(f"TSM API item has no market value, item ID: {item_jso.itemId}")
            else: logger.warning(f"TSM API reported null item ID, 'petSpeciesId'={item_jso.petSpeciesId}")
        return price_by_id
