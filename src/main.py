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

from atexit import register as on_exit

from src.io.arguments import parse_args
from src.io.setup_config import SetupConfig
from src.io.environment import Environment
from src.crafts.recipe import Recipe
from src.crafts.item_db import *
from src.crafts.price_manager import PriceManager
from src.crafts.craft_planner import *
from src.client.item_client import ItemClient
from src.client.tsm_client import TSMClient
from src.util.json_wrapper import *
from src.util.throttle import Throttle
from src.util.heap import Heap
from src.util.color import Color


def main():
    args = parse_args()
    prof = wrap_json(args.profession_data_path)
    recipes = [
        Recipe(
            e.name,
            next(iter(e.levels)),
            list(e.levels)[1:],
            { int(k): v for k, v in e.reagents },
            int(e.product),
            e.produces)
        for e in prof
    ]
    
    throttle: Throttle = Throttle.Builder().add(1, 5).add(15, 60).build()
    item_client: ItemClient = ItemClient(throttle)
    
    item_db: ItemDB = ItemDB(item_client.get_item_name, "item_db")
    on_exit(item_db.save)
    for recipe in recipes:
        item_db.register(recipe)
    
    
    tsm_client: TSMClient = TSMClient(args.api_key)
    on_exit(tsm_client.save)
    
    def load_config() -> JSO:
        env: Environment = Environment("setup")
        try:
            settings = env.load()
            return wrap_json(settings)
        except RuntimeError: pass
        config: SetupConfig = SetupConfig(tsm_client)
        settings = config.full_setup()
        on_exit(env.save)
        return wrap_json(settings)
    
    settings: JSO = load_config()
    tsm_client.auction_house = settings.auction_house
    
    def price_callback(item_id: int) -> int:
        print(f"price for item id is unknown: {item_id}"); return 0
    prices: PriceManager = PriceManager(tsm_client, price_callback)
    
    planner: CraftPlanner = CraftPlanner(item_db, prices)
    for name, quantity in args.required_crafts_path.items():
        if not planner.craft(name, quantity):
            print(Color.RED.ITALIC(f"recipe is unknown: {name}"))

    plan: CraftPlan = planner.plan()

    print("\nITEMS")
    for k, v in plan.craft_counts.items():
        print(item_db.by_recipe[k].item_name, v)

    print("\n\nORDER")
    for t in plan.craft_order:
        a, b, recipe, count = t
        print(f"[{a}, {b}] x{count}: {recipe.name}")
    
if __name__ == "__main__":
    main()
