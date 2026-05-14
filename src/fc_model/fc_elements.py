from typing import Iterator, List, Dict, Literal, Tuple, TypedDict, Union
import numpy as np
from numpy.typing import NDArray

from .fc_value import decode, encode


FCElementTypeLiteral = Literal[
    'NONE',
    'LUMPMASS3D',
    'LUMPMASS6D',
    'LUMPMASS2D',
    'POINT3D',
    'POINT2D',
    'POINT6D',
    'LUMPMASS2DR',
    'BEAM26',
    'BEAM36',
    'SPRING3D',
    'SPRING6D',
    'BEAM27',
    'BEAM37',
    'BAR2',
    'BAR3',
    'CABLE2',
    'CABLE3',
    'TRI3',
    'TRI6',
    'QUAD4',
    'QUAD8',
    'MITC3',
    'MITC6',
    'MITC4',
    'MITC8',
    'TETRA4',
    'TETRA10',
    'HEX8',
    'HEX20',
    'TETRA4S',
    'TETRA10S',
    'HEX8S',
    'HEX20S',
    'WEDGE6',
    'WEDGE15',
    'WEDGE6S',
    'WEDGE15S',
    'PYR5',
    'PYR13',
    'PYR5S',
    'PYR13S',
    'TRI3S',
    'TRI6S',
    'QUAD4S',
    'QUAD8S',
    'SPRING2D',
    'SHELL3S',
    'SHELL4S',
    'SHELL6S',
    'SHELL8S',
    'BEAM26S',
    'BEAM36S',
    'BEAM27S',
    'BEAM37S'
]


class FCElementType(TypedDict):
    name: FCElementTypeLiteral 
    code: int 
    dim: int 
    order: int 
    vertices_count: int
    nodes_count: int 
    nodes_coords: List[List[float]]
    edges: List[List[int]]
    faces: List[List[int]]


_POINT_COORDS = [
    [0.0, 0.0, 0.0]
]

_LINE2_COORDS = [
    [-1.0], 
    [1.0]
]
_LINE3_COORDS = [
    *_LINE2_COORDS, 
    [0.0]
]

_TRI3_COORDS = [
    [1.0, 0.0], 
    [0.0, 1.0], 
    [0.0, 0.0]
]
_TRI6_COORDS = [
    *_TRI3_COORDS,
    [0.5, 0.5],
    [0.0, 0.5],
    [0.5, 0.0],
]

_QUAD4_COORDS = [
    [-1.0, -1.0], 
    [1.0, -1.0], 
    [1.0, 1.0], 
    [-1.0, 1.0]
]

_QUAD8_COORDS = [
    *_QUAD4_COORDS,
    [0.0, -1.0],
    [1.0, 0.0],
    [0.0, 1.0],
    [-1.0, 0.0],
]

_TETRA4_COORDS = [
    [0.0, 1.0, 0.0],
    [1.0, 0.0, 0.0],
    [0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0],
]
_TETRA10_COORDS = [
    *_TETRA4_COORDS,
    [0.5, 0.5, 0.0],
    [0.5, 0.0, 0.5],
    [0.0, 0.5, 0.5],
    [0.0, 0.5, 0.0],
    [0.5, 0.0, 0.0],
    [0.0, 0.0, 0.5],
]

_HEX8_COORDS = [
    [-1.0, -1.0, -1.0],
    [1.0, -1.0, -1.0],
    [1.0, 1.0, -1.0],
    [-1.0, 1.0, -1.0],
    [-1.0, -1.0, 1.0],
    [1.0, -1.0, 1.0],
    [1.0, 1.0, 1.0],
    [-1.0, 1.0, 1.0],
]
_HEX20_COORDS = [
    *_HEX8_COORDS,
    [0.0, -1.0, -1.0],
    [1.0, 0.0, -1.0],
    [0.0, 1.0, -1.0],
    [-1.0, 0.0, -1.0],
    [0.0, -1.0, 1.0],
    [1.0, 0.0, 1.0],
    [0.0, 1.0, 1.0],
    [-1.0, 0.0, 1.0],
    [-1.0, -1.0, 0.0],
    [1.0, -1.0, 0.0],
    [1.0, 1.0, 0.0],
    [-1.0, 1.0, 0.0],
]

