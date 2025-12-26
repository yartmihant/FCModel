from __future__ import annotations
from typing import TypedDict, List

from numpy import dtype, int32
import numpy as np
from .fc_value import FCValue


class FCSrcReceiver(TypedDict):
    id: int
    name: str
    apply_to: str
    apply_to_size: int
    dofs: List[int]
    type: int


class FCReceiver:
    id: int
    apply: FCValue
    dofs: List[int]
    name: str
    type: int

    def __init__(self, id: int = 0, name: str = "", type_val: int = 0, dofs: List[int] = []):
        self.id = id
        self.name = name
        self.type = type_val
        self.dofs = dofs
        self.apply = FCValue(np.array([], dtype=int32))

    @classmethod
    def decode(cls, src_data: FCSrcReceiver) -> FCReceiver:
        receiver = cls(
            id=src_data['id'],
            name=src_data['name'],
            type_val=src_data['type'],
            dofs=src_data['dofs']
        )
        receiver.apply = FCValue.decode(src_data['apply_to'], dtype(int32))
        return receiver

    def encode(self) -> FCSrcReceiver:
        return {
            "apply_to": self.apply.encode(),
            "apply_to_size": len(self.apply),
            "id": self.id,
            "name": self.name,
            "dofs": self.dofs,
            "type": self.type
        }

    def __str__(self) -> str:
        return (
            f"FCReceiver(id={self.id}, name='{self.name}', dofs={self.dofs}, type={self.type}, apply_to_size={len(self.apply)})"
        )

    def __repr__(self) -> str:
        return (
            f"<FCReceiver {self.id!r} {self.name!r}>"
        )
