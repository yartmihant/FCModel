# FC Input File (.fc) Structure

This document describes the JSON structure consumed by `Core/Kernel/FCParser.cpp`.

## Overview

- File extension: `.fc`
- Encoding: UTF-8
- Container format: JSON
- Binary mode support: arrays can be stored as Base64-encoded binary blobs when `header.binary = true`

---

## Top-level fields

The parser reads the following top-level fields (some are optional):

```json
{
  "header":               {},  // Format version, binary mode flag, sizeof() map
  "mesh":                 {},  // Nodes, elements, connectivity, element types
  "materials":            [],  // Material records (elasticity, plasticity, thermal, ...)
  "property_tables":      [],  // Section properties: SHELL, BEAM, SPRING, LUMPMASS
  "coordinate_systems":   [],  // User-defined coordinate systems (Cartesian/cylindrical/spherical)
  "sets":                 {},  // Named node sets and side sets for BC application
  "blocks":               [],  // Element blocks with material/property/CS assignments
  "loads":                [],  // Applied loads (forces, pressures, heat fluxes, ...)
  "restraints":           [],  // Boundary conditions (displacements, temperatures, ...)
  "initial_sets":         [],  // Initial conditions (velocity, temperature, ...)
  "coupling_constraints": [],  // Multipoint constraints (RBE2/RBE3, equations, ...)
  "contact_constraints":  [],  // Contact pairs (general, tied, friction, ...)
  "periodic_constraints": [],  // Periodic/cyclic symmetry boundary conditions
  "receivers":            [],  // Output sensor nodes (displacement, velocity, pressure)
  "settings":             {},  // Analysis type, solver options, output settings
  "orientations":         [],  // Element material orientation definitions
  "imported_sections":    []   // Externally imported beam cross-sections
}
```

## header

```json
{
  "description": "<string>",          // Human-readable description of the file (informational only)
  "version":     "<unsigned short>",  // Format version: 3 = current grouped-property layout; older = legacy constants layout
  "binary":      "<bool>",            // true = array fields are Base64-encoded binary blobs; false = plain JSON arrays
  "types": {                          // sizeof() values for binary decoding; must match the serialized buffer layout
    "char":      1,                   // sizeof(char)
    "short_int": 2,                   // sizeof(short int)
    "int":       4,                   // sizeof(int)
    "double":    8,                   // sizeof(double)
    "FCTYPE":    8                    // sizeof(FCTYPE) — the floating-point precision used throughout (normally double)
  }
}
```

## mesh

```json
{
  "nodes_count":    "<int>",           // Total number of nodes
  "nids":           "<Base64 [int]>",  // Node IDs (1-based, size = nodes_count)
  "nodes":          "<Base64 [double]>", // Node coordinates flat array [x0,y0,z0, x1,y1,z1, ...] (size = nodes_count*3)
  "elems_count":    "<int>",           // Total number of elements
  "elemids":        "<Base64 [int]>",  // Element IDs (1-based, size = elems_count)
  "elem_types":     "<Base64 [int]>",  // Element type codes per element (see elem_types table, size = elems_count)
  "elem_blocks":    "<Base64 [int]>",  // Block ID each element belongs to (size = elems_count)
  "elem_orders":    "<Base64 [int]>",  // Spectral polynomial order per element; relevant for SEM workflows (size = elems_count)
  "elem_parent_ids":"<Base64 [int]>",  // Parent element IDs for sub-element hierarchies (size = elems_count)
  "elems":          "<Base64 [int]>"   // Element connectivity: node indices per element, packed (variable length per type)
}
```

Notes:
- In binary mode (`header.binary = true`), all array fields are Base64-encoded according to `header.types`.
- `elem_orders` is relevant for SEM/high-order workflows.

### elem_types

**Solid FEM elements (3D and 2D)**

| Code | Name |
|------|------|
| 0 | NONE |
| 1 | TETRA4 |
| 2 | TETRA10 |
| 3 | HEX8 |
| 4 | HEX20 |
| 6 | WEDGE6 |
| 7 | WEDGE15 |
| 8 | PYR5 |
| 9 | PYR13 |
| 10 | TRI3 |
| 11 | TRI6 |
| 12 | QUAD4 |
| 13 | QUAD8 |

**Solid SEM elements (3D and 2D)**

| Code | Name |
|------|------|
| 15 | TETRA4S |
| 16 | TETRA10S |
| 17 | HEX8S |
| 18 | HEX20S |
| 20 | WEDGE6S |
| 21 | WEDGE15S |
| 22 | PYR5S |
| 23 | PYR13S |
| 24 | TRI3S |
| 25 | TRI6S |
| 26 | QUAD4S |
| 27 | QUAD8S |

**Shell FEM and SEM elements**

| Code | Name |
|------|------|
| 29 | MITC3 |
| 30 | MITC6 |
| 31 | MITC4 |
| 32 | MITC8 |
| 84 | SHELL3S |
| 85 | SHELL4S |
| 86 | SHELL6S |
| 87 | SHELL8S |

**Beam FEM and SEM elements, springs**

| Code | Name |
|------|------|
| 36 | BEAM26 |
| 37 | BEAM36 |
| 39 | SPRING3D |
| 41 | SPRING6D |
| 83 | SPRING2D |
| 89 | BEAM27 |
| 90 | BEAM37 |
| 95 | BEAM26S |
| 96 | BEAM36S |
| 97 | BEAM27S |
| 98 | BEAM37S |

**Point masses and points**

| Code | Name |
|------|------|
| 38 | LUMPMASS3D |
| 40 | LUMPMASS6D |
| 82 | LUMPMASS2D |
| 99 | POINT3D |
| 100 | POINT2D |
| 101 | POINT6D |
| 105 | LUMPMASS2DR |

## materials

Parser supports:
- Legacy constants layout (`materials[i].constants.*`)
- Grouped property layout (v3): `elasticity`, `plasticity`, `hardening`, `kinematic_hardening`, `creep`, `thermal`, `common`, `geomechanic`, `preload`, `strength`, `swelling`, `hsdf`

Common material record shape:

```json
{
  "id":   "<int>",     // Material ID (referenced by blocks)
  "name": "<string>",  // Material name
  // Property groups — only the needed groups must be present; not all combinations are valid
  "elasticity":         [], // Elasticity / viscoelasticity group
  "common":             [], // Common properties (density, damping ratios)
  "thermal":            [], // Thermal properties
  "geomechanic":        [], // Geomechanics / Biot poroelasticity
  "plasticity":         [], // Plasticity
  "hardening":          [], // Hardening
  "kinematic_hardening": [], // Kinematic hardening
  "creep":              [], // Creep (Norton)
  "preload":            [], // Initial stress/strain state
  "strength":           [], // Strength criteria
  "swelling":           [], // Swelling
  "hsdf":               []  // HSDF group
}
```

Each group is an array of one element. The element shape:

```json
{
  "type":          "<int>",          // Group sub-type (see type tables below)
  "const_names":   "[int]",          // Property index array (see const_names tables below)
  "const_types":   "[[int]]",        // Dependency type per property (inner array for multi-dim; see const_types)
  "const_dep_size":"[int]",          // Number of argument rows per property (0 for CONSTANT/FORMULA)
  "constants":     "[Base64|string]",// Property values: Base64 array for TABULAR_*, formula string for FORMULA
  "const_dep":     "[Base64]",       // Tabular argument values (Base64 per property); empty string for CONSTANT/FORMULA
}
```

Notes:
- `const_types` inner arrays allow multi-dimensional tabular dependencies.
- Parser validates compatibility between analysis type and material groups.

### const_types

| Value | Name |
|-------|------|
| 0 | CONSTANT |
| 1 | TABULAR_X |
| 2 | TABULAR_Y |
| 3 | TABULAR_Z |
| 4 | TABULAR_TIME |
| 5 | TABULAR_TEMPERATURE |
| 6 | FORMULA |
| 7 | TABULAR_FREQUENCY |
| 8 | TABULAR_STRAIN |
| 10 | TABULAR_ELEMENT_ID |
| 11 | TABULAR_NODE_ID |
| 12 | TABULAR_MODE_ID |

### type values per group

**elasticity**

| Value | Name |
|-------|------|
| 0 | HOOK |
| 1 | HOOK_ORTHOTROPIC |
| 2 | HOOK_TRANSVERSAL_ISOTROPIC |
| 3 | BLATZ_KO |
| 4 | MURNAGHAN |
| 11 | COMPR_MOONEY |
| 20 | NEO_HOOK |
| 21 | ANISOTROPIC |

**common**: `0 = USUAL`

**thermal**

| Value | Name |
|-------|------|
| 0 | ISOTROPIC |
| 1 | ORTHOTROPIC |
| 2 | TRANSVERSAL_ISOTROPIC |

**geomechanic**

| Value | Name |
|-------|------|
| 0 | BIOT_ISOTROPIC |
| 1 | BIOT_ORTHOTROPIC |
| 2 | BIOT_TRANSVERSAL_ISOTROPIC |

**plasticity**

| Value | Name |
|-------|------|
| 0 | MISES |
| 1 | DRUCKER_PRAGER |
| 4 | DRUCKER_PRAGER_CREEP |
| 9 | MOHR_COULOMB |

**hardening**: `0 = LINEAR`, `1 = MULTILINEAR`

**creep**: `0 = NORTON`

**preload**: `0 = INITIAL`

**strength**: `0 = ISOTROPIC`

### const_names

**elasticity**

