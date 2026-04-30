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

from wow_recipe_calc.io.resources.project import MutableResource

EnvValue = str | int | float | bool


class Environment(MutableResource[str, EnvValue]):
    _DEFAULT_FILE_EXT: str = "env"
    _DEFAULT_ENV_DIR: str = "cache"
    _COMMENT_LINE_CHAR: str = "#"
    _PAIRING_CHAR: str = "="

    def __init__(self, file_stem: str) -> None:
        """
        :param file_stem: Name of the file, excluding file extension
        """
        super().__init__(file_stem, self._DEFAULT_ENV_DIR, self._DEFAULT_FILE_EXT)

    def save(self) -> None:
        """
        Saves the environment to the storage medium
        """
        self.file_path.write_text(  # save key as uppercase, load as lowercase
            "\n".join(f"{k.upper()}={self._data[k]}" for k in sorted(self._data)) + "\n")

    def load(self) -> None:
        """
        Attempts to load the environment from the storage medium

        Raises an error if environment file is not found, on file
        reading error(s), or if the file has malformed / invalid data.
        """
        self.clear()
        with self.file_path.open("r") as f:
            for line_no, line in enumerate(f, 1):
                line: str = line.strip()
                if not line or line.startswith(self._COMMENT_LINE_CHAR): continue  # allow for comments
                if self._PAIRING_CHAR not in line:  # line is not a key/value pair
                    raise ValueError(f"env '{self.file_name}' is malformed, line #{line_no}: {line}")
                key, raw_val = [part.strip() for part in line.split(self._PAIRING_CHAR, 1)]
                if not raw_val: continue  # ignore empty values
                self._data[key.lower()] = self._parse_value_from_str(raw_val)

    @staticmethod
    def _parse_value_from_str(value: str) -> EnvValue:
        value: str = value.strip()
        try: return int(value)  # test if integer
        except ValueError: pass
        try: return float(value)  # test if float
        except ValueError: pass
        if value.lower() in ("true", "false"):  # test if bool
            return value.lower() == "true"
        return value
