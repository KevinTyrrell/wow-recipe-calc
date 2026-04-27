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

import json

from pathlib import Path
from typing import Optional, Callable

from wow_recipe_calc.util.json_wrapper import JSO, wrap_json
from wow_recipe_calc.client.tsm_client import TSMClient


class PriceManager:
    _PRICE_JSON_RELATIVE_PATH: str = "data/VendorPrices.json"
    
    def __init__(self, tsm: TSMClient, no_price_cb: Optional[Callable[[int], int]] = None) -> None:
        """
        :param tsm: TSM request instance for market value pricing
        :param no_price_cb: (Optional) Callback for pricing unknown items (default: 0)
        """
        self.__no_price_cb: Callable[[int], int] = no_price_cb or (lambda _: 0)
        self.__tsm = tsm
        self.__vendor: dict[int, int] = {
            e.id: e.cost for e in self._load_vendor_prices() }
    
    def get_price(self, item_id: int, no_price_cb: Optional[Callable[[int], int]] = None) -> int:
        """
        Retrieves the price of an item, if possible
        
        If no price is found, the method-level or object-level callback
        is used for pricing instead, after being provided the item id.
        
        :param item_id: Item ID to query price
        :param no_price_cb: (Optional) Callback if no price can be found for the item
        """
        for source in (self.__vendor.get, self.__tsm.get_price):
            price: Optional[int] = source(item_id)
            if price is not None: return price
        if no_price_cb is not None:
            return no_price_cb(item_id)
        return self.__no_price_cb(item_id)
    
    def _load_vendor_prices(self) -> JSO:
        path = Path(self._PRICE_JSON_RELATIVE_PATH)
        try:
            with path.open("r", encoding="utf-8") as f:
                return wrap_json(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            raise RuntimeError(f"failed to load json: {path.absolute()}") from e
