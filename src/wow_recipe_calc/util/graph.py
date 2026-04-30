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
from typing import TypeVar, Generic, Hashable, Optional, Callable, Iterator, Protocol, Iterable
from collections import deque
from collections.abc import Mapping, KeysView

_T = TypeVar("_T", bound=Hashable)


class _Node(Generic[_T]):
    def __init__(self, payload: _T) -> None:
        """
        :param payload: Data coupled with the node
        """
        self.payload: _T = payload
        self.requirements: set[_Node[_T]] = set()
        self.dependents: set[_Node[_T]] = set()
    
    def requires(self, node: _Node[_T]) -> None:
        """
        :param node: associates A as a requirement of B (A<-B)
        """
        self.requirements.add(node)
        node.dependents.add(self)


class Frontier(Protocol[_T]):
    def push(self, element: _T) -> None:
        """
        :param element: Element to be pushed to the frontier
        """
        pass
        
    def pop(self) -> _T:
        """
        :return: Element popped from the frontier
        """
        pass
        
    def __bool__(self) -> bool:
        """
        :return: True if the frontier is not empty
        """
        pass


class FIFOFrontier(Frontier[_T]):
    def __init__(self, elements: Iterable[_T]) -> None:
        self.__queue: deque[_T] = deque(elements)
    def push(self, element: _T) -> None:
        self.__queue.append(element)
    def pop(self) -> _T:
        return self.__queue.popleft()
    def __bool__(self) -> bool:
        return bool(self.__queue)


class Graph(Generic[_T]):
    def __init__(self, nodes: Optional[set[_T]] = None,
                edges: Optional[Mapping[_T, _T]] = None,
                frontier_factory: Optional[Callable[[Iterable[_T]], Frontier[_T]]] = None) -> None:
        """
        Constructs a graph instance
        
        For any edge(a, b) in which either a or b doesn't exist,
        a or b is then created and said edge is assigned as normal.
        
        Frontier objects, used for topological sort, must take in elements,
        and feed back those which are next to be topologically processed.
        By default, uses a FIFO double-sided queue (deque) data structure.
        
        :param nodes: (Optional) Initial set of leaf nodes
        :param edges: (Optional) Matrix of edges connections
        :param frontier_factory: (Optional) Frontier factory for topological sort
        """
        self.__nodes: dict[_T, _Node[_T]] = dict()
        self.__frontier_factory: Callable[[Iterable[_T]], Frontier[_T]] = frontier_factory or (lambda n: FIFOFrontier(n))
        self.__topo: Optional[Graph._TopoView] = None
        self.__topo_strategy: Callable[[], Graph._TopoView[_T]] = self._build_topo
        if nodes is not None:
            for key in nodes: self.__nodes[key] = _Node(key)
        if edges is not None:
            for a, b in edges.items(): self.requires(a, b)
    
    def add(self, node: _T) -> None:
        """
        Adds an orphan node to the graph
        """
        if node not in self.__nodes:
            self.__nodes[node] = _Node(node)
            self._invalidate()
    
    def remove(self, node: _T) -> bool:
        """
        :return: True if the node existed and was removed from the graph
        """
        removed: Optional[_Node[_T]] = self.__nodes.pop(node, None)
        if removed is not None:
            self._invalidate()
            return True
        return False
        
    def requires(self, dependent: _T, requirement: _T) -> None:
        a: _Node[_T] = self._retrieve(dependent)
        b: _Node[_T] = self._retrieve(requirement)
        a.requires(b)
        self._invalidate()
    
    def topological_sort(self, frontier_factory: Optional[Callable[[Iterable[_T]], Frontier[_T]]] = None) -> list[_T]:
        """
        Topologically sorts the nodes using Kahn's algorithm
        
        A runtime error will be raised if cycles are detected in the graph.
        Topological sorts are automatically cached while using the 'topo' property.
        Override this method to swap the topological sort used for caching.
        If no factory is provided, the frontier factory given during construction
        will be used instead to generate the container for next-node selection.
        
        :param frontier_factory: (Optional) Override for the object's frontier factory
        :return: Topologically sorted list of elements (leaves first)
        """
        factory: Callable[[Iterable[_T]], Frontier[_T]] = frontier_factory or self.__frontier_factory
        topo_sorted: list[_T] = list()
        degrees: dict[_T, int] = { element: 0 for element in self.__nodes }
        for node in self.__nodes.values():
            for edge in node.dependents:
                degrees[edge.payload] += 1
        frontier: Frontier[_T] = factory(k for k, v in degrees.items() if v <= 0)
        while frontier:  # At least one element 
            leaf: _T = frontier.pop()
            topo_sorted.append(leaf)
            requirement: _Node[_T] = self.__nodes[leaf]
            for node in requirement.dependents:
                element: _T = node.payload
                degree: int = degrees[element]
                if degree <= 1: frontier.push(element)
                else: degrees[element] = degree - 1  # Kahn's
        cycle: int = len(self.__nodes) - len(topo_sorted)
        if cycle > 0:
            raise RuntimeError(f"topological cycle(s) detected in the graph, cycle(s) size: {cycle}")
        return topo_sorted
    
    @property
    def nodes(self) -> KeysView[_T]:
        """
        :return: Set of all elements the graph
        """
        return self.__nodes.keys()
        
    def _retrieve(self, key: _T) -> _Node[_T]:
        node: Optional[_Node[_T]] = self.__nodes.get(key)
        if node is None:
            node: _Node[_T] = _Node(key)
            self.__nodes[key] = node
            self._invalidate()
        return node
    
    def _invalidate(self) -> None:
        self.__topo = None  # Garbage collect
        self.__topo_strategy = self._build_topo  # Validate
        
    def __iter__(self) -> Iterator[_T]:
        return iter(self.__nodes)

    class _TopoView(Generic[_T]):
        def __init__(self, graph: Graph[_T]):
            self.__graph: Graph[_T] = graph
            self.__order: list[_T] = graph.topological_sort()
            self.__indexes: dict[_T, int] = { e: i for i, e in enumerate(self.__order) }

        def index(self, element: _T) -> int:
            """
            :param element: Element to retrieve topological index
            """
            return self.__indexes[element]

        def cmp(self, a: _T, b: _T) -> int:
            """
            :param a: Element to be topologically compared by
            :param b: Element to be topologically compared to
            :return: -1 if a < b, 1 if a > b, 0 if a == b
            """
            i_a: int = self.__indexes[a]
            i_b: int = self.__indexes[b]
            return (i_a > i_b) - (i_a < i_b)

        def __iter__(self) -> Iterator[_T]:
            return iter(self.__order)

    @property
    def topo(self) -> Graph._TopoView[_T]:
        """
        :return: Cached topologically-sorted view of the graph
        """
        return self.__topo_strategy()

    def _get_topo(self) -> Graph._TopoView[_T]:
        if self.__topo is None:
            raise RuntimeError("topological order has not yet been cached")
        return self.__topo

    def _build_topo(self) -> Graph._TopoView[_T]:
        self.__topo = Graph._TopoView(self)
        self.__topo_strategy = self._get_topo  # Validate
        return self.__topo