| Index | Name | Used in |
|-------|------|---------|
| 0 | YOUNG_MODULE | HOOK |
| 1 | POISSON_RATIO | HOOK |
| 2 | SHEAR_MODULUS | HOOK, MURNAGHAN |
| 3 | BULK_MODULUS | HOOK, MURNAGHAN |
| 4 | MU | BLATZ_KO |
| 5 | ALPHA | BLATZ_KO |
| 6 | BETA | BLATZ_KO |
| 7 | LAME_MODULE | MURNAGHAN |
| 8 | C3 | MURNAGHAN |
| 9 | C4 | MURNAGHAN |
| 10 | C5 | MURNAGHAN |
| 16 | E_T | HOOK_TRANSVERSAL_ISOTROPIC |
| 17 | E_L | HOOK_TRANSVERSAL_ISOTROPIC |
| 18 | PR_T | HOOK_TRANSVERSAL_ISOTROPIC |
| 19 | PR_TL | HOOK_TRANSVERSAL_ISOTROPIC |
| 20 | G_TL | HOOK_TRANSVERSAL_ISOTROPIC |
| 21 | G12 | HOOK_ORTHOTROPIC |
| 22 | G23 | HOOK_ORTHOTROPIC |
| 23 | G13 | HOOK_ORTHOTROPIC |
| 24 | PRXY | HOOK_ORTHOTROPIC |
| 25 | PRYZ | HOOK_ORTHOTROPIC |
| 26 | PRXZ | HOOK_ORTHOTROPIC |
| 27 | C1 | COMPR_MOONEY |
| 28 | C2 | COMPR_MOONEY |
| 29 | D | COMPR_MOONEY |
| 82 | C_1111 | ANISOTROPIC |
| 83 | C_1112 | ANISOTROPIC |
| 84 | C_1113 | ANISOTROPIC |
| 85 | C_1122 | ANISOTROPIC |
| 86 | C_1123 | ANISOTROPIC |
| 87 | C_1133 | ANISOTROPIC |
| 88 | C_1212 | ANISOTROPIC |
| 89 | C_1213 | ANISOTROPIC |
| 90 | C_1222 | ANISOTROPIC |
| 91 | C_1223 | ANISOTROPIC |
| 92 | C_1233 | ANISOTROPIC |
| 93 | C_1313 | ANISOTROPIC |
| 94 | C_1322 | ANISOTROPIC |
| 95 | C_1323 | ANISOTROPIC |
| 96 | C_1333 | ANISOTROPIC |
| 97 | C_2222 | ANISOTROPIC |
| 98 | C_2223 | ANISOTROPIC |
| 99 | C_2233 | ANISOTROPIC |
| 100 | C_2323 | ANISOTROPIC |
| 101 | C_2333 | ANISOTROPIC |
| 102 | C_3333 | ANISOTROPIC |

**common (USUAL)**

| Index | Name |
|-------|------|
| 0 | DENSITY |
| 1 | STRUCTURAL_DAMPING_RATIO |
| 2 | MASS_DAMPING_RATIO |
| 3 | STIFFNESS_DAMPING_RATIO |

**thermal**

| Index | Name | Used in |
|-------|------|---------|
| 0 | COEF_LIN_EXPANSION | ISOTROPIC |
| 1 | COEF_THERMAL_CONDUCTIVITY | ISOTROPIC |
| 2 | COEF_SPECIFIC_HEAT | ISOTROPIC |
| 3 | EMISSIVITY | ISOTROPIC |
| 5 | COEF_THERMAL_CONDUCTIVITY_XX | ORTHOTROPIC |
| 9 | COEF_THERMAL_CONDUCTIVITY_YY | ORTHOTROPIC |
| 13 | COEF_THERMAL_CONDUCTIVITY_ZZ | ORTHOTROPIC |
| 14 | COEF_LIN_EXPANSION_X | ORTHOTROPIC |
| 15 | COEF_LIN_EXPANSION_Y | ORTHOTROPIC |
| 16 | COEF_LIN_EXPANSION_Z | ORTHOTROPIC |
| 17 | COEF_THERMAL_CONDUCTIVITY_T | TRANSVERSAL_ISOTROPIC |
| 18 | COEF_THERMAL_CONDUCTIVITY_L | TRANSVERSAL_ISOTROPIC |
| 19 | COEF_LIN_EXPANSION_T | TRANSVERSAL_ISOTROPIC |
| 20 | COEF_LIN_EXPANSION_L | TRANSVERSAL_ISOTROPIC |

**geomechanic**

| Index | Name | Used in |
|-------|------|---------|
| 0 | PERMEABILITY | BIOT_ISOTROPIC |
| 1 | FLUID_VISCOSITY | all |
| 2 | POROSITY | all |
| 3 | FLUID_BULK_MODULUS | all |
| 4 | SOLID_BULK_MODULUS | all |
| 5 | BIOT_ALPHA | BIOT_ISOTROPIC |
| 6 | PERMEABILITY_XX | BIOT_ORTHOTROPIC |
| 7 | PERMEABILITY_XY | BIOT_ORTHOTROPIC |
| 8 | PERMEABILITY_XZ | BIOT_ORTHOTROPIC |
| 15 | PERMEABILITY_T | BIOT_TRANSVERSAL_ISOTROPIC |
| 16 | PERMEABILITY_TT | BIOT_TRANSVERSAL_ISOTROPIC |
| 19 | FLUID_DENSITY | all |
| 20 | BIOT_MODULUS | all |
| 21 | BIOT_ALPHA_X | BIOT_ORTHOTROPIC |
| 22 | BIOT_ALPHA_Y | BIOT_ORTHOTROPIC |
| 23 | BIOT_ALPHA_Z | BIOT_ORTHOTROPIC |
| 24 | BIOT_ALPHA_T | BIOT_TRANSVERSAL_ISOTROPIC |
| 25 | BIOT_ALPHA_L | BIOT_TRANSVERSAL_ISOTROPIC |

**plasticity**

| Index | Name | Used in |
|-------|------|---------|
| 0 | YIELD_STRENGTH | MISES |
| 1 | TENSILE_STRAIN | MISES |
| 5 | YIELD_STRENGTH_COMPR | DRUCKER_PRAGER, MOHR_COULOMB |
| 6 | TENSILE_STRAIN_COMPR | DRUCKER_PRAGER, MOHR_COULOMB |
| 7 | COHESION | DRUCKER_PRAGER, MOHR_COULOMB |
| 8 | INTERNAL_FRICTION_ANGLE | DRUCKER_PRAGER, MOHR_COULOMB |
| 9 | DILATANCY_ANGLE | DRUCKER_PRAGER, MOHR_COULOMB |
| 21 | DPC_A | DRUCKER_PRAGER_CREEP |
| 22 | DPC_B | DRUCKER_PRAGER_CREEP |
| 23 | DPC_M | DRUCKER_PRAGER_CREEP |

**hardening**

| Index | Name | Used in |
|-------|------|---------|
| 1 | TENSILE_STRAIN | LINEAR |
| 2 | E_TAN | LINEAR |
| 3 | HARDENING | MULTILINEAR |
| 6 | TENSILE_STRAIN_COMPR | LINEAR |
| 10 | E_TAN_COMPR | LINEAR |
| 41 | HARDENING_COHES | MULTILINEAR |

**creep (NORTON)**

| Index | Name |
|-------|------|
| 38 | C1 |
| 39 | C2 |
| 40 | C3 |

**preload (INITIAL)**

| Index | Name |
|-------|------|
| 0 | STRESS_XX |
| 1 | STRESS_YY |
| 2 | STRESS_ZZ |
| 3 | STRESS_XY |
| 4 | STRESS_YZ |
| 5 | STRESS_XZ |
| 46 | THERMAL_STRESS_XY |
| 47 | THERMAL_STRESS_YZ |
| 48 | THERMAL_STRESS_XZ |

**strength (ISOTROPIC)**

| Index | Name |
|-------|------|
| 0 | TENSILE_STRENGTH |
| 1 | TENSILE_STRENGTH_COMPR |

## property_tables

```json
[
  {
    "id":               "<unsigned short>", // Property table ID (referenced by blocks)
    "name":             "<string>",         // Descriptive name
    "type":             "<int>",            // Property table type (see type table below)
    "direction_normal": "<bool>",           // Shell layer direction: true = along normal, false = against normal
    "thickness_change": "<bool>",           // Enable thickness change for shell in SEM
    "properties":       {...},              // Type-specific properties (see properties by type below)
    "layers": [                             // Multi-layer shell definition (type = SHELL only)
      {
        "t":           "<double>",          // Layer thickness
        "angle":       "<double>",          // Layer orientation angle relative to element local CS [deg]
        "material_id": "<int>"              // Material ID for this layer
      }
    ]
  }
]
```

### type

| Value | Name |
|-------|------|
| 0 | SHELL |
| 1 | BEAM |
| 5 | LUMPMASS |
| 6 | SPRING |

### properties by type

**SHELL**

```json
{
  "e": "<double>"  // Eccentricity: position of the given geometry relative to mid-surface.
                   // 0.0 = bottom surface, 0.5 = mid-surface (default), 1.0 = top surface
}
```

**LUMPMASS**

