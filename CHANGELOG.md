# Changelog

## 1.1.21 [2026-05-10 12:00:00]

### Добавлено
- **Константы**: 14 новых справочных констант из спецификации — `FC_CONTACT_TYPES`, `FC_CONTACT_METHODS`, `FC_COUPLING_TYPES_KEYS/CODES`, `FC_PERIODIC_TYPES_KEYS/CODES`, `FC_PROPERTY_TABLE_TYPES_KEYS/CODES`, `FC_BEAM_SECTION_TYPES_KEYS/CODES`, `FC_RECEIVER_TYPES_KEYS/CODES`, `FC_COORDINATE_SYSTEM_TYPES`.
- **Поля**: `FCRestraint.step: Optional[List[int]]` — шаги активности закрепления.
- **Поля**: `FCReceiver.output_step: Optional[int]` — интервал вывода результатов.
- **Поля**: `FCPropertyTable.name: str` — описание таблицы свойств.
- **Unit-тесты**: 125 тестов pytest в 7 файлах (test_value, test_data, test_materials, test_mesh, test_conditions, test_model, test_constants), покрывающие все публичные классы и константы.
- **Документация**: `AGENTS.md` — руководство для ИИ-агентов (русский).
- **Документация**: `FC_MODEL_LLM_CONTEXT.md` — полное описание API для LLM (английский, ~400 строк).
- **Документация**: `CHANGELOG.md` — журнал изменений проекта.

### Изменено
- **Документация**: `FC_MODEL_API_INDEX_TLDR.md` — обновлён компактный индекс API, добавлены все новые константы и поля.
- **Документация**: `README.md` — исправлен пример быстрого старта (`FCModel("path")` → `FCModel.load("path")`).
- **Экспорт**: `__init__.py __all__` — добавлены все 14 новых символов констант.

### Исправлено
- **Баг**: `FCInitialSet.flags` декодировался через `FC_RESTRAINT_FLAGS_KEYS` (маппинг 0→"EmptyRestraint", 1→"Displacement") вместо сохранения исходных 0/1 значений по спецификации. Исправлено на `list(src['flag'])`.

### Убрано
- Удалён устаревший файл `LLM_API_INDEX_FC_MODEL.json` (заменён на `FC_MODEL_LLM_CONTEXT.md` и `FC_MODEL_API_INDEX_TLDR.md`).

