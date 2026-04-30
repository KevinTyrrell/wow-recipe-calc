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
from typing import TypeVar, Generic, Optional, Iterator, Iterable, Callable, Any, MutableSequence
from dataclasses import dataclass
from heapq import heapify, heappush, heappop, heappushpop, heapreplace
from heapq import heapify_max, heappush_max, heappop_max, heappushpop_max, heapreplace_max

_T = TypeVar("_T")


@dataclass(frozen=True)
class _HeapType(Generic[_T]):
    heapify: Callable[[MutableSequence[_T]], None]
    push: Callable[[MutableSequence[_T], _T], None]
    pop: Callable[[MutableSequence[_T]], _T]
    push_pop: Callable[[MutableSequence[_T], _T], _T]
    replace: Callable[[MutableSequence[_T], _T], _T]

_min_heap: _HeapType = _HeapType(heapify, heappush, heappop, heappushpop, heapreplace)
_max_heap: _HeapType = _HeapType(
    heapify_max, heappush_max, heappop_max,
    heappushpop_max, heapreplace_max)

def _cmp_any(a: _T, b: _T) -> int:
    if a < b: return -1
    if a > b: return 1
    return 0


class _HeapItem(Generic[_T]):
    def __init__(self, value: _T, cmp: Callable[[_T, _T], int]) -> None:
        self.value: _T = value
        self.__cmp: Callable[[_T, _T], int] = cmp
        
    def __lt__(self, other: Any) -> bool: 
        if not isinstance(other, _HeapItem): return NotImplemented
        return self.__cmp(self.value, other.value) < 0


class Heap(Generic[_T]):
    def __init__(self, min_heap: bool, elements: Optional[Iterable[_T]]=None,
                cmp: Optional[Callable[[_T, _T], int]]=None) -> None:
        """
        Custom Comparator Signature
            - param [_T] a: Object being compared
            - param [_T] b: Object being compared-to
            - return [int]: Zero if equal, negative num if LT, positive num if GT
        
        :param min_heap: Operates the heap as a min heap if-true, else max heap
        :param elements: (Optional) Initial elements of the heap
        :param cmp: (Optional) Custom comparator, see above
        """
        self.__funcs: _HeapType = _min_heap if min_heap else _max_heap
        self.__cmp: Callable[[_T, _T], int] = cmp or _cmp_any
        if elements is not None:
            heap: list[_HeapItem[_T]] = list(_HeapItem(e, self.__cmp) for e in elements)
            self.__funcs.heapify(heap)
            self.__heap: list[_HeapItem[_T]] = heap
        else: self.__heap: list[_HeapItem[_T]] = list()

    def peek(self) -> Optional[_T]:
        """
        :return: Min/max element in the heap, or None if empty
        """
        return self.__heap[0].value if self.__heap else None

    def push(self, value: _T) -> None:
        """
        :param value: Value to be pushed onto the heap
        """
        self.__funcs.push(self.__heap, _HeapItem(value, self.__cmp))

    def pop(self) -> _T:
        """
        Removes & returns the min/max element in the heap
        """
        if not self.__heap:
            raise IndexError(f"empty heap cannot pop an element")
        return self.__funcs.pop(self.__heap).value
        
    def clear(self) -> None:
        """
        Removes all elements from the heap
        """
        self.__heap.clear()
        
    def __len__(self) -> int: return len(self.__heap)
    def __iter__(self) -> Iterator[_T]:
        return (e.value for e in sorted(self.__heap))
    def __str__(self) -> str: return str(list(self))
    def __bool__(self) -> bool: return bool(self.__heap)
