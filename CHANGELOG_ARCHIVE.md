# Changelog Archive

Архив подробных записей CHANGELOG предыдущих линий версий.

---

## Линия 1.1.x

### 1.1.22 [2026-05-10 18:00:00]

#### Добавлено
- **Метод `FCModel.compress()`** — нормализует все индексные пространства сущностей в модели к каноническому виду `[1, 2, 3, ...]`. Переиндексирует: coordinate systems, materials, property tables, blocks, nodes, elements, loads, restraints, initial sets, constraints, receivers, nodesets, sidesets. Обновляет все перекрёстные ссылки (cs_id, material_id, property_id, element.block, element.nodes, element.parent_id, FCValue apply-массивы, sideset elem_id, TABULAR_NODE_ID/ELEMENT_ID в FCData).
- **Методы `FCValue.remap(mapping)` и `FCValue.remap_pairs(mapping)`** — переиндексация значений в массивах FCValue (все элементы / только первый столбец пар).
- **Метод `FCData.remap_column(dep_type_name, mapping)`** — переиндексация ID в табличных столбцах зависимости.
- **Метод `FCModel._collect_all_data()`** — внутренний хелпер, собирающий все FCData из нагрузок, закреплений, начальных условий и материалов.
- **Unit-тесты**: `test_compress.py` — 68 тестов, покрывающих все 13 индексных пространств, перекрёстные ссылки, формулы, roundtrip, идемпотентность, табулярные зависимости, множественные типы элементов, пустые коллекции, реальные .fc файлы.

### 1.1.21 [2026-05-10 12:00:00]

#### Добавлено
- **Константы**: 14 новых справочных констант из спецификации — `FC_CONTACT_TYPES`, `FC_CONTACT_METHODS`, `FC_COUPLING_TYPES_KEYS/CODES`, `FC_PERIODIC_TYPES_KEYS/CODES`, `FC_PROPERTY_TABLE_TYPES_KEYS/CODES`, `FC_BEAM_SECTION_TYPES_KEYS/CODES`, `FC_RECEIVER_TYPES_KEYS/CODES`, `FC_COORDINATE_SYSTEM_TYPES`.
- **Поля**: `FCRestraint.step: Optional[List[int]]` — шаги активности закрепления.
- **Поля**: `FCReceiver.output_step: Optional[int]` — интервал вывода результатов.
- **Поля**: `FCPropertyTable.name: str` — описание таблицы свойств.
- **Unit-тесты**: 125 тестов pytest в 7 файлах (test_value, test_data, test_materials, test_mesh, test_conditions, test_model, test_constants), покрывающие все публичные классы и константы.
- **Документация**: `AGENTS.md` — руководство для ИИ-агентов (русский).
- **Документация**: `FC_MODEL_LLM_CONTEXT.md` — полное описание API для LLM (английский, ~400 строк).
- **Документация**: `CHANGELOG.md` — журнал изменений проекта.

#### Изменено
- **Документация**: `FC_MODEL_API_INDEX_TLDR.md` — обновлён компактный индекс API, добавлены все новые константы и поля.
- **Документация**: `README.md` — исправлен пример быстрого старта (`FCModel("path")` → `FCModel.load("path")`).
- **Экспорт**: `__init__.py __all__` — добавлены все 14 новых символов констант.

#### Исправлено
- **Баг**: `FCInitialSet.flags` декодировался через `FC_RESTRAINT_FLAGS_KEYS` (маппинг 0→"EmptyRestraint", 1→"Displacement") вместо сохранения исходных 0/1 значений по спецификации. Исправлено на `list(src['flag'])`.

#### Убрано
- Удалён устаревший файл `LLM_API_INDEX_FC_MODEL.json` (заменён на `FC_MODEL_LLM_CONTEXT.md` и `FC_MODEL_API_INDEX_TLDR.md`).

---

### 1.1.0 [Ретроспективный релиз]

Начальная линия версий, восстановленная постфактум. Changelog-политика внедрена начиная с 1.1.21.

#### Возможности fc_model 1.1
- **Объектная модель формата Fidesys Case (.fc)**: полный набор доменных классов — `FCModel`, `FCMesh`, `FCBlock`, `FCCoordinateSystem`, `FCMaterial`, `FCMaterialProperty`, `FCPropertyTable`, `FCLoad`, `FCRestraint`, `FCInitialSet`, `FCConstraint`, `FCReceiver`, `FCSet`, `FCValue`, `FCData`, `FCDependencyColumn`.
- **Encode/decode**: каждый класс реализует `decode(src) → Entity` и `encode() → dict` для roundtrip-совместимости с JSON+Base64.
- **File I/O**: `FCModel.load(path)` / `FCModel.save(path)` — чтение и запись `.fc` файлов.
- **Хелперы модели**: `add_material`, `add_load`, `add_restraint`, `add_initial_set`, `add_nodeset`, `add_sideset`, `add_coordinate_system`, `add_material_property` — автоназначение ID.
- **Справочные константы**: `FC_MATERIAL_PROPERTY_NAMES/TYPES_KEYS/CODES`, `FC_LOADS_TYPES_KEYS/CODES`, `FC_RESTRAINT_FLAGS_KEYS/CODES`, `FC_INITIAL_SET_TYPES_KEYS/CODES`, `FC_ELEMENT_TYPES_KEYID/KEYNAME`, `FC_DEPENDENCY_TYPES_KEYS/CODES`.
- **FCMesh**: `add()`, `compress()`, `reindex()`, `__len__`, `__iter__`, `__contains__`, `__getitem__`, `__setitem__`, `max_id`, `nodes_list`.
- **FCData**: фабричные методы `constant()`, `formula()`; табличные зависимости с `FCDependencyColumn`.
- **PEP 561**: `py.typed` для строгой типизации.
- **Расширения сверх спецификации**: элементы BAR2/3, CABLE2/3; типы материалов VOIGT_*, VP, VS; группа `swelling`.
