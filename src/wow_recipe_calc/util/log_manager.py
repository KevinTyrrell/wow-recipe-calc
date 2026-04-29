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

from __future__ import annotations
from logging import getLogger, Logger, LogRecord, Formatter, Handler
from logging.handlers import MemoryHandler
from typing import Optional, Callable, TextIO

import logging

Destination = Optional[TextIO | Callable[[str], None]]


class LogManager:
    _DEFAULT_CAPACITY: int = 1000  # limit of log records stored in RAM buffer
    _DEFAULT_LOG_LEVEL: int = logging.INFO
    _DEFAULT_FMT: str = "[%(asctime)s] (%(levelname)s) [%(name)s] %(message)s"
    _DEFAULT_TIME_FMT: str = "%I:%M:%S %p"
    _DISABLE_AUTO_FLUSH: int = 1000  # ensures all log records are cleared from buffer

    def __init__(self, log_level: Optional[int] = None,
                 msg_fmt: Optional[str] = None, time_fmt: Optional[str] = None) -> None:
        """
        :param log_level: (Optional) Minimum logging level in-which to broadcast
        :param msg_fmt: (Optional) Logging-style message format for record messages
        :param time_fmt: (Optional) Logging-style time format for record timestamps
        """
        self.__level: int = log_level or self._DEFAULT_LOG_LEVEL
        self.__formatter: Formatter = Formatter(
            msg_fmt or self._DEFAULT_FMT, datefmt = time_fmt or self._DEFAULT_TIME_FMT)
        self.__root: Logger = getLogger()
        self.__mem_handler: MemoryHandler = MemoryHandler(
            capacity = self._DEFAULT_CAPACITY, flushLevel = self._DISABLE_AUTO_FLUSH)
        self.__console_handler: Handler = self._ConsoleEmitter(self.__formatter)
        self.__handler: Handler = self.__mem_handler
        self.__hook_emitter: Callable[[Handler], None] = self.__shutdown_log_buffer
        self.__root.setLevel(self.__level)
        self.__root.addHandler(self.__mem_handler)

    @property
    def level(self) -> int: return self.__level

    @level.setter
    def level(self, value: int) -> None:
        self.__level = value
        self.__root.setLevel(value)

    def broadcast(self, destination: Destination = None) -> None:
        """
        Broadcasts past and future logging records to a specified destination

        Future log records will be channeled to the destination.
        If the manager was previously buffering log records,
        all buffered log records are expelled to the destination

        The destination determines where the log records are sent:
        * no-arg: stdout console message
        * TextIO: file is written to continuously
        * Callable: external callback to consume log records

        :param destination: Destination where to broadcast log records
        """
        handler: Handler = self._map_to_handler(destination)
        self.__hook_emitter(handler)

    def _map_to_handler(self, destination: Destination) -> Handler:
        if destination is None: return self.__console_handler
        if callable(destination): return LogManager._CallbackEmitter(self.__formatter, destination)
        return LogManager._IOEmitter(self.__formatter, destination)

    def __switch_handler(self, handler: Handler) -> None:
        self.__root.removeHandler(self.__handler)
        self.__root.addHandler(handler)
        self.__handler = handler

    def __shutdown_log_buffer(self, handler: Handler) -> None:
        self.__switch_handler(handler)
        for record in self.__mem_handler.buffer:
            if record.levelno >= self.__level:
                handler.emit(record)
        self.__mem_handler.close()
        self.__hook_emitter = self.__switch_handler  # strategy pattern

    class _ConsoleEmitter(Handler):
        def __init__(self, formatter: Formatter) -> None:
            super().__init__()
            self.setFormatter(formatter)
        def emit(self, record: LogRecord) -> None:
            print(self.format(record))

    class _IOEmitter(Handler):
        def __init__(self, formatter: Formatter, file: TextIO) -> None:
            super().__init__()
            self.setFormatter(formatter)
            self.__file: TextIO = file
        def emit(self, record: LogRecord) -> None:
            self.__file.write(f"{self.format(record)}\n")
            self.__file.flush()  # clear RAM and immediately write to file in case of crash

    class _CallbackEmitter(Handler):
        def __init__(self, formatter: Formatter, cb: Callable[[str], None]) -> None:
            super().__init__()
            self.setFormatter(formatter)
            self.__cb: Callable[[str], None] = cb
        def emit(self, record: LogRecord) -> None:
            self.__cb(self.format(record))  # defer to callback
