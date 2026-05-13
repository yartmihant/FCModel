
from __future__ import annotations
from typing import Any, TypedDict, Dict


FC_PROPERTY_TABLE_TYPES_KEYS: Dict[int, str] = {
    0: "SHELL",
    1: "BEAM",
    5: "LUMPMASS",
    6: "SPRING",
}

FC_PROPERTY_TABLE_TYPES_CODES: Dict[str, int] = {v: k for k, v in FC_PROPERTY_TABLE_TYPES_KEYS.items()}


FC_BEAM_SECTION_TYPES_KEYS: Dict[int, str] = {
    0: "RECTANGLE",
    1: "ELLIPSE",
    2: "I_BEAM",
    3: "CIRCLE_WITH_A_CUT",
    4: "POINT",
    5: "C_BEAM",
    6: "L_BEAM",
    7: "Z_BEAM",
    8: "T_BEAM",
    9: "RECTANGLE_WITH_A_CUT",
    10: "HAT_BEAM",
    12: "PIPE",
}

FC_BEAM_SECTION_TYPES_CODES: Dict[str, int] = {v: k for k, v in FC_BEAM_SECTION_TYPES_KEYS.items()}


class FCSrcPropertyTableStrict(TypedDict):
    id: int
    type: int
    properties: Dict[str, Any]
    additional_properties: Dict[str, Any]


class FCSrcPropertyTable(FCSrcPropertyTableStrict, total=False):
    name: str


class FCPropertyTable:
    id: int
    type: str
    name: str
    properties: Dict[str, Any]
    additional_properties: Dict[str, Any]

    def __init__(self, id: int = 0, type_val: str = "SHELL", name: str = ""):
        self.id = id
        self.type = type_val
        self.name = name
        self.properties = {}
        self.additional_properties = {}

    @classmethod
    def decode(cls, src_data: FCSrcPropertyTable) -> FCPropertyTable:
        type_code = src_data.get('type', 0)
        pt = cls(id=src_data['id'], type_val=FC_PROPERTY_TABLE_TYPES_KEYS.get(type_code, str(type_code)), name=src_data.get('name', ''))
        pt.properties = src_data.get('properties', {})
        pt.additional_properties = src_data.get('additional_properties', {})
        return pt

    def encode(self) -> FCSrcPropertyTable:
        out: FCSrcPropertyTable = {
            "id": self.id,
            "type": FC_PROPERTY_TABLE_TYPES_CODES.get(self.type, int(self.type) if self.type.isdigit() else 0),
            "properties": self.properties,
            "additional_properties": self.additional_properties
        }
        if self.name:
            out["name"] = self.name
        return out

    def __str__(self) -> str:
        return (
            f"FCPropertyTable(id={self.id}, type={self.type}, properties={self.properties}, additional_properties={self.additional_properties})"
        )

    def __repr__(self) -> str:
        return (
            f"<FCPropertyTable {self.id!r} {self.type!r}>"
        )