```json
{
  "mass":           "<double>",  // Total mass (mutually exclusive with mass_x/mass_y/mass_z)
  "mass_x":         "<double>",  // Mass distributed along X axis
  "mass_y":         "<double>",  // Mass distributed along Y axis
  "mass_z":         "<double>",  // Mass distributed along Z axis
  "mass_inertia":   "<double>",  // Total moment of inertia (mutually exclusive with per-axis set)
  "mass_inertia_x": "<double>",  // Moment of inertia about X
  "mass_inertia_y": "<double>",  // Moment of inertia about Y
  "mass_inertia_z": "<double>"   // Moment of inertia about Z
}
```

**SPRING**

```json
{
  "spring_type": "<string>",  // Spring type: "linear_spring" or "combined_spring"

  // linear_spring properties:
  "stiffness":                         "<double>",  // Axial stiffness
  "spring_constant_damping":           "<double>",  // Constant (viscous) damping coefficient
  "spring_linear_damping":             "<double>",  // Linear (velocity-proportional) damping coefficient
  "spring_mass":                       "<double>",  // Spring mass
  "stiffness_torsional":               "<double>",  // Torsional stiffness
  "spring_constant_damping_torsional": "<double>",  // Torsional constant damping
  "spring_linear_damping_torsional":   "<double>",  // Torsional linear damping
  "spring_inertia":                    "<double>",  // Moment of inertia

  // combined_spring properties:
  "k1":                "<double>",  // Stiffness of spring 1
  "k2":                "<double>",  // Stiffness of spring 2
  "gap":               "<double>",  // Gap value
  "limit_sliding_force":"<double>", // Limiting sliding force
  "damping":           "<double>",  // Constant damping coefficient
  "mass":              "<double>",  // Spring mass
  "mass_distribution": "<int>"      // Mass distribution between nodes: -1=node 0, 1=node 1, 0=equal
}
```

**BEAM**

```json
{
  "section_type":         "<int>",    // Cross-section shape type (see section_type table below)
  "angle":                "<double>", // Section rotation angle about beam axis [deg]
  "ey":                   "<double>", // Eccentricity along local Y axis
  "ez":                   "<double>", // Eccentricity along local Z axis
  "mesh_quality":         "<int>",    // Cross-section mesh quality for 3D visualization
  "warping_dof":          "<int>",    // Enable additional warping DOF for torsion
  "imported_section_id":  "<int>",    // ID of an imported section (overrides computed geometry)

  // Cross-section properties (for POINT section_type or imported sections):
  "area":                 "<double>", // Cross-section area A
  "A":                    "<double>", // Alias for area
  "Ix":                   "<double>", // Second moment of area about section X
  "Ip":                   "<double>", // Polar moment of inertia
  "Iy":                   "<double>", // Second moment of area about local Y
  "Iz":                   "<double>", // Second moment of area about local Z
  "Iyz":                  "<double>", // Product moment of area
  "It":                   "<double>", // Torsional geometric stiffness constant
  "Iw":                   "<double>", // Warping moment of inertia
  "max_y":                "<double>", // Signed distance from centroid to extreme fiber along Y
  "max_z":                "<double>", // Signed distance from centroid to extreme fiber along Z
  "shear_coefficient_yy": "<double>", // Shear correction factor YY
  "shear_coefficient_zz": "<double>", // Shear correction factor ZZ
  "shear_center_y":       "<double>", // Shear center Y coordinate
  "shear_center_z":       "<double>"  // Shear center Z coordinate
}
```

### section_type (BEAM)

| Value | Shape |
|-------|-------|
| 0 | RECTANGLE |
| 1 | ELLIPSE |
| 2 | I_BEAM |
| 3 | CIRCLE_WITH_A_CUT |
| 4 | POINT (manual parameters) |
| 5 | C_BEAM |
| 6 | L_BEAM |
| 7 | Z_BEAM |
| 8 | T_BEAM |
| 9 | RECTANGLE_WITH_A_CUT |
| 10 | HAT_BEAM |
| 12 | PIPE |

## coordinate_systems

```json
[
  {
    "id":     "<unsigned short>",  // CS ID (> 0); ID=1 must be the global Cartesian CS
    "type":   "<string>",          // CS type: "cartesian", "cylindrical", "spherical"
    "name":   "<string>",          // CS name
    "origin": "<Base64 [double]>", // Origin coordinates [x, y, z]
    "dir1":   "<Base64 [double]>", // End point of direction vector 1 (defines axis 1)
    "dir2":   "<Base64 [double]>"  // End point of direction vector 2 (defines axis 2)
  }
]
```

## sets

```json
{
  "nodesets": [                        // Node sets (used by BCs and queries)
    {
      "id":            "<int>",          // Node set ID
      "name":          "<string>",       // Node set name
      "apply_to_size": "<int>",          // Number of nodes in the set
      "apply_to":      "<Base64 [int]>"  // Node ID array (Base64-encoded)
    }
  ],
  "sidesets": [                        // Side/face sets
    {
      "id":            "<int>",          // Side set ID
      "name":          "<string>",       // Side set name
      "apply_to_size": "<int>",          // Number of element faces/edges in the set
      "apply_to":      "<Base64 [[int, int]]>"  // Pairs [elem_id, face_id], Base64-encoded as one string
    }
  ]
}
```

## blocks

```json
[
  {
    "id":             "<int>",    // Block ID (referenced by mesh elem_blocks)
    "material_id":    "<int>",    // Material ID applied to all elements in this block
    "material": {                 // Step-dependent material assignment (alternative to material_id)
      "ids":   "[int]",           // List of material IDs per step
      "steps": "[int]"            // Step numbers corresponding to each material ID
    },
    "property_id":    "<int>",    // Property table ID (beam/shell/spring/lumpmass sections)
    "cs_id":          "<int>",    // Coordinate system ID for the block
    "orientation_id": "<int>",    // Orientation ID for anisotropic materials
    "steps":          "[int]"     // Steps on which the block is active (empty = all steps)
  }
]
```

## loads

Each record has a load `type` and common control fields:

```json
{
  "id":              "<int>",          // Unique load ID (optional, used for reference)
  "name":            "<string>",       // Human-readable load name
  "type":            "<int>",          // Load type code (see loads.type table below)
  "apply_to_size":   "<int>",          // Number of target entities in apply_to array
  "apply_to":        "<Base64 [int]>", // Target entity IDs (node ids, elem ids, or [elem,face] pairs depending on type)
  "dependency_type": "[int]",          // Dependency type per data component (see const_types: 0=CONSTANT, 1-5=TABULAR_*, 6=FORMULA)
  "dep_var_size":    "[int]",          // Number of argument points per component for tabular data
  "dep_var_num":     "[double]",       // Argument values (e.g. time or temperature) for tabular components
  "data":            "[double]",       // Component values; count depends on load type (see table below)
  "step":            "[int]",          // Active load steps (empty array = all steps)
  "case":            "[int]",          // Active load cases (empty array = all cases)
  "cs":              "<int>"           // Coordinate system ID for force/displacement components
}
```

Parser routes by `type` to:
- face/segment BCs (apply_to encodes `[elem_id, face_id]` pairs)
- shell face BCs (apply_to encodes `[elem_id, face_id]` pairs)
- nodal BCs (apply_to is a node id array)
- point loads (apply_to is a flat `[x, y, z, ...]` coordinate array)
- volume/element loads (apply_to is an element id array)

Dependency model for component values:
- `CONSTANT` (const_type=0): scalar in `data`, no tabular entries
- `FORMULA` (const_type=6): formula string in `data`
- `TABULAR_*` (const_type=1-8): argument values in `dep_var_num`, y-values appended to `data`

Special behavior:
- `apply_to` may be the string `"all"` for node/element-wide assignment.

### loads.type

**Face loads** — `apply_to` encodes pairs `[elem_id, face_id]`

| Code | Name | `data` components |
|------|------|-------------------|
| 1 | FaceDeadStress | 1 (pressure) |
| 3 | FaceTrackingStress | 1 (pressure) |
| 11 | FaceHeatFlux | 1 |
| 13 | FaceConvection | 2 (env. temp, heat transfer coef) |
| 15 | FaceRadiation | 2 (env. temp, emissivity) |
| 19 | FaceAbsorbingBC | 0 |
| 45 | FaceSloshingBC | 0 |
| 35 | FaceDistributedForce | 6 (Fx, Fy, Fz, Mx, My, Mz) |
| 36 | FaceEquivalentForce | 6 (Fx, Fy, Fz, Mx, My, Mz) |
| 37 | FaceTrackingDistributedForce | 6 |
| 38 | FaceTrackingEquivalentForce | 6 |
| 39 | FaceFluidFlux | 1 |

**Shell face loads** — `apply_to` encodes pairs `[elem_id, face_id]`

| Code | Name | `data` components |
|------|------|-------------------|
| 21 | ShellHeatfluxTopBottom | 2 (top flux, bottom flux) |
| 22 | ShellHeatfluxTop | 1 |
| 23 | ShellHeatfluxBottom | 1 |
| 24 | ShellConvectionTopBottom | 4 (T_top, h_top, T_bot, h_bot) |
| 25 | ShellConvectionTop | 2 (T_top, h_top) |
| 26 | ShellConvectionBottom | 2 (T_bot, h_bot) |

**Segment loads** — `apply_to` encodes pairs `[elem_id, edge_id]`

