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

from argparse import Namespace as ArgNamespace
from functools import cached_property
from typing import Optional
from logging import getLogger, Logger
from atexit import register as on_exit

from wow_recipe_calc.client.item_client import ItemClient
from wow_recipe_calc.client.tsm_client import TSMClient
from wow_recipe_calc.io.resources.project import Saveable
from wow_recipe_calc.io.resources.environment import Environment
from wow_recipe_calc.crafts.craft_planner import CraftPlanner, CraftPlan
from wow_recipe_calc.crafts.item_db import ItemDB, ItemEntry
from wow_recipe_calc.crafts.price_manager import PriceManager
from wow_recipe_calc.crafts.recipe.recipe import Recipe
from wow_recipe_calc.io.setup_config import SetupConfig
from wow_recipe_calc.util.throttle import Throttle
from wow_recipe_calc.util.json_wrapper import JSO

logger: Logger = getLogger(__name__)


class CraftingApp:
    _DEFAULT_ENV_STEM: str = "setup"
    _DEFAULT_THROTTLE: Throttle = (Throttle.Builder()
       .add(1, 5).add(15, 60).build())

    def __init__(self, throttle: Optional[Throttle] = None) -> None:
        """
        Crafting app houses all backend components

        If throttle is unspecified: defaults to 1 request per 5 seconds & 15 requests per minute

        :param throttle: (Optional) Throttle for web requests
        """
        self.__throttle: Throttle = throttle or self._DEFAULT_THROTTLE
        # Web clients for data requests
        self.__item_client: ItemClient = ItemClient(self.__throttle)
        self.__tsm_client: TSMClient = TSMClient()
        # Databases/containers/optimizers
        self.__item_db: ItemDB = ItemDB(self.__item_client)
        handler: _UnpriceableHandler = _UnpriceableHandler(self.__item_db)
        self.__prices: PriceManager = PriceManager(self.__tsm_client, handler.fallback_price)


        self.__tsm_client.auction_house = wrap_json(self.environment.data).auction_house



        to_save: list[Saveable] = [ self.environment, self.__item_db, self.__tsm_client ]
        for database in to_save: on_exit(database.save)


    def populate_recipes(self) -> ItemDB:
        """
        Populate the item database with profession recipe data

        :return: Completed item DB
        """
        logger.debug("populating recipe data")
        prof_data: JSO = wrap_json(self.__args.profession_data_path)
        for recipe_data in prof_data:
            recipe: Recipe = Recipe(
                recipe_data.name,
                next(iter(recipe_data.levels)),
                list(recipe_data.levels)[1:],
                { int(k): v for k, v in recipe_data.reagents },
                int(recipe_data.product),
                recipe_data.produces)
            self.__item_db.register(recipe)
        return self.__item_db

    def run_planner(self, desired_crafts: Mapping[str | int | Recipe, int]) -> CraftPlan:
        """
        :return: craft plan detailing the optimal crafting routes/windows/materials
        """
        logger.debug("running craft planner")
        planner: CraftPlanner = CraftPlanner(self.item_db, self.__prices)
        for name, quantity in desired_crafts.items():
            if not planner.craft(name, quantity):
                logger.debug(f"planned recipe is unrecognized: {name}")
        return planner.plan()

    @property
    def item_db(self) -> ItemDB:
        return self.__item_db

    @cached_property
    def environment(self) -> Environment:
        env: Environment = Environment(self._DEFAULT_ENV_STEM)
        try:
            env.load()  # attempt to load from storage medium
            # If SetupConfig doesn't set the api_key, we have to here
            self.__tsm_client.authorize(env.jso().api_key)
        except FileNotFoundError, OSError, ValueError:
            logger.info("no config environment found, running setup")
            config: SetupConfig = SetupConfig(self.__tsm_client)  # run first-time setup
            self.__env.extend(config.full_setup())  # run user through questionnaire
        return env


