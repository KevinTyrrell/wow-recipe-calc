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

from src.util.graph import Graph, Frontier
from src.util.heap import Heap


class PriorityQueue(Frontier[Recipe]):
    def __init__(self) -> None:
        self.__heap: Heap = Heap(True)
    
    def push(self, element: Recipe) -> None:
        ...
    def pop(self) -> Recipe:
        ...
    def __bool__(self) -> bool:
        ...


class RecipeGraph(Graph[Recipe]):
    def __init__(self, item_db: ItemDB, recipes: Optional[Iterable[Recipe]]=None,
                frontier_factory: Optional[Callable[[Iterable[_T]], Frontier[_T]]] = None) -> None:
        super().__init__(frontier_factory = frontier_factory)
        
        
        
        
        if recipes is not None:
            for recipe in recipes:
                self.integrate(recipe)
    
    def integrate(self, recipe: Recipe) -> None:
        vertex: Node = self._get_node(recipe.product)
        for reagent in recipe.reagents:
            edge: Node = self._get_node(reagent)
            vertex.requires(edge)
    
    def _get_node(self, item_id: int) -> Node:
        node: Optional[Node] = self.__nodes_by_id.get(item_id)
        if node is None:
            node = Node(item_id)
            self.add(node)
            self.__nodes_by_id[item_id] = node
        return node