| Code | Name | `data` components |
|------|------|-------------------|
| 2 | SegmentDeadStress | 1 |
| 4 | SegmentTrackingStress | 1 |
| 12 | SegmentHeatFlux | 1 |
| 14 | SegmentConvection | 2 (env. temp, heat transfer coef) |
| 16 | SegmentRadiation | 2 (env. temp, emissivity) |
| 20 | SegmentAbsorbingBC | 0 |
| 46 | SegmentSloshingBC | 0 |
| 31 | SegmentDistributedForce | 6 (Fx, Fy, Fz, Mx, My, Mz) |
| 32 | SegmentEquivalentForce | 6 |
| 33 | SegmentTrackingDistributedForce | 6 |
| 34 | SegmentTrackingEquivalentForce | 6 |
| 40 | SegmentFluidFlux | 1 |

**Node loads** — `apply_to` is node id array

| Code | Name | `data` components |
|------|------|-------------------|
| 5 | NodeForce | 6 (Fx, Fy, Fz, Mx, My, Mz) |
| 18 | HeatSource | 1 |
| 28 | NodeHeatFlux | 1 |
| 29 | NodeConvection | 2 (env. temp, heat transfer coef) |
| 30 | NodeRadiation | 2 (env. temp, emissivity) |
| 41 | NodeFluidFlux | 1 |
| 43 | FluidSource | 1 |

**Point loads** — `apply_to` is array of 3D coordinates (`[x, y, z, ...]`)

| Code | Name | `data` components |
|------|------|-------------------|
| 47 | PointDeadForce | 6 |
| 48 | PointTrackingForce | 6 |
| 49 | PointHydrodynamicForce | 6 |

**Volume/element loads** — `apply_to` is element id array

| Code | Name | `data` components |
|------|------|-------------------|
| 6 | GravityMassForce | 3 (ax, ay, az) |
| 17 | VolumeHeatSource | 1 |
| 42 | VolumeFluidSource | 1 |
| 44 | VolumeGravityMassForce | 3 (ax, ay, az) |

## restraints

Common shape:

```json
{
  "id":              "<int>",          // Unique restraint ID (optional, used for reference)
  "name":            "<string>",       // Human-readable restraint name
  "flag":            "[int]",          // Restraint type codes (see restraints.flag table); array length must match DOF count
  "apply_to_size":   "<int>",          // Number of nodes in apply_to array
  "apply_to":        "<Base64 [int]>", // Node ID array; may be string "all" to apply to every node
  "dependency_type": "[int]",          // Dependency type per DOF (see const_types: 0=CONSTANT, 1-5=TABULAR_*, 6=FORMULA)
  "dep_var_size":    "[int]",          // Number of argument points per DOF for tabular data
  "dep_var_num":     "[double]",       // Argument values (e.g. time or temperature) for tabular DOFs
  "data":            "[double]",       // Prescribed BC values per active DOF
  "step":            "[int]",          // Active load steps (empty array = all steps)
  "case":            "[int]",          // Active load cases (empty array = all cases)
  "cs":              "<int>"           // Coordinate system ID for displacement/rotation components
}
```

Notes:
- `apply_to` can be the string `"all"` to apply the BC to all mesh nodes.
- `flag` array length must match the number of DOFs for the restraint type (e.g. 6 for Displacement, 1 for Temperature).
- Rotordynamics: restraints with `flag=[2,...]` (Velocity) may reference `campbell` and `campbell_axis` for angular velocity setup.

### restraints.flag

| Value | Name | Array length | Description |
|-------|------|--------------|-------------|
| 0 | EmptyRestraint | — | No constraint; used as placeholder in arrays |
| 1 | Displacement | 6 | Displacement and rotation DOFs. e.g. `[1,0,0,0,1,0]` |
| 2 | Velocity | 6 | Velocity and angular velocity DOFs |
| 3 | Temperature | 1 | Temperature BC. e.g. `[3]` |
| 4 | TemperatureTop | 2 | Top surface temperature (shells). Used with TemperatureBottom. e.g. `[4,5]` |
| 5 | TemperatureBottom | 2 | Bottom surface temperature (shells) |
| 6 | TemperatureMiddle | 1 or 2 | Mid-surface temperature (shells). May be combined with TemperatureGradient |
| 7 | TemperatureGradient | 1 or 2 | Temperature gradient (shells) |
| 9 | Acceleration | 6 | Acceleration and angular acceleration. e.g. `[9,0,9,0,0,0]` |
| 10 | PorePressure | 1 | Pore pressure BC. e.g. `[10]` |
| 12 | DirectionDisplacement | 1 | Displacement along a direction; applied to element faces |
| 13 | DirectionVelocity | 1 | Velocity along a direction; applied to element faces |
| 14 | DirectionAcceleration | 1 | Acceleration along a direction; applied to element faces |
| 15 | VolumeAngularVelocity | 3 | Angular velocity for elements. e.g. `[15,15,0]` |

## initial_sets

Common shape:

```json
{
  "id":              "<int>",          // Unique initial condition ID (optional)
  "name":            "<string>",       // Human-readable IC name
  "type":            "<int>",          // IC type code (see initial_sets.type table)
  "flag":            "[int]",          // Active DOF flags per component (0=inactive, 1=active; see per-type notes)
  "apply_to_size":   "<int>",          // Number of nodes in apply_to array
  "apply_to":        "<Base64 [int]>", // Node ID array
  "dependency_type": "[int]",          // Dependency type per DOF (same semantics as loads)
  "dep_var_size":    "[int]",          // Number of argument points per DOF for tabular data
  "dep_var_num":     "[double]",       // Argument values for tabular DOFs
  "data":            "[double]",       // Initial values per DOF
  "cs":              "<int>"           // Coordinate system ID
}
```

`flag` per type:
- **Displacement (type=0), Velocity (type=1)**: array of 6 ints (Ux,Uy,Uz,Rx,Ry,Rz), `1` = active
- **AngularVelocity (type=2)**: array of 3 ints (ωx, ωy, ωz), `1` = active
- **Temperature (type=3), PorePressure (type=4)**: array of 1 int

Supports same dependency scheme as loads/restraints for values.

### initial_sets.type

| Value | Name |
|-------|------|
| 0 | Displacement |
| 1 | Velocity |
| 2 | AngularVelocity |
| 3 | Temperature |
| 4 | PorePressure |

## coupling_constraints

Common record shape:

```json
{
  "id":                   "<int>",          // Coupling constraint ID
  "name":                 "<string>",       // Coupling constraint name
  "type":                 "<int>",          // Coupling type (see coupling_constraints.type table)
  "master_size":          "<int>",          // Number of master nodes
  "master":               "<Base64 [int]>", // Master node ID array (Base64-encoded)
  "slave_size":           "<int>",          // Number of slave nodes
  "slave":                "<Base64 [int]>", // Slave node ID array (Base64-encoded)
  "step":                 "[int]",          // Active load steps (empty = all steps)
  "case":                 "[int]",          // Active load cases (empty = all cases)
  "cs":                   "<int>",          // Coordinate system ID for DOF directions
  "coordinate_system_id": "<int>"           // Alternative field for cs; parser checks both
}
```

### coupling_constraints.type

| Value | Name |
|-------|------|
| 0 | ELASTICITY |
| 1 | TEMPERATURE |
| 2 | DISTANCE |
| 3 | PORE_PRESSURE |
| 4 | DIRECTION |
| 5 | INTERPOLATION |
| 6 | CONSTRAINT_EQUATION |

### Type-specific fields

**ELASTICITY (type=0)**

```json
{
  "dofs":      "[int]",     // 6-element array; 1 = active DOF (Ux,Uy,Uz,Rx,Ry,Rz)
  "stiffness": "[double]", // Spring stiffness per active DOF (penalty connection)
  "damping":   "[double]"  // Damping coefficient per active DOF
}
```

**TEMPERATURE (type=1), PORE_PRESSURE (type=3), DISTANCE (type=2)**

No extra fields. Coupling established purely by master/slave node pairs.

**DIRECTION (type=4)**

```json
{
  "direction": "[double, double, double]",  // Unit direction vector for the constraint
  "stiffness": "<double>"                   // Spring stiffness along the direction
}
```

**INTERPOLATION (type=5)** — RBE3-style distributed coupling

```json
{
  "master_dofs":        "[int]",    // 6-element array; 1 = active DOF on master (reference node)
  "slave_dofs":         "[int]",    // 6-element array; 1 = active DOF on slave (contributing nodes)
  "distance_weighting": "<bool>",   // If true, weights are inversely proportional to distance
  "factor":             "<double>"  // Uniform weight multiplier when distance_weighting = false
}
```

**CONSTRAINT_EQUATION (type=6)** — General linear multipoint constraint: Σ coef·dof = rhs

```json
{
  "equation": {
    "rhs":   "<double>",  // Right-hand side constant value
    "terms": [
      {
        "node":        "<int>",    // Node ID
        "dof":         "<string>", // DOF name: "UX","UY","UZ","RX","RY","RZ"
        "coefficient": "<double>"  // Coefficient for this term (alias: "coef")
      }
    ]
  },
  "enforcement_method": "<string>", // "elimination" or "penalty"
  "stiffness": "[double]",           // Penalty stiffness (when method=penalty)
  "damping":   "[double]"            // Penalty damping (when method=penalty)
}
```

- `term["coef"]` is accepted as an alias for `term["coefficient"]`

## contact_constraints

