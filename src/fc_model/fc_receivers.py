from __future__ import annotations
from typing import Dict, Optional, TypedDict, List

from numpy import dtype, int32
import numpy as np
from .fc_value import FCValue


FC_RECEIVER_TYPES_KEYS: Dict[int, str] = {
    0: "DISPLACEMENT",
    1: "VELOCITY",
    2: "PRINCIPAL_STRESS",
    3: "PRESSURE",
    4: "ACCELERATION",
}

FC_RECEIVER_TYPES_CODES: Dict[str, int] = {v: k for k, v in FC_RECEIVER_TYPES_KEYS.items()}


class FCSrcReceiverStrict(TypedDict):
    id: int
    name: str
    apply_to: str
    apply_to_size: int
    dofs: List[int]
    type: int


class FCSrcReceiver(FCSrcReceiverStrict, total=False):
    output_step: int


class FCReceiver:
    id: int
    apply: FCValue
    dofs: List[int]
    name: str
    type: int
    output_step: Optional[int]

    def __init__(self, id: int = 0, name: str = "", type_val: int = 0, dofs: List[int] = []):
        self.id = id
        self.name = name
        self.type = type_val
        self.dofs = dofs
        self.apply = FCValue(np.array([], dtype=int32))
        self.output_step = None

    @classmethod
    def decode(cls, src_data: FCSrcReceiver) -> FCReceiver:
        receiver = cls(
            id=src_data['id'],
            name=src_data['name'],
            type_val=src_data['type'],
            dofs=src_data['dofs']
        )
        receiver.apply = FCValue.decode(src_data['apply_to'], dtype(int32))
        if 'output_step' in src_data:
            receiver.output_step = src_data['output_step']
        return receiver

    def encode(self) -> FCSrcReceiver:
        out: FCSrcReceiver = {
            "apply_to": self.apply.encode(),
            "apply_to_size": len(self.apply),
            "id": self.id,
            "name": self.name,
            "dofs": self.dofs,
            "type": self.type
        }
        if self.output_step is not None:
            out["output_step"] = self.output_step
        return out

    def __str__(self) -> str:
        return (
            f"FCReceiver(id={self.id}, name='{self.name}', dofs={self.dofs}, type={self.type}, apply_to_size={len(self.apply)})"
        )

    def __repr__(self) -> str:
        return (
            f"<FCReceiver {self.id!r} {self.name!r}>"
        )
