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

from __future__ import annotations 
from typing import TypeVar, Generic, Hashable
from collections import deque
from collections.abc import Mapping
from types import MappingProxyType as ReadOnlyMap

_T = TypeVar("_T", bound=Hashable)


class _Node[Generic[_T]]:
    def __init__(self, payload: _T) -> None:
        """
        :param payload: Data coupled with the node
        """
        self.__payload: _T = payload
        self.__requires: set[_Node[_T]] = set()
        self.__dependents: set[_Node[_T]] = set()
    
    def requires(self, node: _Node) -> None:
        """
        :param node: associates A as a requirement of B (A<-B)
        """
        # Sentinel value allows O(1) read-only via keys()
        self.__requires[node] = _SENTINEL_VALUE
        node.__dependents[self] = _SENTINEL_VALUE
    
    @property
    def payload(self) -> Any: return self.__payload
    @property
    def requirements(self) -> Mapping[_Node, bool]:
        return self.__requires_ro
    @property
    def dependents(self) -> Mapping[_Node, bool]:
        return self.__dependents_ro


class Graph:
    def __init__(self) -> None:
        self.__data_map: dict[JJJJJJJJJJJJJJJJJ
        self.__nodes: dict[_Node, bool] = dict()
        self.__nodes_ro: Mapping[_Node, bool] = ReadOnlyMap(self.__nodes)
    
    def topological_sort(self) -> list[_Node]:
        """
        Topological sort using Kahn's algorithm
        
        :return: List of nodes, sorted in topological order
        """
        topo_sorted: list[_Node] = list()
        degrees: dict[_Node, int] = { node: 0 for node in self.__nodes }
        for node in self.__nodes:
            for edge in node.dependents:
                degrees[edge] += 1
        queue: deque[_Node] = deque(k for k, v in degrees.items() if v <= 0)
        while len(queue) > 0:
            leaf: _Node = queue.popleft()
            topo_sorted.append(leaf)
            for node in leaf.dependents:
                degree: int = degrees[node]
                if degree <= 1: queue.append(node)
                else: degrees[node] = degree - 1
        if len(topo_sorted) < len(self.__nodes):
            raise RuntimeError("topological sort cannot continue as graph contains cycles")
        return topo_sorted

    def add(self, node: _Node) -> None:
        self.__nodes[node] = _SENTINEL_VALUE
    def remove(self, node: _Node) -> None:
        del self.__nodes[node]
    @property
    def nodes(self) -> Mapping[_Node, bool]:
        return self.__nodes_ro
