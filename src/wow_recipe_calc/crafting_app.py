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

from functools import cached_property
from typing import Optional
from logging import getLogger, Logger
from atexit import register as on_exit
from functools import partial

from wow_recipe_calc.client.wh_client import WHClient
from wow_recipe_calc.client.tsm_client import TSMClient
from wow_recipe_calc.io.enums import Expansion, Profession
from wow_recipe_calc.io.resources.project import Saveable
from wow_recipe_calc.io.resources.environment import Environment
from wow_recipe_calc.io.setup_config import SetupConfig
from wow_recipe_calc.crafts.craft_planner import CraftPlanner, CraftPlan
from wow_recipe_calc.crafts.item_db import ItemDB
from wow_recipe_calc.crafts.recipe.recipe_book import RecipeBook
from wow_recipe_calc.crafts.price_manager import PriceManager
from wow_recipe_calc.crafts.recipe.recipe import Recipe
from wow_recipe_calc.util.throttle import Throttle
from wow_recipe_calc.util.json_wrapper import JSW

logger: Logger = getLogger(__name__)


class CraftingApp:
    _RESOURCE_ENV_NAME: str = "setup"

    _DEFAULT_THROTTLE: Throttle = (Throttle.Builder()
       .add(1, 5).add(15, 60).build())

    def __init__(self, throttle: Optional[Throttle] = None) -> None:
        """
        Crafting app houses all backend components

        If throttle is unspecified: defaults to 1 request per 5 seconds & 15 requests per minute

        :param throttle: (Optional) Throttle for web requests
        """
        self.__throttle: Throttle = throttle or self._DEFAULT_THROTTLE
        self.__tsm_client: TSMClient = TSMClient()  # item pricing
        env: JSW = self.environment.jso()  # load the environment
        expac, prof = Expansion(env.expansion), Profession(env.profession)
        self.__wh_client: WHClient = WHClient(self.__throttle, expac, prof)
        self.__book: RecipeBook = RecipeBook(expac, prof)
        self.__tsm_client.set_auction_house(env.auction_house)  # notify TSM the AH it must use
        self.__item_db: ItemDB = ItemDB(self.__wh_client)
        self.__prices: PriceManager = PriceManager(self.__tsm_client, self.__item_db)
        self.save_resources_on_exit()

    def populate_recipes(self) -> None:
        """
        Populate the item database with profession recipe data
        """
        logger.debug("populating recipe data")
        for recipe in self.__book.recipes:
            self.__item_db.register(recipe)

    def run_planner(self, desired_crafts: Mapping[str | int | Recipe, int]) -> CraftPlan:
        """
        Runs the optimizer on the crafting plan, calculating materials, routes, and pricing

        :return: craft plan detailing the optimal crafting routes/windows/materials
        """
        logger.debug("running craft planner")
        planner: CraftPlanner = CraftPlanner(self.__item_db, self.__prices)
        for name, quantity in desired_crafts.items():
            planner.craft(name, quantity)
        return planner.plan()

    @property
    def item_db(self) -> ItemDB: return self.__item_db

    @cached_property
    def environment(self) -> Environment:
        env: Environment = Environment(self._RESOURCE_ENV_NAME)
        try:
            env.load()  # attempt to load from storage medium
            # If SetupConfig doesn't set the api_key, we have to here
            self.__tsm_client.authorize(env.jso().api_key)
            return env
        except FileNotFoundError:
            logger.info("no config environment found, running setup")
        except (OSError, ValueError) as e:
            logger.error(f"config cannot be loaded, running setup: {str(e)}")
        config: SetupConfig = SetupConfig(self.__tsm_client)  # run first-time setup
        env.update(config.full_setup())  # run user through questionnaire
        return env

    @staticmethod  # helper method
    def _save_resource(resource: Saveable) -> None:
        try:
            resource.save()
        except Exception as e:
            logger.error(f"failed to save resource '{type(res).__name__}': {e}")

    def save_resources_on_exit(self) -> None:
        """Sets all resources to save at the end of runtime"""
        saveable: list[Saveable] = [self.environment, self.__item_db, self.__prices]
        for resource in saveable:
            on_exit(partial(self._save_resource, resource))
