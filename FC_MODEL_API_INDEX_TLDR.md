## fc_model API TL;DR (≤ 600 tokens)

Import only from `fc_model` root. Serialize via `encode()`/`save()` only. Load via `FCModel.load(path)` — NOT `FCModel("path")`.

### FCModel (root)
- Fields: `header`, `settings: dict`, `mesh: FCMesh`, `coordinate_systems`, `blocks`, `materials`, `property_tables` (all `Dict[int, ...]`), `loads`, `restraints`, `initial_sets`, `contact_constraints`, `coupling_constraints`, `periodic_constraints`, `receivers` (all `List[...]`), `nodesets`, `sidesets` (`Dict[int, FCSet]`).
- Class methods: `load(path) -> FCModel`, `decode(dict) -> FCModel`.
- Instance: `encode() -> dict`, `save(path)`.
- Helpers: `add_material(name)`, `add_load(...)`, `add_restraint(...)`, `add_initial_set(...)`, `add_nodeset(...)`, `add_sideset(...)`, `add_coordinate_system(...)`, `add_material_property(...)`.
- Index normalization: `compress()` — renumber all entity IDs to `[1,2,3,...]`, update all cross-references.

### Data classes
- **FCMesh**: `nodes_ids`, `nodes_xyz`, `elements` dict. Methods: `add()`, `compress() -> Dict[int,int]`, `reindex(map)`, `__len__`, `__iter__`, `__getitem__`.
- **FCBlock**: `id`, `cs_id`, `material_id`, `property_id`, optional `steps`, `material`.
- **FCCoordinateSystem**: `id`, `type_name`, `name`, `origin`, `dir1`, `dir2`.
- **FCMaterial**: `id`, `name`, `properties` (grouped dict). Helper: `add_property(group, name, values, type)`.
- **FCMaterialProperty**: `type`, `name`, `data: FCData`.
- **FCData**: constant/table/formula. Constructors: `FCData.constant(x)`, `FCData.formula("expr")`. Method: `remap_column(dep_type, mapping)`.
- **FCValue**: Base64 array/formula wrapper. `encode() -> str`, `decode(src, dtype)`. Methods: `remap(mapping)`, `remap_pairs(mapping)`.
- **FCLoad**: `id`, `name`, `type`, `cs_id`, `apply`, `data`.
- **FCRestraint**: `id`, `name`, `flags: List[str]`, `apply`, `data`, `step: Optional[List[int]]`.
- **FCInitialSet**: `id`, `name`, `type`, `flags: List[int]` (raw 0/1), `apply`, `data`.
- **FCConstraint**: `id`, `name`, `type`, `master: FCValue`, `slave: FCValue`, `properties: dict`.
- **FCPropertyTable**: `id`, `name`, `type`, `properties`.
- **FCReceiver**: `id`, `name`, `type`, `apply`, `dofs`, `output_step: Optional[int]`.
- **FCSet**: `id`, `name`, `apply`.

### Constants (all importable from fc_model)
- Materials: `FC_MATERIAL_PROPERTY_NAMES_KEYS/CODES`, `FC_MATERIAL_PROPERTY_TYPES_KEYS/CODES`.
- Loads/BC/IC: `FC_LOADS_TYPES_KEYS/CODES`, `FC_RESTRAINT_FLAGS_KEYS/CODES`, `FC_INITIAL_SET_TYPES_KEYS/CODES`.
- Mesh: `FC_ELEMENT_TYPES_KEYID/KEYNAME`.
- Dependencies: `FC_DEPENDENCY_TYPES_KEYS/CODES`.
- Property tables: `FC_PROPERTY_TABLE_TYPES_KEYS/CODES`, `FC_BEAM_SECTION_TYPES_KEYS/CODES`.
- Constraints: `FC_CONTACT_TYPES`, `FC_CONTACT_METHODS`, `FC_COUPLING_TYPES_KEYS/CODES`, `FC_PERIODIC_TYPES_KEYS/CODES`.
- Receivers: `FC_RECEIVER_TYPES_KEYS/CODES`.
- Coordinate systems: `FC_COORDINATE_SYSTEM_TYPES`.

### Invariants
- Use constants — never hardcode numeric codes.
- `settings` is a plain dict. Binary arrays are Base64 in JSON.
- `FCInitialSet.flags` = `List[int]` (0/1); `FCRestraint.flags` = `List[str]` (names).

### Minimal example
```python
from fc_model import FCModel, FCData
m = FCModel.load("in.fc")
mat = m.add_material("Steel")
mat.add_property("elasticity", "YOUNG_MODULE", 2.1e11, "HOOK")
mat.add_property("common", "DENSITY", 7850.0, "USUAL")
m.add_restraint(name="Fix", flags=["Displacement"]*3+["EmptyRestraint"]*3, apply_to="all", data=[FCData.constant(0.0)]*3)
m.save("out.fc")
```


