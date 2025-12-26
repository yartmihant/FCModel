from __future__ import annotations
from typing import Any, TypedDict, Dict, Union

from numpy import dtype, int32
import numpy as np

from .fc_value import FCValue


class FCSrcConstraint(TypedDict):
    id: int
    name: str
    type: Union[int, str]
    master: str
    master_size: int
    slave: str
    slave_size: int


class FCConstraint:
    id: int
    name: str
    type: Union[int, str]
    master: FCValue
    slave: FCValue
    properties: Dict[str, Any]

    def __init__(self, id: int = 0, name: str = "", type_val: Union[int, str] = 0):
        self.id = id
        self.name = name
        self.type = type_val
        self.master = FCValue(np.array([], dtype=int32))
        self.slave = FCValue(np.array([], dtype=int32))
        self.properties = {}

    @classmethod
    def decode(cls, src_data: FCSrcConstraint) -> FCConstraint:
        
        constraint = cls(
            id=src_data['id'],
            name=src_data['name'],
            type_val=src_data['type']
        )

        constraint.master = FCValue.decode(src_data['master'], dtype(int32))
        constraint.master.reshape(src_data['master_size'])

        constraint.slave = FCValue.decode(src_data['slave'], dtype(int32))
        constraint.slave.reshape(src_data['slave_size'])

        constraint.properties = {
            key: src_data[key] for key in src_data #type:ignore
            if key not in FCSrcConstraint.__annotations__.keys()}
        return constraint

    def encode(self) -> FCSrcConstraint:
        src_constraint: FCSrcConstraint = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "master": self.master.encode(),
            "slave": self.slave.encode(),
            "master_size": len(self.master),
            "slave_size": len(self.slave),
        }

        for key in self.properties:
            src_constraint[key] = self.properties[key] #type:ignore

        return src_constraint


    def __str__(self) -> str:
        return (
            f"FCConstraint(id={self.id}, name='{self.name}', type={self.type}, "
            f"master={self.master}, slave={self.slave}, properties={self.properties})"
        )

    def __repr__(self) -> str:
        return f"<FCConstraint {self.id!r} {self.name!r} {self.type!r}>"