```json
[
  {
    "id":                   "<int>",    // Contact pair ID
    "name":                 "<string>", // Contact pair name
    "type":                 "<string>", // Contact behaviour: "general", "tied", "tied_normal", "tied_tangent"
    "method":               "<string>", // Enforcement method: "auto", "penalty", "mpc", "pure_lagrangian", "aug_lagrangian"
    "step":                 "[int]",    // Active load steps (empty = all steps)
    "master_size":          "<int>",    // Number of master entities
    "master":               "<Base64 [[elem_id, face_id]]>", // Master element faces (or flat [int] node array)
    "slave_size":           "<int>",    // Number of slave entities
    "slave":                "<Base64 [[elem_id, face_id]]>", // Slave element faces (or flat [int] node array)
    "friction":             "<double>", // Coulomb friction coefficient (≥ 0; for type="general")
    "tolerance":            "<double>", // Geometric search tolerance = this value + abs(offset)
    "offset":               "<double>", // Normal offset between master and slave surfaces
    "preload":              "<double>", // Contact preload (for type="tied_tangent")
    "ignoreoverlap":        "<bool>",   // Ignore initial gap/overlap (synonym of ignore_overlap)
    "ignore_overlap":       "<bool>",   // Ignore initial gap/overlap
    "distance":             "<double>", // Max allowed tied distance; -1 = unlimited
    "min_angle":            "<double>", // Min contact detection angle [deg] (default 45)
    "detection_tolerance":  "<double>", // Parametric detection tolerance
    "search_radius":        "<double>", // Pinball search radius multiplier (> 0)
    "normal_stiffness":     "<double>", // Penalty normal stiffness multiplier (> 0; method="penalty")
    "tangent_stiffness":    "<double>", // Penalty tangential stiffness multiplier
    "thermo_penalty_mult":  "<double>", // Thermal penalty multiplier
    "gap_tension":          "<double>", // Gap tension tolerance (≥ 0, default 0.1)
    "ignore_tied_stiffness":"<bool>",   // Disable tied stiffness contributions
    "thermo_penalty_relax": "<double>", // Relaxation factor for thermal penalty
    "gap_gas_material":     "<int>",    // Material ID for gap gas (enables thermal gap model)
    "gap_gas_fractions":    {...},       // Mole fractions of gap gas components (see gap_gas_fractions)
    "lagrange_settings":    {...}        // Lagrange multiplier settings (see lagrange_settings below)
  }
]
```

- `type`: `"general"`, `"tied"`, `"tied_normal"`, `"tied_tangent"`
- `method`: `"auto"`, `"penalty"`, `"mpc"`, `"pure_lagrangian"`, `"aug_lagrangian"`
- `ignoreoverlap` / `ignore_overlap`: synonyms; ignore initial gap/overlap
- `master`/`slave`: encoded as pairs `[elem_id, face_id]` in Base64; when node IDs are used instead, encode as a flat `[int]` array
- `friction`: friction coefficient (Coulomb); must be ≥ 0
- `tolerance`: total search tolerance = geometric tolerance + abs(offset)
- `offset`: normal offset between master and slave surfaces
- `preload`: contact preload value
- `distance`: maximum allowed tied distance; -1 = unlimited
- `search_radius`: pinball search radius multiplier (must be > 0)
- `normal_stiffness`: penalty stiffness in normal direction multiplier (must be > 0)
- `tangent_stiffness`: penalty stiffness in tangential direction multiplier
- `thermo_penalty_mult`: thermal penalty multiplier
- `gap_tension`: gap tension tolerance (must be ≥ 0, default 0.1)
- `min_angle`: minimum angle for contact detection [degrees] (default 45°)
- `detection_tolerance`: parametric detection tolerance
- `ignore_tied_stiffness`: if true, disables tied stiffness contributions (for all models)
- `thermo_penalty_relax`: relaxation factor for thermal penalty
- `gap_gas_fractions`: thermal gap gas composition (enables thermal gap conductance model)
- `gap_gas_material`: material ID for user-defined gap gas (enables thermal gap conductance model)

### gap_gas_fractions

Specifies mole fractions of gap gas components for thermal gap conductance:

```json
{
  "helium":   "<double>",  // Helium mole fraction
  "krypton":  "<double>",  // Krypton mole fraction
  "xenon":    "<double>",  // Xenon mole fraction
  "caesium":  "<double>",  // Caesium mole fraction
  "user_defined": ["<double>"]  // Custom gas: flat array of [mole_fraction, molecular_weight, collision_diameter, characteristic_temp, ...]
}
```

Non-zero fractions are added to the mixture. `user_defined` array must have length divisible by 4.

### lagrange_settings

Used when `method` is `"pure_lagrangian"` or `"aug_lagrangian"`:

```json
{
  "tangent_rate":           "<double>",
  "criteria_smoothing":     "<double>",
  "use_tangent":            "<bool>",
  "use_stick_predictor":    "<bool>",
  "overconstraint_normal":  "<bool>",
  "overconstraint_tangent": "<bool>",
  "stability_normal":       "<double>",
  "stability_tangent":      "<double>",
  "shear_stress_limit":     "<double>",
  "tensile_stress_limit":   "<double>",
  "direction_tolerance":    "<double>",
  "augmented_tolerance":    "<double>"
}
```

## periodic_constraints

```json
[
  {
    "id":          "<int>",                      // Periodic BC ID
    "name":        "<string>",                   // Periodic BC name
    "cs":          "<int>",                      // Coordinate system defining the periodicity axis
    "step":        "[int]",                      // Active load steps (empty = all steps)
    "type":        "<int>",                      // Periodicity type (see periodic_constraints.type)
    "sectors":     "<int>",                      // Number of repeating sectors (cyclic symmetry)
    "master_size": "<int>",                      // Number of master element faces
    "master":      "<Base64 [[elem_id, face_id]]>", // Master surface: pairs [elem_id, face_id]
    "slave_size":  "<int>",                      // Number of slave element faces
    "slave":       "<Base64 [[elem_id, face_id]]>"  // Slave surface: pairs [elem_id, face_id]
  }
]
```

### periodic_constraints.type

| Value | Name |
|-------|------|
| 0 | ALL |
| 1 | DISPLACEMENT |
| 2 | THERMAL_CONDUCTION |
| 3 | PORE_PRESSURE_CONDUCTION |
| 4 | VELOCITY |
| 5 | ACCELERATION |

## receivers

```json
[
  {
    "id":            "<int>",          // Receiver set ID
    "name":          "<string>",       // Receiver set name
    "type":          "<int>",          // Receiver type (see receivers.type table)
    "apply_to_size": "<int>",          // Number of receiver nodes
    "apply_to":      "<Base64 [int]>", // Node ID array (Base64-encoded)
    "dofs":          "[int, int, int]",// Active DOF flags [x, y, z]; 1 = record; not required for PRESSURE
    "output_step":   "<int>"           // Record output every N time steps
  }
]
```

### receivers.type

| Value | Name |
|-------|------|
| 0 | DISPLACEMENT |
| 1 | VELOCITY |
| 2 | PRINCIPAL_STRESS |
| 3 | PRESSURE |
| 4 | ACCELERATION |

## settings

```json
{
  "type":                     "<string>",  // Analysis type (see type values below)
  "dimensions":               "<string>",  // Spatial dimensionality: "2D" or "3D"
  "plane_state":              "<string>",  // 2D formulation: "p-stress", "p-strain", "axisym_x", "axisym_y"
  "permission_write":         "<bool>",    // Allow result writing to disk when RAM is insufficient
  "periodic_bc":              "<bool>",    // Enable periodic BCs for effective properties analysis
  "finite_deformations":      "<bool>",    // Enable geometrically nonlinear (large deformation) analysis
  "elasticity":               "<bool>",    // Include elastic stress/strain computation
  "plasticity":               "<bool>",    // Enable plastic material behavior
  "heat_transfer":            "<bool>",    // Include thermal (heat conduction) analysis
  "porefluid_transfer":       "<bool>",    // Enable poroelastic (Biot) fluid transfer
  "slm":                      "<bool>",    // Enable Selective Laser Melting additive manufacturing
  "incompressibility":        "<bool>",    // Enforce incompressibility constraint
  "preload":                  "<bool>",    // Include prestress from preload material group
  "lumpmass":                 "<bool>",    // Use lumped (diagonal) mass matrix instead of consistent
  "radiation_among_surfaces": "<bool>",    // Enable surface-to-surface radiation
  "spectral_element":         "<bool>",    // Use spectral element method (SEM)
  "spectral_order":           "<int>",     // Polynomial order for SEM elements (3–9)
  "bc_tolerance":             "<double>",  // Geometric tolerance for BC node/face detection
  "lump_agreed":              "<bool>",    // Suppress lump-mass compatibility warning
  "viscosity":                "<bool>",    // Enable viscous material model
  "xfem":                     "<bool>",    // Enable experimental XFEM crack propagation
  "thermal_expansion":        "<bool>",    // Effectiveprops: compute thermal expansion coefficients
  "poroelasticity":           "<bool>",    // Effectiveprops: compute poroelastic effective properties
  "permeability":             "<bool>",    // Effectiveprops: compute effective permeability
  "linear_solver":            "{...}",     // Linear solver settings
  "nonlinear_solver":         "{...}",     // Nonlinear (Newton-Raphson) solver settings
  "eigen_solver":             "{...}",     // Eigenvalue solver settings
  "damping":                  "{...}",     // Damping model settings
  "thermal_gap_settings":     "{...}",     // Thermal gas gap solver settings
  "statics":                  "{...}",     // Static analysis settings
  "dynamics":                 "{...}",     // Transient dynamics settings
  "harmonic":                 "{...}",     // Harmonic response settings
  "environment":              "{...}",     // Environment (reference temperature)
  "output":                   "{...}",     // Result output settings
  "test_opts":                "{...}",     // Debug/test options
  "link":                     "{...}",     // Incompatible mesh link settings
  "mbd":                      "{...}",     // Multi-body dynamics output settings
  "table_interpolation":      "{...}",     // Spatial table interpolation settings
  "effectiveprops":           "{...}"      // Effective properties analysis settings
}
```

