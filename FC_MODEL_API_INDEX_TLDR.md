## fc_model API TL;DR (≤ 400 tokens)

Use only: `from fc_model import ...` (public re-exports). Serialize via `encode()`/`save()` only.

### Root
- FCModel()
  - Fields: `header`, `coordinate_systems: Dict[int, FCCoordinateSystem]`, `mesh: FCMesh`,
    `blocks: Dict[int, FCBlock]`, `materials: Dict[int, FCMaterial]`, `property_tables`,
    `loads: List[FCLoad]`, `restraints`, `initial_sets`, `contact_constraints`,
    `coupling_constraints`, `periodic_constraints`, `receivers`, `nodesets`, `sidesets`, `settings: dict`.
  - Methods: `load(path: str) -> FCModel`, `decode(data: dict) -> FCModel`, `encode() -> Dict[str, Any]`, `save(path: str) -> None`.
  - Constructors/helpers: `add_material(name)`, `add_load(...)`, `add_restraint(...)`, `add_initial_set(...)`, `add_nodeset(...)`, `add_sideset(...)`.

### Mesh and geometry
- FCMesh: holds arrays (node ids/coords, elem ids/types/blocks/orders/parents, flattened `elems`).
- FCCoordinateSystem: `id`, `type`, `name`, `origin`, `dir1`, `dir2` (vectors encoded/decoded as Base64 in JSON).

### Materials and properties
- FCMaterial: `id`, `name`, grouped `properties` (elasticity/common/thermal/...).
- FCMaterial has helper: `add_property(group_name, property_name, values, property_type=None)`.
- FCMaterialProperty: `type`, `name`, `data: FCData`.
- FCData: represents constant/table/formula; fields `data`, `dep_type`, `dep_data`.
  - Helpers: `FCData.constant(x|[x...])`, `FCData.formula('...')`.

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
from fc_model import FCModel, FCData
m = FCModel.load("in.fc")
mat = m.add_material("Steel")
mat.add_property("common", "DENSITY", 7850.0, "USUAL")
m.add_restraint(name="Fix", flags=["UX","UY","UZ"], apply_to="all", data=[FCData.constant(0.0)]*3)
m.save("out.fc")
```


