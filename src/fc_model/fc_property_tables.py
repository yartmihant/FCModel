
from __future__ import annotations
from typing import Any, TypedDict, Dict


class FCSrcPropertyTable(TypedDict):
    id: int
    type: int
    properties: Dict[str, Any]
    additional_properties: Dict[str, Any]


class FCPropertyTable:
    id: int
    type: int
    properties: Dict[str, Any]
    additional_properties: Dict[str, Any]

    def __init__(self, id: int = 0, type_val: int = 0):
        self.id = id
        self.type = type_val
        self.properties = {}
        self.additional_properties = {}

    @classmethod
    def decode(cls, src_data: FCSrcPropertyTable) -> FCPropertyTable:
        pt = cls(id=src_data['id'], type_val=src_data.get('type', 0))
        pt.properties = src_data.get('properties', {})
        pt.additional_properties = src_data.get('additional_properties', {})
        return pt

    def encode(self) -> FCSrcPropertyTable:
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties,
            "additional_properties": self.additional_properties
        }

    def __str__(self) -> str:
        return (
            f"FCPropertyTable(id={self.id}, type={self.type}, properties={self.properties}, additional_properties={self.additional_properties})"
        )

    def __repr__(self) -> str:
        return (
            f"<FCPropertyTable {self.id!r} {self.type!r}>"
        )