### settings.linear_solver

```json
{
  "method":               "<string>",  // SLAE solution method: "auto", "direct", "iterative"
  "use_cuda":             "<string>",  // Use GPU acceleration: "yes", "no", "auto"
  "precision":            "<string>",  // Floating-point precision: "single", "double", "auto"
  "on_fail":              "<bool>",    // Fall back to other methods on failure (only for method="auto")
  "use_uzawa":            "<string>",  // Use Uzawa saddle-point solver: "auto", "yes", "no"
  "uzawa_rel_precision":  "<double>",  // Uzawa relative convergence tolerance
  "uzawa_max_iterations": "<int>",     // Uzawa maximum iteration count
  "iter_opts": {                       // Iterative solver options
    "epsilon":           "<double>",   // Relative tolerance
    "stopping_criteria": "<double>",   // Absolute tolerance
    "max_iterations":    "<int>",      // Maximum iteration count
    "preconditioner":    "<string>"    // Preconditioner: "auto","none","diagonal","ilu0","ilut","ssor",
                                       // "multigrid","multigrid_ilu1","algmultigrid","ic","ilu",
                                       // "amg","ainv_standart","ainv_static","ainv_novel","ainv_unsym"
  }
}
```

### settings.nonlinear_solver

```json
{
  "arc_method":          "<bool>",    // Enable arc-length continuation method for snap-through/limit point problems
  "min_arc_length":      "<double>",  // Minimum relative arc-length radius (required when arc_method=true)
  "line_search":         "<bool>",    // Enable line-search acceleration for Newton iterations
  "min_load_steps":      "<int>",     // Minimum number of incremental load steps (required)
  "start_load_steps":    "<int>",     // Initial number of load steps (defaults to min_load_steps)
  "max_load_steps":      "<int>",     // Maximum number of incremental load steps (required)
  "max_iterations":      "<int>",     // Maximum Newton-Raphson iterations per step (required)
  "diverge_max_iterations": "<int>", // Steps with divergence allowed before error; 0 = disabled
  "target_iter":         "<int>",     // Target Newton iterations per step for adaptive step sizing
  "tolerance":           "<double>"   // Convergence tolerance for residual and variable norms (required)
}
```

Field requirements depend on analysis type:
- `finite_deformations=true`: `min_load_steps`, `max_load_steps`, `max_iterations`, `tolerance` are required
- `arc_method=true`: `min_arc_length` is required

### settings.eigen_solver

```json
{
  "number":                  "<int | string>", // Number of eigenvalues to compute; or "all" to find all in target range
  "target":                  "<double | [double, double]>", // Target: scalar=nearest search, [min,max]=interval search [Hz]
  "solver":                  "<string>",  // EPS algorithm; required
  "prime_solver":            "<string>",  // Backend solver choice; optional
  "relative_tolerance":      "<double>",  // EPS convergence relative tolerance (required, must be > 0)
  "absolute_tolerance":      "<double>",  // EPS absolute convergence tolerance (optional)
  "eps_max_iterations":      "<int>",     // Maximum EPS iterations (required, must be > 0)
  "shift":                   "<double>",  // Manual spectral shift value (optional)
  "damped_type":             "<string>",  // Damping model type for eigenvalue problem
  "symmetrization_type":     "<string>",  // Matrix symmetrization type for FSI problems
  "evaluate_effective_mass": "<bool>",    // Compute modal effective mass
  "rotation_center":         "[double, double, double]", // Center of rotation for effective mass calculation
  "calc_stress_for_modal":   "<bool>",    // Compute stresses/strains for each modal shape
  "acoustic_displacements":  "<bool>",    // Compute acoustic displacements in FSI
  "campbell":                "<bool>",    // Build Campbell diagram (rotordynamics only)
  "modal_result_filename":   "<string>",  // Path to .bin modal result file for harmonic/transient response
  "chunk_size":              "<int>",     // Block size for block eigensolver algorithms
  "spectr_trans": {
    "name":             "<string>",  // Spectral transformation: "auto", "shift", "shift_invert", "general_cayley" (required)
    "shift_value":      "<double>",  // Shift value for shift/shift_invert/general_cayley
    "anti_shift_value": "<double>"   // Anti-shift value (only for general_cayley)
  },
  "linear_solver": {                     // Inner linear solver settings for EPS (required)
    "solver":         "<string>",   // "direct" / "iterative" / "auto"
    "method":         "<string>",   // KSP method (required)
    "preconditioner": "<string>",   // Preconditioner (required)
    "iter_opts": {
      "linear_relative_tolerance":   "<double>",  // KSP relative tolerance (required, > 0)
      "linear_absolute_tolerance":   "<double>",  // KSP absolute tolerance (required, > 0)
      "linear_divergence_tolerance": "<double>",  // KSP divergence tolerance (required, > 0)
      "linear_max_iterations":       "<int>"       // KSP max iterations (required, > 0)
    }
  }
}
```

**`solver` values:**
- `"Auto"` — automatic selection
- `"krylovschur"` — Krylov-Schur (recommended for large sparse problems)
- `"arnoldi"` — Arnoldi iteration
- `"lanczos"` — Lanczos iteration (symmetric problems)
- `"gd"` — Generalized Davidson
- `"jd"` — Jacobi-Davidson
- `"blocklanczos"` — Block Lanczos (selects `BLOCK LANCZOS` prime solver automatically)

**`prime_solver` values:**
- `"SLEPc"` — use SLEPc library (default when built with PETSc)
- `"BLOCK LANCZOS"` — use MKL Block Lanczos backend
- `"MKLES"` — use MKLES backend
- `"NECH"` — use NECH backend

**`spectr_trans.name` values:**
- `"auto"` — automatic transformation selection
- `"shift"` — additive shift (requires `shift_value`)
- `"shift_invert"` — shift-and-invert (requires `shift_value`)
- `"general_cayley"` — Cayley transformation (requires `shift_value` and `anti_shift_value`)

**`linear_solver.method` values:**
`"auto"`, `"preonly"`, `"cg"`, `"gmres"`, `"richardson"`, `"chebyshev"`, `"bicg"`, `"bcgs"`, `"tfqmr"`, `"minres"`, `"cr"`, `"gcr"`

**`linear_solver.preconditioner` values:**
`"auto"`, `"lu"` (requires `solver=direct`), `"none"`, `"jacobi"`, `"bjacobi"`, `"sor"`, `"ssor"`, `"ilu"`, `"asm"`

**Target behavior:**
- `target` absent → minimal eigenvalue search
- `target` = scalar 0.0 → minimal eigenvalue search
- `target` = non-zero scalar → nearest-to-target search
- `target` = `[min, max]` array → interval search (lower bound must be ≥ 0)

### settings.damping

```json
{
  "use":              "<bool>",    // Enable damping
  "structural":       "<double>",  // Structural (hysteretic) damping ratio η
  "mass_matrix":      "<double>",  // Rayleigh mass-proportional damping coefficient α
  "stiffness_matrix": "<double>",  // Rayleigh stiffness-proportional damping coefficient β
  "coriolis":         "<bool>",    // Include Coriolis matrix (rotordynamics)
  "spin_softening":   "<bool>",    // Include spin softening (centrifugal stiffness correction)
  "is_stationary":    "<bool>"     // Treat rotation as stationary (suppress Coriolis contribution)
}
```

### settings.thermal_gap_settings

```json
{
  "start_temp":       "<double>",  // Starting temperature for gap conductance table
  "end_temp":         "<double>",  // Ending temperature for gap conductance table
  "step_temp":        "<double>",  // Temperature step for gap conductance table
  "scatangle_eps":    "<double>",  // Scattering angle tolerance
  "impact_eps":       "<double>",  // Impact tolerance
  "velocity_eps":     "<double>",  // Velocity tolerance
  "result_filename":  "<string>"   // Path to a previous thermal gap result file for warm restart
}
```

### settings.statics

```json
{
  "steps_count":        "<int>",     // Number of static load steps
  "init_time":          "<double>",  // Initial (start) pseudo-time value
  "init_step":          "<int>",     // Initial step index for restart
  "time_step":          "<double>",  // Optional: fixed time step (overrides steps_count if given)
  "result_output_iter": "<int>",     // Output every N iterations (mutually exclusive with other output options)
  "result_output_time": "<double>",  // Output every dt time units (mutually exclusive)
  "result_number":      "<int>"      // Total number of equally-spaced output points (mutually exclusive)
}
```

Output options are mutually exclusive: use exactly one of `result_output_iter`, `result_output_time`, or `result_number`.

### settings.dynamics

