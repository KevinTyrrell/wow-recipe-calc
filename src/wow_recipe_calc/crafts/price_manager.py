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

from pathlib import Path
from typing import Optional
from logging import getLogger, Logger

from wow_recipe_calc.io.resources.project import Saveable, Resource
from wow_recipe_calc.io.resources.json_store import load_json, JsonValue
from wow_recipe_calc.io.resources.ttl_cache import TTLCache, CachePolicy
from wow_recipe_calc.crafts.item_db import ItemDB
from wow_recipe_calc.client.tsm_client import TSMClient
from wow_recipe_calc.util.json_wrapper import wrap_json, JSW

logger: Logger = getLogger(__name__)


class PriceManager(Saveable):
    _RESOURCE_MARKET_STEM: str = "market_value_db"
    _MARKET_STALE_THRESH: int = 3 * 60 * 60  # 3 hours before pricing data becomes stale
    
    def __init__(self, tsm_client: TSMClient, item_db: ItemDB) -> None:
        """
        :param tsm_client: TSM request instance for market value pricing
        :param item_db: Item DB instance for item name requesting
        """
        policy: CachePolicy = CachePolicy(self._MARKET_STALE_THRESH, tsm_client.scan_ah_market_value)
        self.__mv_cache: TTLCache = TTLCache(self._RESOURCE_MARKET_STEM, policy)  # continuously tosses stale data
        self.__vendor: Resource[int, int] = _VendorPriceDB()  # [item_id, copper cost from vendor]
        self.__unpriceable: _UnpriceableHandler = _UnpriceableHandler(item_db)
        self.__tsm_client = tsm_client
        self.__vendor.load()

    def get_price(self, item_id: int) -> int:
        """
        Retrieves the price of an item, if possible
        
        If no price is found, the method-level or object-level callback
        is used for pricing instead, after being provided the item id.
        
        :param item_id: Item ID to query price
        """
        for source in (self.__vendor.get, self.__mv_cache.get):
            price: Optional[int] = source(item_id)
            if price is not None: return price
        return self.__unpriceable.fallback_price(item_id)

    def market_value(self, item_id: int) -> Optional[int]:
        """
        :param item_id: Item ID to retrieve pricing information
        :return: Market value of the item, in copper, if present
        """
        return self.__mv_cache.get(item_id)

    def save(self) -> None:
        try:
            self.__mv_cache.save()
        except Exception as e:
            logger.error(f"TSM pricing cache could not be saved to {self.__mv_cache.file_path}: {e}")


class _VendorPriceDB(Resource[int, int]):
    _RESOURCE: Path = Path("data/items/vendor_prices")
    _DEFAULT_FILE_EXT: str = "json"

    def __init__(self) -> None:
        super().__init__(self._RESOURCE.stem, self._RESOURCE.parent)

    def load(self) -> None:
        """Loads the vendor prices from the storage medium"""
        data: list[JsonValue] = load_json(self.file_path, list, True)
        jso: JSW = wrap_json(data)



        self._data = load_json(self.file_path, dict, True)


class _UnpriceableHandler:
    def __init__(self, item_db: ItemDB) -> None:
        self.__unpriceable: set[int] = set()
        self.__item_db: ItemDB = item_db

    def fallback_price(self, item_id: int) -> int:
        """Retrieve prices for items in which the item_db cannot handle"""
        entry: Optional[ItemEntry] = self.__item_db.get(item_id)
        if entry is None:
            raise ValueError(f"item ID is unknown and has no pricing data: {item_id}")
        if not item_id in self.__unpriceable:
            logger.warning(f"item '{entry.item_name}' has no pricing data, ID: {item_id}")
            self.__unpriceable.add(item_id)
        return 0  # fallback pricing
