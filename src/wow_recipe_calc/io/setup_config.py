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

from questionary import Style, Choice, select, password

from wow_recipe_calc.util.json_wrapper import JSO
from wow_recipe_calc.client.tsm_client import TSMClient


class SetupConfig:
    _DEFAULT_EXTENSION: str = ".env"
    _DEFAULT_SELECT_STYLE: Style = Style([
        ("qmark", "fg:#ff9d00 bold"),
        ("question", "bold"),
        ("answer", "fg:#00ff9c bold"),
        ("pointer", "fg:#ff9d00 bold"),
        ("highlighted", "fg:#00ff9c bold"),
        ("selected", "fg:#00ff9c"),
    ])
    
    _WOW_EXPANSIONS: list[tuple[str, str]] = [
        ("World of Warcraft", "classic"),
        ("The Burning Crusade", "tbc"),
        ("Wrath of the Lich King", "wotlk"),
        ("Cataclysm", "cata"),
        ("Mists of Pandaria", "mop"),
        ("Warlords of Draenor", "wow/retail"),
        ("Legion", "wow/retail"),
        ("Battle for Azeroth", "wow/retail"),
        ("Shadowlands", "wow/retail"),
        ("Dragonflight", "wow/retail"),
        ("The War Within", "wow/retail"),
        ("Midnight", "wow/retail"),
        ("The Last Titan", "wow/retail"),
    ]
    
    _WOW_PROFESSIONS: dict[str, str] = {
        "Alchemy": "professions/alchemy",
        "Blacksmithing": "professions/blacksmithing",
        "Cooking": "secondary-skills/cooking",
        "Enchanting": "professions/enchanting",
        "Engineering": "professions/engineering",
        "Leatherworking": "professions/leatherworking",
        "Tailoring": "professions/tailoring",
        "Jewelcrafting": "professions/jewelcrafting",
        "Inscription": "professions/inscription",
    }
    
    def __init__(self, tsm: TSMClient) -> None:
        self.__tsm: TSMClient = tsm
        
    def full_setup(self) -> dict[str, str | int]:
        """
        Completes a full setup, querying the user about the following:
        Region, Realm, Faction, Expansion, Profession
        """
        api_key: str = self.enter_tsm_api_key()
        self.__tsm.authorize(api_key)  # JIT for following calls
        region: int = self.choose_region_id()
        realm_info: tuple[int, object] = self.choose_realm_id(region)
        auction_house: int = self.choose_ah_id(realm_info[1])
        expac_info: tuple[str, int] = self.choose_expansion()
        prof: str = self.choose_profession(expac_info[1])
        return {
            "api_key": api_key,
            "region": region,
            "realm": realm_info[0],
            "auction_house": auction_house,
            "expansion": expac_info[0],
            "profession": prof
        }

    def enter_tsm_api_key(self) -> str:
        return password("Please enter your TSM API Key:",
            instruction=(
                "\nPaste in your copied key by pressing the SHIFT and INSERT keys.\n"
                
                "\nYour TSM API Key can be found by visiting the following URL:\n"
                "(You can copy this URL by sweeping and pressing the SHIFT and CTRL and C keys)\n\n"
                
                "https://id.tradeskillmaster.com/realms/app/account"
                
                "\n\nYou may be prompted to sign in or create a TSM account.\n"
                "Navigate to 'Account' --> 'Personal Info' --> 'Legacy API Key'\n"
                "Your TSM API Key will look like: a3f9c7d2-b6e1-9c2a-f7d1-3b8e4a91c6d2\n"
                "This key, along with your other responses, will be stored & loaded locally.\n"

                "\nThe TSM API Key is required to retrieve auction houses pricing data.\n"
                "Due to daily API request limits, we must request the entire auction\n"
                "house's pricing data all at once. This may lead to long start-up times.\n"
                "This pricing data is considered stale after three hours, and will be\n"
                "requested again, on next run, after that threshold of time is exceeded.\n"
                
                "\nEnter TSM API Key: "
            )).ask()

    def choose_region_id(self) -> int:
        """
        :return: World of Warcraft Region ID corresponding to user's choice
        """
        regions = sorted(self.__tsm.regions(), key = lambda t: (t[0], t[1]))
        choices: list[Choice] = [
            Choice(f"{version} ({name})", value = region_id)
            for version, name, region_id in regions ]
        return select("Select World of Warcraft game region",
            choices = choices, style = self._DEFAULT_SELECT_STYLE).ask()
    
    def choose_realm_id(self, region: int) -> tuple[int, object]:
        """
        :param region: World of Warcraft Region ID
        :return World of Warcraft Server ID corresponding to user's choice
        :return Auction house information of the aforementioned server
        """
        realms = sorted(self.__tsm.realms(region), key = lambda x: x[0])
        choices: list[Choice] = [
            Choice(name, value = (realm_id, auction_houses))
            for name, realm_id, auction_houses in realms ]
        return select("Select World of Warcraft game realm",
            choices = choices, style = self._DEFAULT_SELECT_STYLE).ask()
    
    def choose_ah_id(self, auction_houses: JSO) -> int:
        """
        :param auction_houses: JSON array of auction house information
        :return: Auction house ID
        """
        choices: list[Choice] = [
            Choice(o.type, value = o.auctionHouseId) for o in auction_houses ]
        return select("Select World of Warcraft realm auction house",
            choices = choices, style = self._DEFAULT_SELECT_STYLE).ask()
    
    def choose_expansion(self) -> tuple[str, int]:
        """
        :return: Portal url prefix associated with the specified expansion
        :return: Expansion number associated with the specified expansion
        """
        choices: list[Choice] = [ Choice(self._WOW_EXPANSIONS[i][0],
            value = i) for i in range(len(self._WOW_EXPANSIONS)) ]
        choice: int = select("Select World of Warcraft expansion",
            choices = choices, style = self._DEFAULT_SELECT_STYLE).ask()
        return self._WOW_EXPANSIONS[choice][1], choice + 1
    
    def choose_profession(self, expansion: int) -> str:
        """
        :param expansion: Expansion ID
        :return: Profession segment associated with the specified profession
        """
        prof_data: dict[str, str] = self._WOW_PROFESSIONS.copy()
        if expansion < 3:
            del prof_data["Inscription"]
            if expansion < 2: del prof_data["Jewelcrafting"]
        professions = sorted(prof_data.items(), key = lambda t: (t[1], t[0]))
        choices: list[Choice] = [
            Choice(name, value = segment) for name, segment in professions ]
        return select("Select World of Warcraft profession",
            choices = choices, style = self._DEFAULT_SELECT_STYLE).ask()
