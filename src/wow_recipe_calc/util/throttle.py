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
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from typing import List, Deque
from collections import namedtuple, deque
from time import time as now, sleep
from logging import getLogger, Logger

logger: Logger = getLogger(__name__)


class Throttle:
    _Rule = namedtuple("_Rule", ["limit", "window", "ticks"])
    _constructor_access = object()  # Prevents unauthorized instantiation

    def __init__(self, rules: List[Throttle._Rule], key: object):
        if key != Throttle._constructor_access:
            raise ValueError("class cannot be instantiated directly")
        self.__rules = rules

    @staticmethod
    def __clean_ticks(rule: _Rule, ts: float) -> None:
        horizon: float = ts - rule.window
        ticks: Deque[float] = rule.ticks
        while ticks and ticks[0] < horizon:
            ticks.popleft()

    def tick(self) -> None:
        """
        Ticks the throttle, sleeping for any violated rules

        Each tick represents an action that should be throttled.
        Sleep duration will only last for the minimum amount of
        time for all throttle conditions to be satisfied.
        """
        ts: float = now()
        for rule in self.__rules:
            self.__clean_ticks(rule, ts)
            if len(rule.ticks) >= rule.limit:
                dropped: float = rule.ticks.popleft()
                delay: float = rule.window - (ts - dropped)
                logger.info(f"throttling for {delay:.1f} second(s)")
                sleep(delay)
                ts = now()  # Timestamp should be updated, since we've slept
        for rule in self.__rules:
            rule.ticks.append(ts)


    class Builder:
        def __init__(self):
            self.__throttles: List[Throttle._Rule] = []

        def add(self, limit: int, window: float) -> Throttle.Builder:
            """
            :param limit: Number of times the throttle can be ticked within the time window
            :param window: Time span, in seconds, in which the tick limit is constrained to
            :return: builder reference
            """
            if limit <= 0: raise ValueError(f"throttle rule limit must be positive: {limit}")
            if window <= 0: raise ValueError(f"throttle rule window must be positive: {window}")
            self.__throttles.append(Throttle._Rule(limit, window, deque()))
            return self

        def build(self) -> Throttle:
            s: List[Throttle._Rule] = sorted(self.__throttles, key=lambda r: r.limit / r.window)
            return Throttle(s, Throttle._constructor_access)
