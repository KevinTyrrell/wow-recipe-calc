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

from __future__ import annotations
from logging import getLogger, Logger, LogRecord, Formatter, Handler
from typing import Optional, Callable, TextIO, TypeAlias
from collections import deque

import logging

Destination: TypeAlias = Optional[TextIO | Callable[[str], None]]


class LogManager:
    _DEFAULT_CAPACITY: int = 1000
    _DEFAULT_LOG_LEVEL: int = logging.INFO
    _DEFAULT_FMT: str = "[%(asctime)s] (%(levelname)s) [%(name)s] %(message)s"
    _DEFAULT_TIME_FMT: str = "%I:%M:%S %p"

    def __init__(self, log_level: Optional[int] = None,
                 msg_fmt: Optional[str] = None, time_fmt: Optional[str] = None) -> None:
        self.__level: int = log_level or self._DEFAULT_LOG_LEVEL
        self.__formatter: Formatter = Formatter(
            msg_fmt or self._DEFAULT_FMT, datefmt = time_fmt or self._DEFAULT_TIME_FMT)
        self.__root: Logger = getLogger()
        self.__buffer: deque[LogRecord] = deque(maxlen = self._DEFAULT_CAPACITY)
        self.__listeners: list[Handler] = list()
        self.__root.setLevel(self.__level)

        # Console is always live — no buffering needed
        console = self._ConsoleEmitter(self.__formatter)
        self.__root.addHandler(console)
        self.__listeners.append(console)

    @property
    def level(self) -> int: return self.__level

    @level.setter
    def level(self, value: int) -> None:
        self.__level = value
        self.__root.setLevel(value)

    def broadcast(self, destination: Destination) -> None:
        """
        Registers a new listener and immediately replays all buffered records to it.

        * TextIO        : live file writer, replays buffer then writes future records immediately
        * Callable      : replays buffer into callback, then forwards future records live
        """
        if callable(destination):
            handler: Handler = LogManager._CallbackEmitter(self.__formatter, destination)
        else: handler: Handler = LogManager._IOEmitter(self.__formatter, destination)
        for record in self.__buffer:  # Replay buffered logs into the new handler
            if record.levelno >= self.__level:
                handler.emit(record)
        self.__root.addHandler(handler)
        self.__listeners.append(handler)

    def _buffer_record(self, record: LogRecord) -> None:
        """Called by the internal buffering handler to store records"""
        self.__buffer.append(record)

    class _BufferingTap(Handler):
        """Silent handler whose only job is to feed records into LogManager's buffer"""
        def __init__(self, manager: LogManager) -> None:
            super().__init__()
            self.__manager = manager
        def emit(self, record: LogRecord) -> None:
            self.__manager._buffer_record(record)

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
            self.__file.flush()

    class _CallbackEmitter(Handler):
        def __init__(self, formatter: Formatter, cb: Callable[[str], None]) -> None:
            super().__init__()
            self.setFormatter(formatter)
            self.__cb: Callable[[str], None] = cb
        def emit(self, record: LogRecord) -> None:
            self.__cb(self.format(record))
