# Changelog

## 1.2.3 [2026-05-13 20:46:06]

### Изменено

- **FC_ELEMENT_TYPES**: структура `FCElementType` обновлена под уточнённую спецификацию FidesysCase: `fc_id` → `code`, `nodes` → `nodes_count`, `facets` → `faces`; добавлены `nodes_coords` и `vertices_count`; поле `tetras` удалено.
- **FC_ELEMENT_TYPES**: геометрия элементов пересчитана по `docs/fc-input-format 2.md` для FEM/SEM solid, shell, beam/string, spring, point/lumpmass элементов; `edges` и `faces` приведены к каноническому порядку узлов.
- **FC_ELEMENT_TYPES**: исходные данные справочника вынесены в табличный список строк, а `List[FCElementType]` формируется из него циклом.
- **FCMesh**: кодирование и декодирование сетки переведены на новые ключи `code` и `nodes_count`.
- **Документация**: LLM-контекст обновлён для нового формата `FCElementType`.

### Исправлено

- Убраны устаревшие упоминания `facets`/`tetras` из черновых комментариев `fc_addons.py`.

## 1.2.2 [2026-05-13 18:52:00]

### Добавлено

- **Материалы**: группы `kinematic_hardening` и `hsdf` в `FCMaterialPropertiesTypeLiteral`, `FC_MATERIAL_PROPERTY_NAMES_KEYS`, `FC_MATERIAL_PROPERTY_TYPES_KEYS`, `FCSrcMaterial`.
- **Материалы**: константы `COEF_SPECIFIC_HEAT` (thermal[2]), `EMISSIVITY` (thermal[3]), `TENSILE_STRAIN` (plasticity[1]), `TENSILE_STRAIN_COMPR` (plasticity[6]).
- **Нагрузки**: типы `GravityMassForce` (6), `FaceSloshingBC` (45), `SegmentSloshingBC` (46), `PointDeadForce` (47), `PointTrackingForce` (48), `PointHydrodynamicForce` (49) в `FC_LOADS_TYPES_KEYS`.
- **Coupling constraints**: тип `CONSTRAINT_EQUATION` (6) в `FC_COUPLING_TYPES_KEYS`.
- **Contact methods**: `pure_lagrangian` и `aug_lagrangian` в `FC_CONTACT_METHODS`.
- **FCBlock**: опциональное поле `orientation_id` (decode/encode).
- **FCLoad**: опциональные поля `step` и `case` (decode/encode).
- **FCRestraint**: опциональное поле `case` (decode/encode).
- **FCInitialSet**: поле `name` (decode/encode).
- **FCModel**: pass-through поля `orientations` и `imported_sections` (`List[Dict[str, Any]]`).
- **Header**: `FCTYPE: 8` в default `header.types`.
- **FCConstraint**: параметр `kind: FCConstraintKind` (`'contact'`/`'coupling'`/`'periodic'`) в `decode()`/`encode()` для корректного маппинга типов.
- **FCConstraintKind**: новый экспортируемый тип-литерал.

### Изменено

- **FCReceiver.type**: `int` → `str`. Decode маппит через `FC_RECEIVER_TYPES_KEYS`, encode — через `FC_RECEIVER_TYPES_CODES`. Пример: `0` → `"DISPLACEMENT"`.
- **FCPropertyTable.type**: `int` → `str`. Decode маппит через `FC_PROPERTY_TABLE_TYPES_KEYS`, encode — через `FC_PROPERTY_TABLE_TYPES_CODES`. Пример: `0` → `"SHELL"`.
- **FCConstraint.type**: `Union[int, str]` → `str`. Для coupling/periodic типы маппятся из int-кодов в строки. Пример: coupling `0` → `"ELASTICITY"`, periodic `0` → `"ALL"`.
- **FCData.type**: `Union[int, str]` → `str`. Magic numbers заменены строками: `0` → `"CONSTANT"`, `6` → `"FORMULA"`, `-1` → `"TABLE"`.
- **FCData.encode()**: возвращает `Tuple[str, int, str]` вместо `Tuple[str, Union[int, str], str]` для не-табличных данных.
- Нормализация `dependency_type: ""` → `0` в тестовых данных `ultracube.fc`.

## 1.2.0 [2026-05-10 20:00:00]

Релиз версии 1.2 — полное установление и фиксация публичного API.

### Ключевые изменения

- **Фиксация публичного API**: все 16 доменных классов (`FCModel`, `FCMesh`, `FCBlock`, `FCCoordinateSystem`, `FCMaterial`, `FCMaterialProperty`, `FCPropertyTable`, `FCLoad`, `FCRestraint`, `FCInitialSet`, `FCConstraint`, `FCReceiver`, `FCSet`, `FCValue`, `FCData`, `FCDependencyColumn`) и 28 справочных констант стабилизированы и покрыты тестами.
- **Перенос всех флагов и констант из спецификации**: 14 новых справочных констант (`FC_CONTACT_TYPES`, `FC_CONTACT_METHODS`, `FC_COUPLING_TYPES_*`, `FC_PERIODIC_TYPES_*`, `FC_PROPERTY_TABLE_TYPES_*`, `FC_BEAM_SECTION_TYPES_*`, `FC_RECEIVER_TYPES_*`, `FC_COORDINATE_SYSTEM_TYPES`), дополнительные поля `FCRestraint.step`, `FCReceiver.output_step`, `FCPropertyTable.name`.
- **Обновление LLM-контекста**: `FC_MODEL_LLM_CONTEXT.md` и `FC_MODEL_API_INDEX_TLDR.md` актуализированы до версии 1.2, включая compress API, методы remap, полный перечень констант и рецепты.
- **`FCModel.compress()`**: нормализация всех 13 индексных пространств модели к каноническому виду `[1, 2, 3, ...]` с обновлением всех перекрёстных ссылок (coordinate systems, materials, property tables, blocks, nodes, elements, loads, restraints, initial sets, constraints, receivers, nodesets, sidesets). Методы `FCValue.remap()`, `FCValue.remap_pairs()`, `FCData.remap_column()`.
- **192 unit-теста**: полное покрытие всех публичных классов, констант, encode/decode, roundtrip на реальных `.fc` файлах, compress + идемпотентность.
- **Исправлено**: `FCInitialSet.flags` сохраняет исходные `List[int]` (0/1) вместо ошибочного маппинга через restraint-коды.
- **Документация**: `AGENTS.md`, `FC_MODEL_LLM_CONTEXT.md`, `FC_MODEL_API_INDEX_TLDR.md`, `CHANGELOG.md` + `CHANGELOG_ARCHIVE.md`.

Подробная история изменений линии 1.1.x — в `CHANGELOG_ARCHIVE.md`.
