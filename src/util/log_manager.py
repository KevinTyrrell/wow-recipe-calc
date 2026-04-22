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

import logging

from logging.handlers import MemoryHandler
from logging import getLogger, Logger, LogRecord


class LogManager:
    DEFAULT_MEM_CAPACITY: int = 1000
    DEFAULT_FLUSH_LEVEL: int = 100  # 100 is higher than CRITICAL, to avoid flush
    DEFAULT_LOG_FMT: str = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"

    def __init__(self, log_level: int = logging.INFO):
        logging.basicConfig(level = log_level, format = self.DEFAULT_LOG_FMT)
        self.__logger: Logger = getLogger()
        self.__mem_handler: MemoryHandler = MemoryHandler(
            capacity = self.DEFAULT_MEM_CAPACITY,
            flushLevel = self.DEFAULT_FLUSH_LEVEL)
        self.__logger.addHandler(self.__mem_handler)

    @property
    def history(self) -> list[LogRecord]:
        """
        :return: History of all log messages recorded, up to a capacity
        """
        return self.__mem_handler.buffer

    def stop_buffering(self) -> None:
        """
        Disables buffering of logged messages. Freeing RAM after use period.
        """
        self.__logger.removeHandler(self.__mem_handler)
        self.__mem_handler.close()