_WEDGE6_COORDS = [
    [-1.0, 1.0, 0.0],
    [-1.0, 0.0, 1.0],
    [-1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0],
    [1.0, 0.0, 1.0],
    [1.0, 0.0, 0.0],
]
_WEDGE15_COORDS = [
    *_WEDGE6_COORDS,
    [-1.0, 0.5, 0.5],
    [-1.0, 0.0, 0.5],
    [-1.0, 0.5, 0.0],
    [1.0, 0.5, 0.5],
    [1.0, 0.0, 0.5],
    [1.0, 0.5, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [0.0, 0.0, 0.0],
]

_PYR5_COORDS = [
    [-1.0, -1.0, -1.0],
    [1.0, -1.0, -1.0],
    [1.0, 1.0, -1.0],
    [-1.0, 1.0, -1.0],
    [0.0, 0.0, 1.0],
]
_PYR13_COORDS = [
    *_PYR5_COORDS,
    [0.0, -1.0, -1.0],
    [1.0, 0.0, -1.0],
    [0.0, 1.0, -1.0],
    [-1.0, 0.0, -1.0],
    [-0.5, -0.5, 0.0],
    [0.5, -0.5, 0.0],
    [0.5, 0.5, 0.0],
    [-0.5, 0.5, 0.0],
]

_LINE2_EDGES = [[0, 1]]
_LINE3_EDGES = [[0, 1, 2]]

_TRI3_EDGES = [[0, 1], [1, 2], [0, 2]]
_TRI6_EDGES = [[0, 1, 3], [1, 2, 4], [0, 2, 5]]

_QUAD4_EDGES = [[0, 1], [1, 2], [2, 3], [0, 3]]
_QUAD8_EDGES = [[0, 1, 4], [1, 2, 5], [2, 3, 6], [0, 3, 7]]

_TETRA4_EDGES = [[0, 1], [1, 2], [0, 2], [0, 3], [1, 3], [2, 3]]
_TETRA10_EDGES = [[0, 1, 4], [1, 2, 5], [0, 2, 6], [0, 3, 7], [1, 3, 8], [2, 3, 9]]
_TETRA4_FACES = [[0, 2, 3], [1, 2, 3], [0, 1, 3], [0, 1, 2]]
_TETRA10_FACES = [[0, 2, 3, 6, 9, 7], [1, 2, 3, 5, 9, 8], [0, 1, 3, 4, 8, 7], [0, 1, 2, 4, 5, 6]]

_HEX8_EDGES = [[0, 1], [1, 2], [2, 3], [0, 3], [4, 5], [5, 6], [6, 7], [4, 7], [0, 4], [1, 5], [2, 6], [3, 7]]
_HEX20_EDGES = [[0, 1, 8], [1, 2, 9], [2, 3, 10], [0, 3, 11], [4, 5, 12], [5, 6, 13], [6, 7, 14], [4, 7, 15], [0, 4, 16], [1, 5, 17], [2, 6, 18], [3, 7, 19]]
_HEX8_FACES = [[0, 1, 2, 3], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [0, 3, 7, 4], [4, 5, 6, 7]]
_HEX20_FACES = [[0, 1, 2, 3, 8, 9, 10, 11], [0, 1, 5, 4, 8, 17, 12, 16], [1, 2, 6, 5, 9, 18, 13, 17], [2, 3, 7, 6, 10, 19, 14, 18], [0, 3, 7, 4, 11, 19, 15, 16], [4, 5, 6, 7, 12, 13, 14, 15]]

_WEDGE6_EDGES = [[0, 1], [1, 2], [0, 2], [3, 4], [4, 5], [3, 5], [0, 3], [1, 4], [2, 5]]
_WEDGE15_EDGES = [[0, 1, 6], [1, 2, 7], [0, 2, 8], [3, 4, 9], [4, 5, 10], [3, 5, 11], [0, 3, 12], [1, 4, 13], [2, 5, 14]]
_WEDGE6_FACES = [[0, 1, 2], [1, 2, 4, 5], [0, 2, 3, 5], [0, 1, 3, 4], [3, 4, 5]]
_WEDGE15_FACES = [[0, 1, 2, 6, 7, 8], [1, 2, 4, 5, 7, 10, 13, 14], [0, 2, 3, 5, 8, 11, 12, 14], [0, 1, 3, 4, 6, 9, 12, 13], [3, 4, 5, 9, 10, 11]]

_PYR5_EDGES = [[0, 1], [1, 2], [2, 3], [0, 3], [0, 4], [1, 4], [2, 4], [3, 4]]
_PYR13_EDGES = [[0, 1, 5], [1, 2, 6], [2, 3, 7], [0, 3, 8], [0, 4, 9], [1, 4, 10], [2, 4, 11], [3, 4, 12]]
_PYR5_FACES = [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
_PYR13_FACES = [[0, 1, 2, 3, 5, 6, 7, 8], [0, 1, 4, 5, 10, 9], [1, 2, 4, 6, 11, 10], [2, 3, 4, 7, 12, 11], [3, 0, 4, 8, 9, 12]]


FCElementTypeRow = Tuple[
    FCElementTypeLiteral,
    int,
    int,
    int,
    int,
    List[List[float]],
    List[List[int]],
    List[List[int]],
]


_FC_ELEMENT_TYPE_ROWS: List[FCElementTypeRow] = [
    # name          code  dim  order  verts  nodes_coords      edges           faces
    ('NONE',          0,    0,     0,     0, [],               [],             []),

    ('LUMPMASS3D',   38,    0,     1,     1, _POINT_COORDS,    [],             []),
    ('LUMPMASS6D',   40,    0,     1,     1, _POINT_COORDS,    [],             []),
    ('LUMPMASS2D',   82,    0,     1,     1, _POINT_COORDS,    [],             []),
    ('POINT3D',      99,    0,     1,     1, _POINT_COORDS,    [],             []),
    ('POINT2D',     100,    0,     1,     1, _POINT_COORDS,    [],             []),
    ('POINT6D',     101,    0,     1,     1, _POINT_COORDS,    [],             []),
    ('LUMPMASS2DR', 105,    0,     1,     1, _POINT_COORDS,    [],             []),

    ('BEAM26',       36,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('BEAM36',       37,    1,     2,     2, _LINE3_COORDS,    _LINE3_EDGES,   []),
    ('SPRING3D',     39,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('SPRING6D',     41,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('SPRING2D',     83,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('BEAM27',       89,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('BEAM37',       90,    1,     2,     2, _LINE3_COORDS,    _LINE3_EDGES,   []),
    ('BEAM26S',      95,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('BEAM36S',      96,    1,     2,     2, _LINE3_COORDS,    _LINE3_EDGES,   []),
    ('BEAM27S',      97,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('BEAM37S',      98,    1,     2,     2, _LINE3_COORDS,    _LINE3_EDGES,   []),
    ('BAR2',        107,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('BAR3',        108,    1,     2,     2, _LINE3_COORDS,    _LINE3_EDGES,   []),
    ('CABLE2',      109,    1,     1,     2, _LINE2_COORDS,    _LINE2_EDGES,   []),
    ('CABLE3',      110,    1,     2,     2, _LINE3_COORDS,    _LINE3_EDGES,   []),

    ('TRI3',         10,    2,     1,     3, _TRI3_COORDS,     _TRI3_EDGES,    _TRI3_EDGES),
    ('TRI6',         11,    2,     2,     3, _TRI6_COORDS,     _TRI6_EDGES,    _TRI6_EDGES),
    ('QUAD4',        12,    2,     1,     4, _QUAD4_COORDS,    _QUAD4_EDGES,   _QUAD4_EDGES),
    ('QUAD8',        13,    2,     2,     4, _QUAD8_COORDS,    _QUAD8_EDGES,   _QUAD8_EDGES),
    ('TRI3S',        24,    2,     1,     3, _TRI3_COORDS,     _TRI3_EDGES,    _TRI3_EDGES),
    ('TRI6S',        25,    2,     2,     3, _TRI6_COORDS,     _TRI6_EDGES,    _TRI6_EDGES),
    ('QUAD4S',       26,    2,     1,     4, _QUAD4_COORDS,    _QUAD4_EDGES,   _QUAD4_EDGES),
    ('QUAD8S',       27,    2,     2,     4, _QUAD8_COORDS,    _QUAD8_EDGES,   _QUAD8_EDGES),
    ('MITC3',        29,    2,     1,     3, _TRI3_COORDS,     _TRI3_EDGES,    _TRI3_EDGES),
    ('MITC6',        30,    2,     2,     3, _TRI6_COORDS,     _TRI6_EDGES,    _TRI6_EDGES),
    ('MITC4',        31,    2,     1,     4, _QUAD4_COORDS,    _QUAD4_EDGES,   _QUAD4_EDGES),
    ('MITC8',        32,    2,     2,     4, _QUAD8_COORDS,    _QUAD8_EDGES,   _QUAD8_EDGES),
    ('SHELL3S',      84,    2,     1,     3, _TRI3_COORDS,     _TRI3_EDGES,    _TRI3_EDGES),
    ('SHELL4S',      85,    2,     1,     4, _QUAD4_COORDS,    _QUAD4_EDGES,   _QUAD4_EDGES),
    ('SHELL6S',      86,    2,     2,     3, _TRI6_COORDS,     _TRI6_EDGES,    _TRI6_EDGES),
    ('SHELL8S',      87,    2,     2,     4, _QUAD8_COORDS,    _QUAD8_EDGES,   _QUAD8_EDGES),

    ('TETRA4',        1,    3,     1,     4, _TETRA4_COORDS,   _TETRA4_EDGES,  _TETRA4_FACES),
    ('TETRA10',       2,    3,     2,     4, _TETRA10_COORDS,  _TETRA10_EDGES, _TETRA10_FACES),
    ('HEX8',          3,    3,     1,     8, _HEX8_COORDS,     _HEX8_EDGES,    _HEX8_FACES),
    ('HEX20',         4,    3,     2,     8, _HEX20_COORDS,    _HEX20_EDGES,   _HEX20_FACES),
    ('WEDGE6',        6,    3,     1,     6, _WEDGE6_COORDS,   _WEDGE6_EDGES,  _WEDGE6_FACES),
    ('WEDGE15',       7,    3,     2,     6, _WEDGE15_COORDS,  _WEDGE15_EDGES, _WEDGE15_FACES),
    ('PYR5',          8,    3,     1,     5, _PYR5_COORDS,     _PYR5_EDGES,    _PYR5_FACES),
    ('PYR13',         9,    3,     2,     5, _PYR13_COORDS,    _PYR13_EDGES,   _PYR13_FACES),
    ('TETRA4S',      15,    3,     1,     4, _TETRA4_COORDS,   _TETRA4_EDGES,  _TETRA4_FACES),
    ('TETRA10S',     16,    3,     2,     4, _TETRA10_COORDS,  _TETRA10_EDGES, _TETRA10_FACES),
    ('HEX8S',        17,    3,     1,     8, _HEX8_COORDS,     _HEX8_EDGES,    _HEX8_FACES),
    ('HEX20S',       18,    3,     2,     8, _HEX20_COORDS,    _HEX20_EDGES,   _HEX20_FACES),
    ('WEDGE6S',      20,    3,     1,     6, _WEDGE6_COORDS,   _WEDGE6_EDGES,  _WEDGE6_FACES),
    ('WEDGE15S',     21,    3,     2,     6, _WEDGE15_COORDS,  _WEDGE15_EDGES, _WEDGE15_FACES),
    ('PYR5S',        22,    3,     1,     5, _PYR5_COORDS,     _PYR5_EDGES,    _PYR5_FACES),
    ('PYR13S',       23,    3,     2,     5, _PYR13_COORDS,    _PYR13_EDGES,   _PYR13_FACES),
]

FC_ELEMENT_TYPES: List[FCElementType] = []
for (
    name,
    code,
    dim,
    order,
    vertices_count,
    nodes_coords,
    edges,
    faces,
) in _FC_ELEMENT_TYPE_ROWS:
    FC_ELEMENT_TYPES.append({
        'name': name,
        'code': code,
        'dim': dim,
        'order': order,
        'vertices_count': vertices_count,
        'nodes_count': len(nodes_coords),
        'nodes_coords': nodes_coords,
        'edges': edges,
        'faces': faces,
    })

FC_ELEMENT_TYPES_KEYID: Dict[int, FCElementType] = {
    element_type['code']:element_type for element_type in FC_ELEMENT_TYPES
}

FC_ELEMENT_TYPES_KEYNAME: Dict[FCElementTypeLiteral, FCElementType] = {
    element_type['name']:element_type for element_type in FC_ELEMENT_TYPES
}


class FCSrcElement(TypedDict):
    id: int
    block: int
    parent_id: int
    type: FCElementTypeLiteral
    nodes: List[int]
    order: int


class FCElement:
    """
    Определяет один конечный элемент в сетке.
    """
    id: int
    block: int
    parent_id: int
    type: FCElementTypeLiteral
    nodes: List[int]
    order: int

    def __init__(self, src_element: FCSrcElement):
        """
        Инициализатор для FCElem.
        """

        self.id = src_element['id']
        self.block = src_element['block']
        self.parent_id = src_element['parent_id']
        self.type = src_element['type']
        self.nodes = src_element['nodes']
        self.order = src_element['order']
       

    def encode(self) -> FCSrcElement:
        return {
            'id': self.id,
            'block': self.block,
            'parent_id': self.parent_id,
            'type': self.type,
            'nodes': self.nodes,
            'order': self.order,
        }

    def __str__(self) -> str:
        return (
            f"FCElement(id={self.id}, type='{self.type}', nodes={self.nodes}, "
            f"block={self.block}, parent_id={self.parent_id}, order={self.order})"
        )

    def __repr__(self) -> str:
        return (
            f"<FCElement {self.id} ('{self.type}')>"
        )
