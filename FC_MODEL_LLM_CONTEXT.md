## LLM Context for the fc_model library (≥ 1.2)

fc_model is a strictly typed Python object model for the Fidesys Case (`.fc`) format.
Use only the public re-exports from the `fc_model` package root. Do not import from internal modules `fc_model.fc_*`.

---

### Versions and compatibility

- Current version: **1.2.0** (read from `VERSION`).
- Python: ≥ 3.8.
- Runtime dependency: `numpy ≥ 1.20`.
- PEP 561 (`py.typed`) — first-party types available to static analysis tools.
- Published on PyPI: [fc-model](https://pypi.org/project/fc-model/).

### Import rules

```python
# CORRECT — import from package root only
from fc_model import FCModel, FCMaterial, FCData, FC_LOADS_TYPES_KEYS

# WRONG — never import from internal modules
from fc_model.fc_materials import FCMaterial  # ✗
```

### Format overview

- `.fc` files are JSON with Base64-encoded binary arrays, UTF-8.
- Format version: 3.
- Top-level sections: `header`, `settings`, `mesh`, `blocks`, `coordinate_systems`, `materials`, `property_tables`, `loads`, `restraints`, `initial_sets`, `contact_constraints`, `coupling_constraints`, `periodic_constraints`, `receivers`, `sets`.

---

## Public API Reference

### FCModel — Root class

```python
class FCModel:
    header: FCHeader              # {"binary": True, "description": str, "version": 3, "types": {...}}
    settings: FCSettings          # dict — analysis settings (type, dimensions, solvers, etc.)
    mesh: FCMesh                  # Mesh container (nodes + elements)
    coordinate_systems: Dict[int, FCCoordinateSystem]
    blocks: Dict[int, FCBlock]
    materials: Dict[int, FCMaterial]
    property_tables: Dict[int, FCPropertyTable]
    loads: List[FCLoad]
    restraints: List[FCRestraint]
    initial_sets: List[FCInitialSet]
    contact_constraints: List[FCConstraint]
    coupling_constraints: List[FCConstraint]
    periodic_constraints: List[FCConstraint]
    receivers: List[FCReceiver]
    nodesets: Dict[int, FCSet]
    sidesets: Dict[int, FCSet]
```

**Constructor:**
```python
m = FCModel()  # Empty model with default header (version=3) and base coordinate system
```

**Class methods:**
```python
FCModel.load(path: str) -> FCModel          # Read .fc file, decode Base64 fields
FCModel.decode(data: FCSrcModel) -> FCModel  # Build from dict (already loaded JSON)
```

**Instance methods:**
```python
m.encode() -> FCSrcModel    # Serialize to JSON-ready dict (Base64 for binary)
m.save(path: str) -> None   # Write to .fc file
```

**Helper methods (auto-assign IDs):**
```python
m.add_coordinate_system(name: str, type_name: str = "cartesian") -> FCCoordinateSystem
m.add_material(name: str) -> FCMaterial
m.add_material_property(material_id, group_name, property_name, values, property_type=None) -> FCMaterialProperty
m.add_load(name, type, apply_to, *, cs_id=0, data=None) -> FCLoad
m.add_restraint(name, flags, apply_to, *, cs_id=0, data=None) -> FCRestraint
m.add_initial_set(type, apply_to, *, flags=None, cs_id=0, data=None) -> FCInitialSet
m.add_nodeset(name: str, apply_to: Sequence[int]) -> FCSet
m.add_sideset(name: str, apply_to: Sequence[int]) -> FCSet
```

**Index normalization:**
```python
m.compress() -> None  # Renumber all entity IDs to [1, 2, 3, ...], update all cross-references
```

**IMPORTANT:** `FCModel("path")` does NOT load a file. Use `FCModel.load("path")`.

---

### FCMesh — Mesh container

```python
class FCMesh:
    nodes_ids: NDArray[int32]       # Node IDs
    nodes_xyz: NDArray[float64]     # Node coordinates, shape (N, 3)
    elements: Dict[str, Dict[int, FCElement]]  # Type name → {elem_id → FCElement}
```

**Key methods:**
```python
mesh.decode(src: FCSrcMesh) -> None    # Populate from source dict (Base64 decode)
mesh.encode() -> FCSrcMesh             # Serialize (Base64 encode)
mesh.add(elem: FCElement) -> None      # Add element
mesh.compress() -> Dict[int, int]      # Renumber element IDs to [1,2,3,...], return old→new map
mesh.reindex(map: Dict[int,int]) -> None  # Apply custom ID mapping
mesh.max_id -> int                     # Highest element ID
mesh.nodes_list -> List[int]           # List of node IDs
len(mesh)                              # Number of elements
elem = mesh[id]                        # Get element by ID
mesh[id] = elem                        # Set element by ID
id in mesh                             # Check if element exists
for elem in mesh: ...                  # Iterate elements
```

### FCElement

```python
class FCElement:
    id: int
    type: FCElementTypeLiteral  # Element type name (e.g. "TETRA4", "HEX8")
    nodes: List[int]            # Node IDs forming the element
    parent_id: int              # Geometry parent ID (0 = no parent)
    block: int                  # Block ID
    order: int                  # SEM order (ignored for FEM)
```

### Element types

`FC_ELEMENT_TYPES` — list of `FCElementType` dicts with `id`, `name`, `nodes` count.

Lookup dicts:
- `FC_ELEMENT_TYPES_KEYID: Dict[int, FCElementType]` — by numeric ID
- `FC_ELEMENT_TYPES_KEYNAME: Dict[str, FCElementType]` — by name

**Solid FEM (3D/2D):** NONE(0), TETRA4(1), TETRA10(2), HEX8(3), HEX20(4), WEDGE6(6), WEDGE15(7), PYR5(8), PYR13(9), TRI3(10), TRI6(11), QUAD4(12), QUAD8(13).

**Solid SEM:** TETRA4S(15)–QUAD8S(27).

**Shell FEM/SEM:** MITC3(29), MITC4(31), MITC6(30), MITC8(32), SHELL3S(84), SHELL4S(85), SHELL6S(86), SHELL8S(87).

**Beam/Spring:** BEAM26(36), BEAM36(37), BEAM27(89), BEAM37(90), BEAM26S(95), BEAM36S(96), BEAM27S(97), BEAM37S(98), SPRING3D(39), SPRING6D(41), SPRING2D(83).

**Point/Lumpmass:** LUMPMASS3D(38), LUMPMASS6D(40), LUMPMASS2D(82), LUMPMASS2DR(105), POINT3D(99), POINT2D(100), POINT6D(101).

**Library extensions (beyond spec):** BAR2(42), BAR3(43), CABLE2(44), CABLE3(45).

---

### FCBlock

```python
class FCBlock:
    id: int
    cs_id: int          # Coordinate system ID
    material_id: int    # Material ID
    property_id: int    # Property table ID
    steps: Optional[List[int]]           # Active calculation steps
    material: Optional[Dict[str, Any]]   # Multi-step material assignment {"ids": [...], "steps": [...]}
```

---

### FCCoordinateSystem

```python
class FCCoordinateSystem:
    id: int
    type_name: str    # "cartesian" | "cylindrical" | "spherical"
    name: str
    origin: NDArray[float64]  # 3D origin point
    dir1: NDArray[float64]    # Direction vector 1
    dir2: NDArray[float64]    # Direction vector 2
```

`FC_COORDINATE_SYSTEM_TYPES: List[str]` = `["cartesian", "cylindrical", "spherical"]`

---

### FCMaterial and FCMaterialProperty

```python
class FCMaterial:
    id: int
    name: str
    properties: Dict[str, List[List[FCMaterialProperty]]]
    # Groups: "elasticity", "common", "thermal", "geomechanic",
    #         "plasticity", "hardening", "creep", "preload", "strength", "swelling"
```

**Helper method:**
```python
mat.add_property(
    group_name: str,        # "elasticity", "common", "thermal", etc.
    property_name: str,     # e.g. "YOUNG_MODULE", "DENSITY"
    values: Union[str, float, int, List],
    property_type: Optional[str] = None  # e.g. "HOOK", "USUAL"
) -> FCMaterialProperty
```

```python
class FCMaterialProperty:
    type: str     # Property type code name (e.g. "HOOK", "USUAL", "ISOTROPIC")
    name: str     # Property name (e.g. "YOUNG_MODULE", "DENSITY")
    data: FCData  # Value with dependency info
```

#### Material property constants

**Property names by group** — `FC_MATERIAL_PROPERTY_NAMES_KEYS: Dict[str, Dict[int, str]]`:
```
elasticity:  0=YOUNG_MODULE, 1=POISSON_RATIO, 2=SHEAR_MODULUS, 3=BULK_MODULUS,
             4=MU, 5=ALPHA, 6=BETA, 7=LAME_MODULE, 8..10=C3..C5,
             16..20=E_T/E_L/PR_T/PR_TL/G_TL, 21..26=G12/G23/G13/PRXY/PRYZ/PRXZ,
             27..29=C1/C2/D, 82..102=C_1111..C_3333
common:      0=DENSITY, 1=STRUCTURAL_DAMPING_RATIO, 2=MASS_DAMPING_RATIO, 3=STIFFNESS_DAMPING_RATIO
thermal:     0=COEF_LIN_EXPANSION, 1=COEF_THERMAL_CONDUCTIVITY, 5..20=orthotropic/transversal
geomechanic: 0=PERMEABILITY, 1=FLUID_VISCOSITY, 2=POROSITY, 3=FLUID_BULK_MODULUS, 4=SOLID_BULK_MODULUS, 5=BIOT_ALPHA, ...
plasticity:  0=YIELD_STRENGTH, 5=YIELD_STRENGTH_COMPR, 7=COHESION, 8=INTERNAL_FRICTION_ANGLE, 9=DILATANCY_ANGLE, 21..23=DPC_*
hardening:   1=TENSILE_STRAIN, 2=E_TAN, 3=HARDENING, 6=TENSILE_STRAIN_COMPR, 10=E_TAN_COMPR, 11=HARDENING_COMPR, 41=HARDENING_COHES
creep:       38=C1, 39=C2, 40=C3
preload:     0..48 = STRESS_*/STRAIN_*/PSI_*/GRADIENT_*/PLASTIC_STRAIN_*/FINGER_STRAIN_*/THERMAL_STRESS_*
strength:    0=TENSILE_STRENGTH, 1=TENSILE_STRENGTH_COMPR
```

**Property types by group** — `FC_MATERIAL_PROPERTY_TYPES_KEYS: Dict[str, Dict[int, str]]`:
```
elasticity:   0=HOOK, 1=HOOK_ORTHOTROPIC, 2=HOOK_TRANSVERSAL_ISOTROPIC, 3=BLATZ_KO, 4=MURNAGHAN, 11=COMPR_MOONEY, 20=NEO_HOOK, 21=ANISOTROPIC
common:       0=USUAL
thermal:      0=ISOTROPIC, 1=ORTHOTROPIC, 2=TRANSVERSAL_ISOTROPIC
geomechanic:  0=BIOT_ISOTROPIC, 1=BIOT_ORTHOTROPIC, 2=BIOT_TRANSVERSAL_ISOTROPIC
plasticity:   0=MISES, 1=DRUCKER_PRAGER, 4=DRUCKER_PRAGER_CREEP, 9=MOHR_COULOMB
hardening:    0=LINEAR, 1=MULTILINEAR
creep:        0=NORTON
preload:      0=INITIAL
strength:     0=ISOTROPIC
```

Inverse lookups: `FC_MATERIAL_PROPERTY_NAMES_CODES`, `FC_MATERIAL_PROPERTY_TYPES_CODES` (name→code).

---

### FCData — Dependency representation

```python
class FCData:
    type: Union[int, str]  # 0=CONSTANT, 6=FORMULA, -1=TABLE
    value: FCValue         # The data payload
    table: List[FCDependencyColumn]  # Dependency columns (for tabular data)
```

**Constructors:**
```python
FCData.constant(1000.0)            # Single constant value
FCData.constant([1.0, 2.0, 3.0])   # Array of constants
FCData.formula("x*10+y")           # Formula expression
```

**Reindexing tabular columns:**
```python
data.remap_column("TABULAR_NODE_ID", node_map)      # Remap node IDs in tabular dependency
data.remap_column("TABULAR_ELEMENT_ID", elem_map)    # Remap element IDs in tabular dependency
```

**Dependency types** — `FC_DEPENDENCY_TYPES_KEYS: Dict[int, str]`:
```
0=CONSTANT, 1=TABULAR_X, 2=TABULAR_Y, 3=TABULAR_Z, 4=TABULAR_TIME,
5=TABULAR_TEMPERATURE, 6=FORMULA, 7=TABULAR_FREQUENCY, 8=TABULAR_STRAIN,
10=TABULAR_ELEMENT_ID, 11=TABULAR_NODE_ID, 12=TABULAR_MODE_ID
```

### FCDependencyColumn

```python
class FCDependencyColumn:
    type: str       # Dependency type name (from FC_DEPENDENCY_TYPES_KEYS)
    value: FCValue  # Column data
```

### FCValue — Base64 wrapper

```python
class FCValue:
    type: Literal['formula', 'array', 'null']
    data: Union[NDArray, str]

    @classmethod
    def decode(cls, src_data, dtype=int32, value_type='array') -> FCValue
    def encode(self) -> str            # Base64 string or formula string
    def reshape(self, size: int) -> None
    def remap(self, mapping: dict[int, int]) -> None    # Remap all values via mapping; skips formula/null
    def remap_pairs(self, mapping: dict[int, int]) -> None  # Remap first element of each [id, extra] pair
    len(v)  # Array length (0 for formula/null)
```

---

### FCLoad — Loads

```python
class FCLoad:
    id: int
    name: str
    type: str          # Load type name (from FC_LOADS_TYPES_KEYS)
    cs_id: int         # Coordinate system ID
    apply: FCValue     # Target nodes/faces/elements or "all"
    data: List[FCData] # Component values
```

**Load types** — `FC_LOADS_TYPES_KEYS: Dict[int, str]`:
```
Face loads:    1=FaceDeadStress, 3=FaceTrackingStress, 11=FaceHeatFlux, 13=FaceConvection,
               15=FaceRadiation, 19=FaceAbsorbingBC, 21=ShellHeatfluxTopBottom,
               22=ShellHeatfluxTop, 23=ShellHeatfluxBottom, 24=ShellConvectionTopBottom,
               25=ShellConvectionTop, 26=ShellConvectionBottom,
               35=FaceDistributedForce, 36=FaceEquivalentForce,
               37=FaceTrackingDistributedForce, 38=FaceTrackingEquivalentForce, 39=FaceFluidFlux
Segment loads: 2=SegmentDeadStress, 4=SegmentTrackingStress, 12=SegmentHeatFlux, 14=SegmentConvection,
               16=SegmentRadiation, 20=SegmentAbsorbingBC, 31=SegmentDistributedForce,
               32=SegmentEquivalentForce, 33=SegmentTrackingDistributedForce,
               34=SegmentTrackingEquivalentForce, 40=SegmentFluidFlux
Node loads:    5=NodeForce, 18=HeatSource, 28=NodeHeatFlux, 29=NodeConvection,
               30=NodeRadiation, 41=NodeFluidFlux, 43=FluidSource
Volume loads:  17=VolumeHeatSource, 42=VolumeFluidSource, 44=VolumeGravityMassForce
```

### FCRestraint — Boundary conditions

```python
class FCRestraint:
    id: int
    name: str
    flags: List[str]         # Flag names (from FC_RESTRAINT_FLAGS_KEYS values)
    cs_id: int
    apply: FCValue
    data: List[FCData]
    step: Optional[List[int]]  # Active steps (None = all steps)
```

**Restraint flags** — `FC_RESTRAINT_FLAGS_KEYS: Dict[int, str]`:
```
0=EmptyRestraint, 1=Displacement, 2=Velocity, 3=Temperature, 4=TemperatureTop,
5=TemperatureBottom, 6=TemperatureMiddle, 7=TemperatureGradient, 9=Acceleration,
10=PorePressure, 12=DirectionDisplacement, 13=DirectionVelocity,
14=DirectionAcceleration, 15=VolumeAngularVelocity
```

The `flags` field is a list of flag names (strings). The `data` list provides values for each active flag component.

### FCInitialSet — Initial conditions

```python
class FCInitialSet:
    id: int
    name: str
    type: str          # Type name (from FC_INITIAL_SET_TYPES_KEYS)
    flags: List[int]   # 0/1 flags per component (NOT mapped through restraint codes)
    cs_id: int
    apply: FCValue
    data: List[FCData]
```

**Initial set types** — `FC_INITIAL_SET_TYPES_KEYS: Dict[int, str]`:
```
0=Displacement, 1=Velocity, 2=AngularVelocity, 3=Temperature, 4=PorePressure
```

**IMPORTANT:** `FCInitialSet.flags` stores raw `List[int]` (0/1 values), NOT string names like FCRestraint.flags.

---

### FCConstraint — Contact / Coupling / Periodic constraints

```python
class FCConstraint:
    id: int
    name: str
    type: Union[int, str]
    master: FCValue     # Master surface node IDs
    slave: FCValue      # Slave surface node IDs
    properties: Dict[str, Any]  # Additional type-dependent properties
```

**Contact types** — `FC_CONTACT_TYPES: List[str]` = `["general", "tied", "tied_normal", "tied_tangent"]`
**Contact methods** — `FC_CONTACT_METHODS: List[str]` = `["auto", "penalty", "mpc"]`

**Coupling types** — `FC_COUPLING_TYPES_KEYS: Dict[int, str]`:
```
0=ELASTICITY, 1=TEMPERATURE, 2=DISTANCE, 3=PORE_PRESSURE, 4=DIRECTION, 5=INTERPOLATION
```

**Periodic types** — `FC_PERIODIC_TYPES_KEYS: Dict[int, str]`:
```
0=ALL, 1=DISPLACEMENT, 2=THERMAL_CONDUCTION, 3=PORE_PRESSURE_CONDUCTION, 4=VELOCITY, 5=ACCELERATION
```

---

### FCPropertyTable — Property tables

```python
class FCPropertyTable:
    id: int
    name: str            # Optional description (empty string if not set)
    type: str            # Type name (from FC_PROPERTY_TABLE_TYPES_KEYS)
    properties: dict     # Type-dependent properties dict
```

**Property table types** — `FC_PROPERTY_TABLE_TYPES_KEYS: Dict[int, str]`:
```
0=SHELL, 1=BEAM, 5=LUMPMASS, 6=SPRING
```

**Beam section types** — `FC_BEAM_SECTION_TYPES_KEYS: Dict[int, str]`:
```
0=RECTANGLE, 1=ELLIPSE, 2=I_BEAM, 3=CIRCLE_WITH_A_CUT, 4=POINT,
5=C_BEAM, 6=L_BEAM, 7=Z_BEAM, 8=T_BEAM, 9=RECTANGLE_WITH_A_CUT, 10=HAT_BEAM, 12=PIPE
```

### FCReceiver — Result receivers

```python
class FCReceiver:
    id: int
    name: str
    type: str           # Type name (from FC_RECEIVER_TYPES_KEYS)
    apply: FCValue      # Node IDs
    dofs: List[int]     # Degrees of freedom
    output_step: Optional[int]  # Save every N steps (None = every step)
```

**Receiver types** — `FC_RECEIVER_TYPES_KEYS: Dict[int, str]`:
```
0=DISPLACEMENT, 1=VELOCITY, 2=PRINCIPAL_STRESS, 3=PRESSURE, 4=ACCELERATION
```

### FCSet — Node/side sets

```python
class FCSet:
    id: int
    name: str
    apply: FCValue  # Node IDs (nodesets) or [elem_id, face_id] pairs (sidesets)
```

---

## Settings reference

`FCModel.settings` is a plain dict. Key fields:

```python
settings = {
    "type": str,          # "static"|"dynamic"|"eigenfrequencies"|"buckling"|"spectrum"|"harmonic"|"effectiveprops"
    "dimensions": str,    # "2D"|"3D"
    "plane_state": str,   # "p-stress"|"p-strain"|"axisym_x"|"axisym_y" (for 2D)
    # Boolean toggles:
    "elasticity": bool, "plasticity": bool, "heat_transfer": bool,
    "finite_deformations": bool, "incompressibility": bool, "preload": bool,
    "lumpmass": bool, "porefluid_transfer": bool, "slm": bool,
    "radiation_among_surfaces": bool, "periodic_bc": bool,
    "permission_write": bool,
    # Solver sub-dicts:
    "linear_solver": {...}, "nonlinear_solver": {...}, "eigen_solver": {...},
    "damping": {...}, "thermal_gap_settings": {...},
    "statics": {...}, "dynamics": {...}, "harmonic": {...},
    "output": {...}, "test_opts": {...}
}
```

See `docs/FidesysCase.md` for the full specification of each solver sub-section.

---

## All public constants summary

| Constant | Type | Purpose |
|----------|------|---------|
| `FC_MATERIAL_PROPERTY_NAMES_KEYS` | `Dict[str, Dict[int, str]]` | Property name codes by group |
| `FC_MATERIAL_PROPERTY_NAMES_CODES` | `Dict[str, Dict[str, int]]` | Inverse of above |
| `FC_MATERIAL_PROPERTY_TYPES_KEYS` | `Dict[str, Dict[int, str]]` | Property type codes by group |
| `FC_MATERIAL_PROPERTY_TYPES_CODES` | `Dict[str, Dict[str, int]]` | Inverse of above |
| `FC_LOADS_TYPES_KEYS` | `Dict[int, str]` | Load type code → name |
| `FC_LOADS_TYPES_CODES` | `Dict[str, int]` | Load type name → code |
| `FC_RESTRAINT_FLAGS_KEYS` | `Dict[int, str]` | Restraint flag code → name |
| `FC_RESTRAINT_FLAGS_CODES` | `Dict[str, int]` | Restraint flag name → code |
| `FC_INITIAL_SET_TYPES_KEYS` | `Dict[int, str]` | Initial set type code → name |
| `FC_INITIAL_SET_TYPES_CODES` | `Dict[str, int]` | Initial set type name → code |
| `FC_ELEMENT_TYPES_KEYID` | `Dict[int, FCElementType]` | Element by numeric ID |
| `FC_ELEMENT_TYPES_KEYNAME` | `Dict[str, FCElementType]` | Element by name |
| `FC_DEPENDENCY_TYPES_KEYS` | `Dict[int, str]` | Dependency type code → name |
| `FC_DEPENDENCY_TYPES_CODES` | `Dict[str, int]` | Dependency type name → code |
| `FC_PROPERTY_TABLE_TYPES_KEYS` | `Dict[int, str]` | Property table type code → name |
| `FC_PROPERTY_TABLE_TYPES_CODES` | `Dict[str, int]` | Inverse |
| `FC_BEAM_SECTION_TYPES_KEYS` | `Dict[int, str]` | Beam section code → name |
| `FC_BEAM_SECTION_TYPES_CODES` | `Dict[str, int]` | Inverse |
| `FC_CONTACT_TYPES` | `List[str]` | Contact constraint type names |
| `FC_CONTACT_METHODS` | `List[str]` | Contact methods |
| `FC_COUPLING_TYPES_KEYS` | `Dict[int, str]` | Coupling type code → name |
| `FC_COUPLING_TYPES_CODES` | `Dict[str, int]` | Inverse |
| `FC_PERIODIC_TYPES_KEYS` | `Dict[int, str]` | Periodic BC code → name |
| `FC_PERIODIC_TYPES_CODES` | `Dict[str, int]` | Inverse |
| `FC_RECEIVER_TYPES_KEYS` | `Dict[int, str]` | Receiver type code → name |
| `FC_RECEIVER_TYPES_CODES` | `Dict[str, int]` | Inverse |
| `FC_COORDINATE_SYSTEM_TYPES` | `List[str]` | CS type names |

---

## Common recipes

### Load and save
```python
from fc_model import FCModel
m = FCModel.load("case.fc")
m.save("out.fc")
```

### Create a model from scratch
```python
from fc_model import FCModel, FCData, FCElement, FCBlock
import numpy as np

m = FCModel()

# Add nodes
m.mesh.nodes_ids = np.array([1, 2, 3, 4], dtype=np.int32)
m.mesh.nodes_xyz = np.array([
    [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
], dtype=np.float64)

# Add element
m.mesh.add(FCElement({
    'id': 1, 'type': 'TETRA4', 'nodes': [1, 2, 3, 4],
    'parent_id': 0, 'block': 1, 'order': 1
}))

# Add block
m.blocks[1] = FCBlock(id=1, cs_id=1, material_id=1, property_id=0)

# Add material
mat = m.add_material("Steel")
mat.add_property("elasticity", "YOUNG_MODULE", 2.1e11, "HOOK")
mat.add_property("elasticity", "POISSON_RATIO", 0.3, "HOOK")
mat.add_property("common", "DENSITY", 7850.0, "USUAL")

# Add load
m.add_load(name="Pressure", type="FaceDeadStress", apply_to="all", data=[FCData.constant(1e6)])

# Add restraint
m.add_restraint(
    name="Fix", flags=["Displacement"]*3 + ["EmptyRestraint"]*3,
    apply_to=[1, 2], data=[FCData.constant(0.0)]*3
)

m.save("output.fc")
```

### Modify existing material
```python
mat = m.materials[1]
mat.add_property("thermal", "COEF_LIN_EXPANSION", 1.2e-5, "ISOTROPIC")
```

### Add initial conditions
```python
m.add_initial_set(type="Temperature", apply_to="all", flags=[1], data=[FCData.constant(293.15)])
```

### Access mesh
```python
print(f"Nodes: {len(m.mesh.nodes_ids)}, Elements: {len(m.mesh)}")
for elem in m.mesh:
    print(elem.id, elem.type, elem.nodes)
```

### Encode without saving to file
```python
data = m.encode()  # Returns serializable dict
import json
json_str = json.dumps(data, indent=2)
```

### Normalize IDs (compress)
```python
m = FCModel.load("messy_ids.fc")
m.compress()   # All entity IDs become [1, 2, 3, ...]; all cross-references updated
m.save("clean.fc")
```

### Configure analysis settings
```python
m.settings = {
    "type": "static",
    "dimensions": "3D",
    "elasticity": True,
    "plasticity": False,
    "nonlinear_solver": {"max_iterations": 25, "tolerance": 1e-6}
}
```

---

## Anti-patterns (avoid)

| Don't | Do instead |
|-------|-----------|
| `FCModel("path")` | `FCModel.load("path")` |
| `from fc_model.fc_materials import ...` | `from fc_model import ...` |
| Hardcode type codes: `load.type = 1` | Use constant names: `load.type = "FaceDeadStress"` |
| Manually build Base64 strings | Use `FCValue`, `FCData.constant()`, `FCData.formula()` |
| Modify `encode()` output and re-decode | Modify the object model directly, then `encode()` |

---

## Library extensions beyond spec

These types are present in the library but not in `docs/FidesysCase.md`:
- Element types: `BAR2`(42), `BAR3`(43), `CABLE2`(44), `CABLE3`(45)
- Material property types: `VOIGT_ISOTROPIC`, `VOIGT_ORTHOTROPIC`, `VP`, `VS`
- Material group: `swelling`

They are valid extensions and work correctly with encode/decode.

---

## Where to look for implementation details

- Entry point: `src/fc_model/__init__.py` — all public classes, constants, `__all__`.
- Domain modules: `fc_mesh.py`, `fc_materials.py`, `fc_data.py`, `fc_value.py`, `fc_blocks.py`, `fc_conditions.py`, `fc_constraint.py`, `fc_property_tables.py`, `fc_set.py`, `fc_receivers.py`, `fc_coordinate_system.py`.
- Specification: `docs/FidesysCase.md`.
- Tests: `tests/` directory — unit tests and roundtrip tests with real `.fc` files.

## Ready-to-use context block for LLM prompts

```text
Context:
- Library: fc_model (>=1.2). Strictly typed Python model of Fidesys Case (.fc) format.
- Import only from `fc_model` root. Never from `fc_model.fc_*` internals.
- Key classes: FCModel, FCMesh, FCBlock, FCCoordinateSystem, FCConstraint, FCMaterial,
  FCPropertyTable, FCLoad, FCRestraint, FCInitialSet, FCReceiver, FCSet, FCValue, FCData.
- Constants: FC_MATERIAL_PROPERTY_*, FC_LOADS_TYPES_*, FC_RESTRAINT_FLAGS_*, FC_ELEMENT_TYPES_*, FC_DEPENDENCY_TYPES_*.
- Pattern: m = FCModel.load("in.fc"); modify; m.save("out.fc")
- Helpers: m.add_material(), mat.add_property(), m.add_load(), m.add_restraint(), FCData.constant/formula, m.compress()
- Settings is a plain dict. Binary arrays encoded as Base64.
Task: [describe what to do]
```
