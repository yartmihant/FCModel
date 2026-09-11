# Mesh audit coverage

`audit_mesh.audit(data)` checks the sections assigned by `CONTRACT.md` directly
against `docs/FC_INPUT_FORMAT.md`:

- `mesh` (lines 64–82): object and count types, required current arrays,
  JSON/Base64 representation selected by `header.binary`, `header.types` byte
  sizes, array lengths, the explicitly flat `nodes_count*3` coordinate buffer,
  all element codes listed in the element tables (including shell, beam,
  spring, lump-mass and point codes), and known FEM connectivity arities.
  `elem_types` uses one unsigned byte per element, independently of
  `header.types.int`, as approved in the specification correction. Unknown mesh fields are reported as
  ambiguity. Rules: `MESH.*`.
- `coordinate_systems` (lines 974–987): record shape, id/type fields,
  coordinate buffer sizes, listed type names, and the documented global `id=1`.
  Rules: `CS.*`.
- `sets` (lines 989–1009): node/side set record fields, payload encoding and
  `apply_to_size` (side pairs count twice in binary flat buffers). `name` is
  type-checked when present and is not invented as a required field. Rules:
  `SET.*`.
- `blocks` (lines 1012–1027): array/record shape, block id presence and
  uniqueness, coordinate/material/property references when their target tables
  are present, sentinel `material_id=0`, documented property_id=-1 (no special properties), other ambiguous property sentinels, the
  alternative step-dependent material object, and integer `steps`. Rules:
  `BLOCK.*`.

Versions below 3 are reported as `MESH.LEGACY_LAYOUT` with severity `legacy`,
because the specification explicitly documents an old packed mesh layout
(lines 2076–2081). Common JSON/type checks still run, while the undocumented
old field set is one `MESH.LEGACY_LAYOUT_FIELDS` ambiguity rather than a v3
unknown-field failure. Unknown element codes are `ambiguity`, since the
current excerpt does not establish a closed set covering every solver
extension.

The audit does not validate geometry, element orientation, physical
correctness, connectivity semantics beyond documented node arities, or byte
order. In binary mode it validates Base64 and byte lengths but does not decode
integer references: the specification does not fully fix endianness, so
cross-reference conclusions are limited to plain JSON. Missing
optional sections are accepted; an empty coordinate-system section does not
itself require a global record. A non-empty section without id=1 is reported
as ambiguity, and id=1 with a non-Cartesian type is a violation. Plain
connectivity is checked as flat packed data when numeric and known FEM arities
are available; nested corpus layouts are reported as ambiguity. This coverage limitation is documented here and no longer produces a
per-file finding, as requested by the user. Integer-valued JSON floats are
accepted for integer fields; binary widths are unchanged.

## Финальная интеграция

Для version<3 проверки v3 ширины elem_types/connectivity отключены: структура old packed layout документом не задана. Это относится и к раннему замечанию о cube_multi.fc в review_mesh.json — оно отменено итоговой интеграцией. Добавлены ambiguity REF.DUPLICATE_ID для повторных material/property-table/CS ID и проверка целочисленности plain ID/connectivity массивов. Сумма FEM арностей используется только если известны все типы; при неполной таблице не подставляется нулевая арность неизвестного типа.
