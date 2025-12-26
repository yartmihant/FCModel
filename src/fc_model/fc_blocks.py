from __future__ import annotations
from typing import TypedDict, List, Dict, Optional


class FCSrcBlockMaterial(TypedDict):
    ids: List[int]
    steps: List[int]


class FCSrcBlockStrict(TypedDict):
    id: int
    cs_id: int
    material_id: int
    property_id: int

class FCSrcBlock(FCSrcBlockStrict, total=False):
    steps: List[int]  # Опционально в файле
    material: FCSrcBlockMaterial  # Опционально в файле


class FCBlock:
    """
    Определяет 'блок' элементов.
    Блок - это группа элементов, которая ссылается на один и тот же материал
    и имеет общие свойства.
    """
    id: int
    cs_id: int
    material_id: int
    property_id: int

    # Опциональные поля блока
    steps: Optional[List[int]]
    material: Optional[Dict[str, List[int]]]

    def __init__(self, id: int = 0, cs_id: int = 0, material_id: int = 0, property_id: int = 0):
        self.id = id
        self.cs_id = cs_id
        self.material_id = material_id
        self.property_id = property_id
        self.steps = None
        self.material = None

    @classmethod
    def decode(cls, src_data: FCSrcBlock) -> FCBlock:
        block = cls(
            id=src_data['id'],
            cs_id=src_data['cs_id'],
            material_id=src_data['material_id'],
            property_id=src_data['property_id']
        )

        if 'steps' in src_data:
            steps_val = src_data.get('steps')
            if isinstance(steps_val, list):
                block.steps = [int(x) for x in steps_val]
            else:
                raise ValueError(f"Block(id={block.id}) steps must be a list of ints")

        if 'material' in src_data:
            mat_val = src_data.get('material')
            if isinstance(mat_val, dict):
                ids = mat_val.get('ids', [])
                stp = mat_val.get('steps', [])
                if not isinstance(ids, list) or not isinstance(stp, list):
                    raise ValueError(f"Block(id={block.id}) material.ids and material.steps must be lists")
                if len(ids) != len(stp):
                    raise ValueError(f"Block(id={block.id}) material ids ({len(ids)}) and steps ({len(stp)}) length mismatch")
                # нормализуем к int
                block.material = {
                    'ids': [int(v) for v in ids],
                    'steps': [int(v) for v in stp],
                }
            else:
                raise ValueError(f"Block(id={block.id}) material must be a dict with ids/steps")
        return block

    def encode(self) -> FCSrcBlock:
        out: FCSrcBlock = {
            "id": self.id,
            "material_id": self.material_id,
            "property_id": self.property_id,
            "cs_id": self.cs_id,
        }
        if self.steps is not None and len(self.steps):
            out['steps'] = list(self.steps)
        if self.material is not None and len(self.material.get('ids', [])):
            out['material'] = {
                'ids': list(self.material['ids']),
                'steps': list(self.material['steps']),
            }
        return out

    def __str__(self) -> str:
        return (
            f"FCBlock(id={self.id}, cs_id={self.cs_id}, material_id={self.material_id}, "
            f"property_id={self.property_id}, steps={self.steps}, material={self.material})"
        )

    def __repr__(self) -> str:
        return (
            f"<FCBlock {self.id!r}>"
        )
