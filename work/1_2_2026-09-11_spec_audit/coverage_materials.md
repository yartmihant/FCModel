# Materials and property tables coverage

`audit_materials.audit(data)` audits only `materials` and `property_tables` and
does not load files or call the FCModel implementation. It emits the contract
finding shape and keeps `actual` short (types, lengths, codes, or decoded
lengths).

The implementation covers the material record and grouped layout described in
`docs/FC_INPUT_FORMAT.md:491`, group type tables and `const_names` tables in
the materials section, dependency codes and component encoding at lines
`1812-1838`, documented flat v1/v2 material constants at `1846-1970`, and the
property-table/type/beam-section/layer schemas at `811-976`.

The numeric `const_names` sets were automatically compared with the published
tables in `docs/FC_INPUT_FORMAT.md:603-810`: missing codes = none in the
implementation, extra codes = none. A corpus code absent from the published
table is still emitted as `ambiguity`, since the document does not declare the
tables closed; this preserves evidence such as elasticity codes 11-13.

Rules include record and section shape, scalar/list/bool types, known group and
property-table codes, component-array alignment, dependency-code shape,
constant/formula versus table encoding, Base64 validity and decoded table
lengths, beam section codes, type-specific property field types and spring
codes, geometry numeric values, unknown nested fields, shell-only layers, layer
field types, lump-mass mutual exclusions, and `mass_distribution` branch
values. Tabular dependent-value payload lengths are compared with
`const_dep_size`; missing `header.types.double` produces an ambiguity rather
than an assumed byte width. Component dependency lists reject CONSTANT and
FORMULA codes, and `const_dep` must be the documented empty string for
constant/formula components.

Groups with no published type table (`hsdf`, `kinematic_hardening`, and
`swelling`) emit `MAT.GROUP_SCHEMA` ambiguity when present. Unknown numeric
enum values remain ambiguity unless a separate direct type or shape rule is
violated. For format versions below 3, object-shaped material groups are
reported as `legacy` while v3 object-shaped groups remain violations.

The audit accepts numeric JSON arrays for payloads because the main
specification permits plain JSON when `header.binary=false`; Base64 payloads
are checked independently using the `header.types.double` size. It does not
infer endianness, physical ranges, required material combinations, required
properties, or geometry completeness. It does not treat the published
`const_names` lists as exhaustive: corpus codes absent from those tables are
reported as `ambiguity`. Unknown nested fields are reported as `ambiguity`,
while repeated group components and non-array grouped fields are direct
violations of the v3 shape. The documented flat `materials[i].constants`
object is reported as `legacy`.

No source files, corpus files, documentation, VERSION, or changelog were
modified by the audit.
