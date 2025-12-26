from __future__ import annotations
from typing import TypedDict
from numpy.typing import NDArray

from numpy import dtype, float64
import numpy as np

from .fc_value import decode, encode



class FCSrcCoordinateSystem(TypedDict):
    id: int
    type: str
    name: str
    origin: str
    dir1: str
    dir2: str


class FCCoordinateSystem:
    id: int
    type: str
    name: str
    origin: NDArray[float64]
    dir1: NDArray[float64]
    dir2: NDArray[float64]


    def __init__(self, id: int = 0, name: str = "", type_name: str = "cartesian"):
        self.id = id
        self.type = type_name
        self.name = name
        self.origin = np.array([0., 0., 0.], dtype=float64)
        self.dir1 = np.array([1., 0., 0.], dtype=float64)
        self.dir2 = np.array([0., 1., 0.], dtype=float64)

    @classmethod
    def decode(cls, src_data: FCSrcCoordinateSystem) -> FCCoordinateSystem:
        cs = cls(
            id=src_data['id'],
            name=src_data['name'],
            type_name=src_data['type']
        )
        cs.origin = decode(src_data['origin'], dtype(float64))
        cs.dir1 = decode(src_data['dir1'], dtype(float64))
        cs.dir2 = decode(src_data['dir2'], dtype(float64))
        return cs

    def encode(self) -> FCSrcCoordinateSystem:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "origin": encode(self.origin),
            "dir1": encode(self.dir1),
            "dir2": encode(self.dir2)
        }

    def __str__(self) -> str:
        return (
            f"FCCoordinateSystem(id={self.id}, type='{self.type}', name='{self.name}', "
            f"origin={self.origin}, dir1={self.dir1}, dir2={self.dir2})"
        )

    def __repr__(self) -> str:
        return f"<FCCoordinateSystem id={self.id!r} type={self.type!r} name={self.name!r}>"
