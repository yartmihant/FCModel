# Changelog

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