```json
{
  "method":             "<string>",  // Integration method: "full_solution" or "mode_superposition"
  "scheme":             "<string>",  // Time integration scheme: "explicit" or "implicit"
  "max_time":           "<double>",  // Total simulation time
  "init_time":          "<double>",  // Start time (for restart)
  "init_step":          "<int>",     // Start step index (for restart)
  "time_step":          "<double>",  // Fixed time step size (implicit; mutually exclusive with steps_count)
  "steps_count":        "<int>",     // Number of time steps (implicit; mutually exclusive with time_step)
  "courant":            "<double>",  // Courant number for automatic step size in explicit scheme
  "max_steps_count":    "<int>",     // Maximum step count limit for explicit scheme
  "newmark_gamma":      "<double>",  // Newmark γ parameter for numerical damping in implicit/mode_superposition (default: 0.005, valid range [0, 0.4])
  "result_output_iter": "<int>",     // Output every N steps (mutually exclusive with other output options)
  "result_output_time": "<double>",  // Output every dt time (mutually exclusive)
  "result_number":      "<int>",     // Total equally-spaced output count (mutually exclusive)
  "mod_count":          "<int>"      // Number of modes to include for mode_superposition method
}
```

- `method`: `"full_solution"` — direct time integration; `"mode_superposition"` — modal superposition
- `scheme`: `"explicit"` — central differences (requires `courant` + `max_steps_count`); `"implicit"` — Newmark (requires `time_step` or `steps_count`)
- `newmark_gamma`: controls high-frequency numerical dissipation; 0.0 = no dissipation (standard Newmark), 0.005 = slight damping (default)
- Output options are mutually exclusive: use exactly one of `result_output_iter`, `result_output_time`, or `result_number`

### settings.harmonic

```json
{
  "method":         "<string>",  // "mode_superposition" — requires prior modal analysis result in eigen_solver.modal_result_filename
  "frequency_step": "<double>",  // Frequency increment [Hz] (mutually exclusive with steps_count)
  "steps_count":    "<int>"      // Number of frequency steps (mutually exclusive with frequency_step)
}
```

- `method`: `"mode_superposition"` — modal superposition frequency response
- `frequency_step` and `steps_count` are mutually exclusive; frequency range is taken from the modal result file

### settings.output

```json
{
  "energy":               "<bool>",  // Compute and output strain/kinetic energy
  "intermediate_results": "<bool>",  // Output results at every nonlinear increment
  "log":                  "<bool>",  // Write solver log file
  "normal_force":         "<bool>",  // Output contact normal forces
  "record3d":             "<bool>",  // Output 3D result records
  "vtu":                  "<bool>",  // Write VTU output files
  "without_smoothing":    "<bool>",  // Skip result smoothing (output raw Gauss-point values)
  "multiblock_off":       "<bool>",  // Disable multiblock (partitioned) VTK output
  "zvtk":                "<bool>",  // Write compressed ZVTK output files
  "trackingForce":        "<bool>",  // Output tracking (follower) force contributions
  "material":             "<bool>"   // Output material elastic modulus field
}
```

### settings.link

```json
{
  "rms": "<bool>"  // Use RMS (root-mean-square) link model for connecting incompatible meshes
}
```

### settings.mbd

Multi-body dynamics output settings:

```json
{
  "precision":     "<int>",    // Output floating-point precision (significant digits)
  "output_format": "<string>", // Output format: "binary" or "text"
  "all_nodes":     "<bool>"    // Output results for all nodes (not just attachment points)
}
```

### settings.table_interpolation

Settings for spatially distributed material/load table interpolation:

```json
{
  "interp_type":   "<string>", // Interpolation method: "near", "LRBF_lin", "LRBF", "Triangle", "MC_lin"
  "func_type":     "<string>", // RBF basis function: "gauss", "multiquad", "inv_multiquad", "inv_quad", "thin_plate", "wendland"
  "interp_points": "<int>",    // Number of support points for RBF interpolation
  "interp_param":  "<double>", // Shape parameter for RBF basis function
  "radius":        "<double>"  // Compact support radius for Wendland/LRBF
}
```

### settings.effectiveprops

Effective properties analysis settings:

```json
{
  "permeability":       "<bool>",  // Compute effective permeability
  "need_compression":   "<bool>"   // Apply compression loading pattern
}
```

### settings.environment

```json
{
  "temperature": "<double>"  // Reference ambient temperature [K or °C depending on material units]
}
```

### settings.test_opts

```json
{
  "print_matrix_full":        "<bool>",  // Print full system matrix to console
  "print_matrix_txt":         "<bool>",  // Save system matrix as text file
  "print_matrix_bin":         "<bool>",  // Save system matrix as binary file
  "print_matrix_ccs":         "<bool>",  // Save system matrix in CCS format
  "precision":                "<int>",   // Console output precision for debug values
  "output_iteration_results": "<bool>"   // Output results at every Newton iteration
}
```

## Data dependencies and value encoding

For BCs/material tables, parser accepts:
- scalar constants
- formulas (string)
- tabular dependencies via paired `data` and `dep_var_num`
- multidimensional tables (`dependency_type` as array)

In binary mode, payload arrays are decoded according to `header.types` and field-specific expected type.

## Compatibility notes

- Parser keeps backward compatibility with older material/property layouts, but new integrations should prefer v3 grouped format.
- Some combinations are analysis-type dependent and validated at parse time.
- Unknown/unsupported enum values or inconsistent output settings produce parse errors.

## Deprecated & Legacy Fields

This section documents fields and structures that have been superseded, renamed, or made optional.

### Legacy Material Property Layouts

#### **Layout v1 & v2: Flat Constants (Deprecated)**

**Writer**: No longer serializes flat layout; always uses v3 grouped structure.

**Reader**: Still supported for backward compatibility (FCParser.cpp lines 4206-4192).

**Example v1/v2 structure:**
```json
{
  "materials": [{
    "id": 1,
    "name": "Steel",
    "constants": {
      "young": 210e9,
      "poisson": 0.3,
      "density": 7850,
      "thermal_conductivity": 50,
      "specific_heat": 480,
      "emissivity": 0.5
    }
  }]
}
```

**Replacement (v3 grouped layout):**
```json
{
  "materials": [{
    "id": 1,
    "name": "Steel",
    "elasticity": [{
      "type": 0,
      "const_names": [0, 1],
      "const_types": [0, 0],
      "const_dep_size": [0, 0],
      "constants": "base64_[210e9, 0.3]",
      "const_dep": ["", ""]
    }],
    "common": [{
      "type": 0,
      "const_names": [0],
      "const_types": [0],
      "const_dep_size": [0],
      "constants": "base64_[7850]",
      "const_dep": [""]
    }],
    ...
  }]
}
```

**Migration Path**: Existing v1/v2 files parse successfully; new exports always use v3.

#### **Layout v2: Enum Index Mapping (Deprecated)**

**Issue**: Property indices were direct enum values; v3 uses explicit `const_names` array.

**Example conflict**: In v2, index `0` in material.constants always meant YOUNG_MODULE. In v3, `const_names[0]` explicitly says which property, supporting non-sequential and property-group-specific indexing.

**Parser handling**: FillMaterialsV2() (FCParser.cpp:3950) maps old indices to v3 structure.

---

### Deprecated/Legacy Settings Fields (Partial Legacy)

| Field | Status | Parser Support | Replacement | Note |
|-------|--------|-----------------|-------------|------|
| `settings.incompressibility` | LEGACY | ✅ **ACTIVE** (line 13124) | Boolean flag in `settings.incompressibility` | Still read; writer passes through from UI settings |
| `settings.spectral_element` | LEGACY | ✅ **ACTIVE** (lines 12325, 12371) | Modern field; used for SEM detection | Still read; writer passes through |
| `settings.plasticity` | LEGACY | ✅ **ACTIVE** (line 13126) | Separate feature flags per analysis | Still read; writer passes through |
| `settings.dynamics.scheme` | LEGACY | ✅ **ACTIVE** (lines 12488, 12501) | Enum-based scheme selection | Still actively used; not deprecated despite comments at 6399 |
| `settings.dimensions` (if present) | LEGACY | ❌ Commented | Use problem geometry/element types | No active parsing |

**Important**: Fields like `incompressibility`, `spectral_element`, `plasticity`, and `dynamics.scheme` are NOT actually deprecated in parser code, despite having commented-out legacy checks. They are actively read and used in current code paths (see line references above). Keep these fields in new exports.

---

### Field Name Aliases & Synonyms

| Canonical Name | Alternative Name(s) | Status | Parser Route | Priority |
|----------------|-------------------|--------|--------------|----------|
| `coupling_constraints[i].cs` | `coupling_constraints[i].coordinate_system_id` | ✅ BOTH SUPPORTED | Parser checks `cs` first, then `coordinate_system_id` (FCParser.cpp:7356-7357) | Use `cs` for new files; `coordinate_system_id` is backward compat |
| `restraints[i].cs` | (none; use `cs`) | ✅ | FCParser.cpp:6882-6883 | Standard |
| `initial_sets[i].cs` | (none; use `cs`) | ✅ | FCParser.cpp:7116-7117 | Standard |
| `loads[i].cs` | (none; use `cs`) | ✅ | Multiple load routing paths (FCParser.cpp:7943-7944, 8245-8246, etc.) | Standard |

**Recommendation for writers**: Use canonical `cs` name exclusively; parser accepts both.

---

### Alternative Field Names & Silent Fallbacks

| Field Path | Variant | Behavior | Parser Check |
|------------|---------|----------|--------------|
| `contact_constraints.ignore_overlap` | `contact_constraints.ignoreoverlap` | Both parsed; use either | Lexical match in parser; both valid JSON keys |
| `gap_gas_fractions.user_defined` | Flexible array | Custom gas mixture specification | Parser processes as mole-fraction array with stride 4 (mole_frac, MW, diameter, temp) |

---

### Commented-Out Parser Branches (Not Yet Removed)

Some legacy checks remain commented in parser code but are not actively executed:

