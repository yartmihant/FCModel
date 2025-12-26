## fc_model API TL;DR (≤ 400 tokens)

Use only: `from fc_model import ...` (public re-exports). Serialize via `dump()`/`save()` only.

### Root
- FCModel(filepath: Optional[str] = None)
  - Fields: `header`, `coordinate_systems: Dict[int, FCCoordinateSystem]`, `mesh: FCMesh`,
    `blocks: Dict[int, FCBlock]`, `materials: Dict[int, FCMaterial]`, `property_tables`,
    `loads: List[FCLoad]`, `restraints`, `initial_sets`, `contact_constraints`,
    `coupling_constraints`, `periodic_constraints`, `receivers`, `nodesets`, `sidesets`, `settings: dict`.
  - Methods: `dump() -> Dict[str, Any]`, `save(path: str) -> None`.

### Mesh and geometry
- FCMesh: holds arrays (node ids/coords, elem ids/types/blocks/orders/parents, flattened `elems`).
- FCCoordinateSystem: `id`, `type`, `name`, `origin`, `dir1`, `dir2` (vectors encoded/decoded as Base64 in JSON).

### Materials and properties
- FCMaterial: `id`, `name`, grouped `properties` (elasticity/common/thermal/...).
- FCMaterialProperty: `type`, `name`, `data: FCData`.
- FCData: represents constant/table/formula; fields `data`, `dep_type`, `dep_data`.

### Topology and grouping
- FCBlock: links elements to materials/properties.
- FCSet: node/side sets; FCReceiver: result receivers.

### Loads, restraints, initial sets
- FCLoad, FCRestraint, FCInitialSet: accept `apply_to` (list or string "all"); support component dependencies and steps.

### Constraints
- FCConstraint: contact/coupling/periodic structures preserved round‑trip with additional fields.

### Constants (import from fc_model)
- Materials: `FC_MATERIAL_PROPERTY_NAMES_KEYS/CODES`, `FC_MATERIAL_PROPERTY_TYPES_KEYS/CODES`.
- Loads/BC/IC: `FC_LOADS_TYPES_KEYS/CODES`, `FC_RESTRAINT_FLAGS_KEYS/CODES`, `FC_INITIAL_SET_TYPES_KEYS/CODES`.
- Mesh: `FC_ELEMENT_TYPES_KEYID/KEYNAME`.
- Dependencies: `FC_DEPENDENCY_TYPES_KEYS/CODES`.

### Invariants
- Import from `fc_model` root; rely on type hints.
- Use constants, do not hardcode numeric codes.
- `settings` is a dict (default `{}`).
- `elem_types` are unsigned bytes (uint8) in JSON.
- Binary arrays encoded as Base64 strings in JSON.

### Minimal usage
```python
from fc_model import FCModel, FCMaterialProperty, FCData
m = FCModel("in.fc"); m.save("out.fc")
mat = m.materials[next(iter(m.materials))]
mat.properties.setdefault("common", [[]])[0].append(
  FCMaterialProperty(type="USUAL", name="DENSITY", data=FCData(data="", dep_type=0, dep_data=""))
)
```


