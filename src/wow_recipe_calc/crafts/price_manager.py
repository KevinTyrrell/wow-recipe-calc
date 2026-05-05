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
from typing import Optional, Callable
from logging import getLogger, Logger

from wow_recipe_calc.io.resources.project import Saveable, Resource
from wow_recipe_calc.io.resources.json_store import JsonStore
from wow_recipe_calc.util.json_wrapper import JSO, wrap_json
from wow_recipe_calc.client.tsm_client import TSMClient
from wow_recipe_calc.io.resources.ttl_cache import TTLCache, CachePolicy

logger: Logger = getLogger(__name__)


class PriceManager(Saveable):
    _RESOURCE_MARKET_STEM: str = "market_value_db"
    _MARKET_STALE_THRESH: int = 3 * 60 * 60  # 3 hours before pricing data becomes stale
    
    def __init__(self, tsm_client: TSMClient) -> None:
        """
        :param tsm_client: TSM request instance for market value pricing
        """
        policy: CachePolicy = CachePolicy(self._MARKET_STALE_THRESH, tsm_client.scan_ah_market_value)
        self.__mv_cache: TTLCache = TTLCache(self._RESOURCE_MARKET_STEM, policy)  # continuously tosses stale data
        self.__vendor: dict[int, int] = dict()  # [item_id, copper cost from vendor]
        self.__tsm_client = tsm_client

    def get_price(self, item_id: int) -> int:
        """
        Retrieves the price of an item, if possible
        
        If no price is found, the method-level or object-level callback
        is used for pricing instead, after being provided the item id.
        
        :param item_id: Item ID to query price
        :param no_price_cb: (Optional) Callback if no price can be found for the item
        """
        for source in (self.__vendor.get, self.__tsm_client.market_value):
            price: Optional[int] = source(item_id)
            if price is not None: return price
        if no_price_cb is not None:
            return no_price_cb(item_id)
        return self.__no_price_cb(item_id)

    def market_value(self, item_id: int) -> Optional[int]:
        """
        :param item_id: Item ID to retrieve pricing information
        :return: Market value of the item, in copper, if present
        """
        return self.__mv_cache.get(item_id)

    def save(self) -> None:
        pass






    def _load_vendor_prices(self) -> JSO:
        try:
            with path.open("r", encoding = self._FILE_ENCODING) as f:
                return wrap_json(json.load(f))
        except FileNotFoundError as e:
            logger.error(f"no vendor prices at path, recipe costs will be inaccurate: {self._RESOURCE_VENDOR}")
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            raise RuntimeError(f"failed to load json: {path.absolute()}") from e


class _VendorPriceDB(Resource[int, int]):
    _RESOURCE: Path = Path("data/items/vendor_prices")
    _FILE_ENCODING: str = "utf-8"

    def __init__(self) -> None:
        super().__init__(self._RESOURCE.stem, self._RESOURCE.parent)

    def load(self) -> None:



        with self.file_path.open("r", encoding = self._FILE_ENCODING) as f:
            data: dict[str, JsonValue] = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"expected a JSON object, got {type(data).__name__}, path: {self.file_path}")
        self._data = data





class _UnpriceableHandler:
    def __init__(self, item_db: ItemDB) -> None:
        self.__unpriceable: set[int] = set()
        self.__item_db: ItemDB = item_db

    def fallback_price(self, item_id: int) -> int:
        """Retrieve prices for items in which the item_db cannot handle"""
        entry: Optional[ItemEntry] = self.__item_db.get(item_id)
        if entry is None:
            raise ValueError(f"item ID is unknown: {item_id}")
        if not item_id in self.__unpriceable:
            logger.warning(f"item '{entry.item_name}' has no pricing data, ID: {item_id}")
            self.__unpriceable.add(item_id)
        return 0  # fallback pricing