| Location | Condition | Status | Reason |
|----------|-----------|--------|--------|
| FCParser.cpp:6214 | `if (_root["settings"]["incompressibility"].asBool())` | ❌ COMMENTED | Old incompressibility mapping; still read at line 13124 instead |
| FCParser.cpp:6383-6390 | Spectral element element-type checks | ❌ COMMENTED | Legacy SEM element type override; modern path at line 12325 |
| FCParser.cpp:6399-6406 | Dynamics scheme checks for BEAM/SPRING | ❌ COMMENTED | Old validation; active path at lines 12488-12501 |

**Conclusion**: Commented-out code should not affect import; modern active paths handle these fields correctly.



## FC Format Mapping & Compatibility Matrix

This section documents the relationship between writer (FFidesysCaseWriter.cpp), reader (FCParser.cpp), and specification to identify mismatches and data consistency issues.

### Field Write/Read/Document Status

| Field | Written | Read | Documented | Status | Note |
|-------|---------|------|------------|--------|------|
| `header` | ✅ | ✅ | ✅ | ACTIVE | Format version, binary flag, type sizes |
| `mesh` | ✅ | ✅ | ✅ | ACTIVE | Nodes, elements, connectivity |
| `blocks` | ✅ | ✅ | ✅ | ACTIVE | Material/property assignments per element |
| `materials` | ✅ | ✅ | ✅ | ACTIVE | Material properties (v3 grouped layout) |
| `property_tables` | ✅ | ✅ | ✅ | ACTIVE | Shell/beam/spring sections, lump mass |
| `imported_sections` | ✅ | ✅ | ✅ | ACTIVE | External beam cross-sections |
| `coordinate_systems` | ✅ | ✅ | ✅ | ACTIVE | Local coordinate system definitions |
| `sets` | ✅ | ✅ | ✅ | ACTIVE | Named node/side sets for BC application |
| `contacts` | ✅ | ✅ | ✅ | ACTIVE | General contact pair definitions |
| `coupling_constraints` | ✅ | ✅ | ✅ | ACTIVE | RBE2/RBE3/MPC definitions |
| `contact_constraints` | ✅ | ✅ | ✅ | ACTIVE | Tied/friction contact pairs |
| `periodic_constraints` | ✅ | ✅ | ✅ | ACTIVE | Cyclic/periodic symmetry BCs |
| `receivers` | ✅ | ✅ | ✅ | ACTIVE | Output sensor nodes |
| `initial_sets` | ✅ | ✅ | ✅ | ACTIVE | Initial conditions (velocity, temperature) |
| `settings` | ✅ (passthrough) | ✅ | ✅ | ACTIVE | Analysis settings (mostly pass-through from UI) |
| `orientations` | ❓ | ❓ | ✅ | UNKNOWN | Element material orientations; check writer/reader |
| `restraints` | ✅ (via `writeGeneralBCs`) | ✅ | ✅ | ACTIVE | Legacy `writeRestraints()` path is commented out, but export goes through `writeGeneralBCs()` |
| `load_sets` | ❌ DISABLED | ❌ | ✅ | NOT USED | Writer code commented out; no parser support |
| `loads` | ✅ (via `writeGeneralBCs`) | ✅ | ✅ | ACTIVE | Legacy `writeLoads()` path is commented out, but export goes through `writeGeneralBCs()` |
| `restraint_sets` | ❌ DISABLED | ❌ | ✅ | NOT USED | Writer code commented out; no parser support |

**Risk Assessment:**
- **MEDIUM RISK**: Legacy `writeRestraints`/`writeLoads` paths are commented out, but BC export is performed via `writeGeneralBCs()` (writer line 197). Keep this routing in mind when debugging UI export.
- **MEDIUM RISK**: `orientations` field status unclear; needs cross-reference verification.

### Critical Field Mismatches

#### 1. **Written but NOT Read**
None identified. All active writer paths have corresponding parser logic.

#### 2. **Read but NOT Written**
- `orientations` (status unclear; verify against mesh orientation export)

#### 3. **Disabled Legacy Writer Paths (Commented Out)**
All in `FFidesysCaseWriter.cpp` write() method lines 172–195:
- `writeRestraints()` (line 175, commented)
- `writeRestraintSets()` (line 181, commented)
- `writeLoads()` (line 189, commented)
- `writeLoadSets()` (line 189, commented)

**Alternative active path**: General BCs are exported via `writeGeneralBCs()` to top-level `restraints`/`loads` (line 197).

#### 4. **Legacy/Version-Dependent Reader Paths**

| Field | Legacy Layout | Current Layout | Parser Route |
|-------|---------------|-----------------|--------------|
| `materials` | v1/v2: `constants.*` flat (old enum indices) | v3: grouped properties (elasticity, plasticity, thermal, ...) | FillMaterials() checks `header.version` and routes to FillMaterialsV1/V2/V3 (FCParser.cpp:4552-4562) |
| `mesh` | Old packed connectivity format | Current format with elem_types, elem_blocks, etc. | FillMesh() routes to _fillMeshOld() or _fillMeshUnique() (FCParser.cpp:5904-5908) |

---

## Sentinel & Branch Values

This section documents numeric and string values that trigger special processing logic (enum branches, optional field parsing, etc.).

### Numeric Sentinel Values (Element/Node BC Encoding)

| Value | Field | Name | Semantic Meaning | Branch/Usage |
|-------|-------|------|------------------|--------------|
| `-1` | `SIDE_ID_FOR_ELEMENT` constant | Element-level BC marker | Indicates BC applies to element bulk, not a surface | FCParser.cpp:62; FFidesysCaseWriter.cpp:48 |
| `-2` | `SIDE_ID_FOR_NODE` constant | Node-level BC marker | Indicates BC applies to a node | FCParser.cpp:63; FFidesysCaseWriter.cpp:48 |
| `-1` | `contact_constraints.distance` | Unlimited tie distance | No maximum distance check for tied contact | [fc-input-format.md] contact section; typical usage: `"distance": -1` |
| `0` | `block.material_id` | Unassigned material | Error state; block must have valid material | FillBlocks() validation |
| `0` | `contact_constraints.friction` | Frictionless contact | Coulomb friction coefficient = 0 | Contact enforcement logic |

### Dependent Value Routing (Material Constants)

**const_types (material property dependency encoding):**

Determines how property values in `constants` array and `const_dep` array are interpreted:

| Code | Name | Value Source | Tabular Data | Branch Logic |
|------|------|--------------|--------------|--------------|
| `0` | CONSTANT | `constants[i]` (scalar) | None (empty `const_dep[i]`) | Direct value; no interpolation |
| `1-5` | TABULAR_X, TABULAR_Y, TABULAR_Z, TABULAR_TIME, TABULAR_TEMPERATURE | Y-values in `constants[i]`; X-values in `const_dep[i]` | Paired argument points | Interpolate `constants[i]` using `const_dep[i]` as lookup table argument |
| `6` | FORMULA | Formula string in `constants[i]` | None | Parse and evaluate formula at runtime |
| `7` | TABULAR_FREQUENCY | Y-values in `constants[i]`; frequency points in `const_dep[i]` | Harmonic response data | Frequency-dependent interpolation |
| `8` | TABULAR_STRAIN | Y-values in `constants[i]`; strain points in `const_dep[i]` | Stress-strain curve | Strain-dependent hardening |
| `10` | TABULAR_ELEMENT_ID | Varies by element ID | Element-dependent map in `const_dep[i]` | Distribute constant per element ID |
| `11` | TABULAR_NODE_ID | Varies by node ID | Node-dependent map in `const_dep[i]` | Distribute constant per node ID |
| `12` | TABULAR_MODE_ID | Varies by mode/eigenvalue index | Mode-dependent map in `const_dep[i]` | Distribute constant per mode (transient/harmonic) |

**Example: Hook elasticity with temperature-dependent Young's modulus**
```json
{
  "elasticity": [{
    "type": 0,
    "const_names": [0, 1],
    "const_types": [5, 0],
    "const_dep_size": [10, 0],
    "constants": "base64_[E_val_0, E_val_1, ..., E_val_9, nu]",
    "const_dep": ["base64_[T_0, T_1, ..., T_9]", ""]
  }]
}
```

### String-Based Sentinel & Mode Selection

| Value/Field | Condition | Semantic | Branch/Feature |
|------------|-----------|----------|-----------------|
| `apply_to: "all"` | Loads, restraints, initial_sets | Apply to every node/element in dataset | Parser checks for string "all" vs. array (FCParser.cpp usage pattern) |
| `method: "auto"` | `contact_constraints`, `coupling_constraints` | Auto-select enforcement method | Solver picks penalty/Lagrange/MPC at runtime |
| `method: "penalty"` | Contact/coupling | Use penalty stiffness parameters | `normal_stiffness`, `tangent_stiffness`, `damping` required |
| `method: "pure_lagrangian"` \| `"aug_lagrangian"` | Contact/coupling | Use Lagrange multiplier method | `lagrange_settings` object required (see contact_constraints section) |
| `settings.dynamics.scheme: "explicit"` | Dynamics | Central-difference time integration | Explicit code path; FCParser.cpp:6399-6406 (legacy commented), active at 12488 |
| `settings.dynamics.scheme: "implicit"` | Dynamics | Newmark implicit time integration | Implicit code path; FCParser.cpp:12501 (active) |
| `contact_constraints.type: "tied_tangent"` | Contact | Tied contact with tangential slip allowed | Affects `preload` interpretation |

---

