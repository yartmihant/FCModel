from __future__ import annotations
from typing import TypedDict

from numpy import dtype, int32
import numpy as np

from .fc_value import FCValue


class FCSrcSet(TypedDict):
    id: int
    name: str
    apply_to: str
    apply_to_size: int


class FCSet:
    id: int
    apply: FCValue
    name: str

    def __init__(self, id: int = 0, name: str = ""):
        self.id = id
        self.name = name
        self.apply = FCValue(np.array([], dtype=int32))

    @classmethod
    def decode(cls, src_data: FCSrcSet) -> FCSet:
        s = cls(id=src_data['id'], name=src_data['name'])
        s.apply = FCValue.decode(src_data['apply_to'], dtype(int32))
        s.apply.reshape(src_data['apply_to_size'])
        return s

    def encode(self) -> FCSrcSet:
        return {
            "apply_to": self.apply.encode(),
            "apply_to_size": len(self.apply),
            "id": self.id,
            "name": self.name
        }

    def __str__(self) -> str:
        return f"FCSet(id={self.id}, name='{self.name}', apply_to_size={len(self.apply)})"

    def __repr__(self) -> str:
        return f"<FCSet{'['+self.name+']' if self.name else ''} {self.id!r} {self.apply.__repr__()}>"
