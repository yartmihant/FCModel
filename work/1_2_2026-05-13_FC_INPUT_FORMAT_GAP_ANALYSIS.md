# Анализ расхождений: fc-input-format 1.md vs текущая реализация fc_model

**Дата**: 2026-05-13 18:30  
**Версия библиотеки**: 1.2.1  
**Источник спецификации**: `docs/fc-input-format 1.md` (получен от разработчика)

---

## Содержание

1. [Отсутствующие top-level секции](#1-отсутствующие-top-level-секции)
2. [Отсутствующие группы материалов](#2-отсутствующие-группы-материалов)
3. [Отсутствующие константы материалов](#3-отсутствующие-константы-материалов)
4. [Расхождения в именах констант](#4-расхождения-в-именах-констант)
5. [Отсутствующие типы нагрузок](#5-отсутствующие-типы-нагрузок)
6. [Отсутствующие типы coupling constraints](#6-отсутствующие-типы-coupling-constraints)
7. [Отсутствующие методы контактных ограничений](#7-отсутствующие-методы-контактных-ограничений)
8. [Отсутствующие поля в блоках](#8-отсутствующие-поля-в-блоках)
9. [Отсутствующие поля в нагрузках и ГУ](#9-отсутствующие-поля-в-нагрузках-и-ГУ)
10. [Отсутствующие поля в initial_sets](#10-отсутствующие-поля-в-initial_sets)
11. [Header: отсутствует FCTYPE](#11-header-отсутствует-fctype)
12. [FCSettings TypedDict: неполнота](#12-fcsettings-typeddict-неполнота)
13. [Расширения библиотеки (нет в спецификации)](#13-расширения-библиотеки-нет-в-спецификации)
14. [Сводная таблица](#14-сводная-таблица)

---

## 1. Отсутствующие top-level секции

Спецификация определяет два top-level поля, которых нет в `FCSrcModel` и `FCModel`:

| Поле | Описание по спецификации | Статус |
|------|--------------------------|--------|
| `orientations` | Element material orientation definitions | ❌ Не реализовано |
| `imported_sections` | Externally imported beam cross-sections | ❌ Не реализовано |

**Воздействие**: Модели с ориентациями материалов или импортированными сечениями балок потеряют эти данные при roundtrip через библиотеку. `FCModel.decode()` игнорирует эти ключи, `FCModel.encode()` не записывает их.

---

## 2. Отсутствующие группы материалов

Спецификация определяет 12 property-групп для материалов. Библиотека (`FCMaterialPropertiesTypeLiteral`) поддерживает 10 из 12:

| Группа | Код | Статус |
|--------|-----|--------|
| `kinematic_hardening` | — | ❌ Не реализовано |
| `hsdf` | — | ❌ Не реализовано |

**Воздействие**: Материалы с группами `kinematic_hardening` или `hsdf` будут потеряны при decode, т.к. эти имена не входят в `FC_MATERIAL_PROPERTY_NAMES_KEYS` и `FC_MATERIAL_PROPERTY_TYPES_KEYS`.

---

## 3. Отсутствующие константы материалов

### 3.1. thermal — отсутствующие свойства

| Индекс | Имя (по спецификации) | Модель | Статус |
|--------|----------------------|--------|--------|
| 2 | `COEF_SPECIFIC_HEAT` | ISOTROPIC | ❌ Отсутствует |
| 3 | `EMISSIVITY` | ISOTROPIC | ❌ Отсутствует |

Библиотека `fc_materials.py` → `FC_MATERIAL_PROPERTY_NAMES_KEYS["thermal"]` содержит индексы `{0, 1, 5, 9, 13–20}`, но не содержит `2` и `3`.

### 3.2. plasticity — отсутствующие свойства

| Индекс | Имя (по спецификации) | Модель | Статус |
|--------|----------------------|--------|--------|
| 1 | `TENSILE_STRAIN` | MISES | ❌ Отсутствует |
| 6 | `TENSILE_STRAIN_COMPR` | DRUCKER_PRAGER, MOHR_COULOMB | ❌ Отсутствует |

Библиотека `FC_MATERIAL_PROPERTY_NAMES_KEYS["plasticity"]` содержит индексы `{0, 5, 7, 8, 9, 21, 22, 23}`, но не `1` и `6`.

**Воздействие**: Decode материала с этими свойствами завершится ошибкой (KeyError) или молча подставит числовой код вместо строкового имени.

---

## 4. Расхождения в именах констант

### 4.1. plasticity[22]: DPC_N vs DPC_B

| Индекс | Спецификация | Библиотека | Статус |
|--------|-------------|------------|--------|
| 22 | `DPC_B` | `DPC_N` | ⚠️ Расхождение |

Файл: `fc_materials.py`, строка в `FC_MATERIAL_PROPERTY_NAMES_KEYS["plasticity"]`:
```python
22: "DPC_N",  # DRUCKER_PRAGER_CREEP
```
Спецификация указывает имя `DPC_B`.

**Приоритет**: Требует уточнения у разработчика — что является каноническим именем.

---

## 5. Отсутствующие типы нагрузок

`FC_LOADS_TYPES_KEYS` в `fc_conditions.py` не содержит 6 типов, описанных в спецификации:

| Код | Имя | Категория | Описание | Статус |
|-----|-----|-----------|----------|--------|
| 6 | `GravityMassForce` | Volume/element | Гравитация (ax, ay, az), 3 компоненты | ❌ Отсутствует |
| 45 | `FaceSloshingBC` | Face | Sloshing ГУ (0 компонент данных) | ❌ Отсутствует |
| 46 | `SegmentSloshingBC` | Segment | Sloshing ГУ (0 компонент данных) | ❌ Отсутствует |
| 47 | `PointDeadForce` | Point | Точечная сила (6 компонент) | ❌ Отсутствует |
| 48 | `PointTrackingForce` | Point | Следящая точечная сила (6 компонент) | ❌ Отсутствует |
| 49 | `PointHydrodynamicForce` | Point | Гидродинамическая точечная сила (6 компонент) | ❌ Отсутствует |

**Воздействие**: Decode нагрузки с одним из этих типов вызовет `KeyError` в `FC_LOADS_TYPES_KEYS[src_load['type']]`.

**Примечание**: Точечные нагрузки (47–49) используют `apply_to` как массив 3D-координат `[x, y, z, ...]`, а не ID узлов — это принципиально иная семантика.

---

## 6. Отсутствующие типы coupling constraints

| Код | Имя | Статус |
|-----|-----|--------|
| 6 | `CONSTRAINT_EQUATION` | ❌ Отсутствует |

`FC_COUPLING_TYPES_KEYS` содержит коды 0–5, но не 6. Спецификация описывает для этого типа сложную структуру `equation` с полями `rhs`, `terms[]` (node, dof, coefficient), а также `enforcement_method`, `stiffness`, `damping`.

**Воздействие**: Библиотека не может представить MPC-уравнения (general linear multipoint constraints). Decode не упадёт (тип хранится в `properties` как число), но значение не будет распознано.

---

## 7. Отсутствующие методы контактных ограничений

`FC_CONTACT_METHODS` содержит `["auto", "penalty", "mpc"]`.

Спецификация добавляет:

| Метод | Описание | Статус |
|-------|----------|--------|
| `pure_lagrangian` | Метод множителей Лагранжа, требует `lagrange_settings` | ❌ Отсутствует |
| `aug_lagrangian` | Дополненный Лагранжиан, требует `lagrange_settings` | ❌ Отсутствует |

Спецификация также описывает вложенный объект `lagrange_settings` с полями: `tangent_rate`, `criteria_smoothing`, `use_tangent`, `use_stick_predictor`, `overconstraint_normal`, `overconstraint_tangent`, `stability_normal`, `stability_tangent`, `shear_stress_limit`, `tensile_stress_limit`, `direction_tolerance`, `augmented_tolerance`.

**Воздействие**: Эти методы сохраняются в `properties["method"]` как строки, но не валидируются. Формально roundtrip работает, но нет поддержки на уровне API.

---

## 8. Отсутствующие поля в блоках

| Поле | Тип | Описание | Статус |
|------|-----|----------|--------|
| `orientation_id` | `int` | ID ориентации для анизотропных материалов | ❌ Не реализовано |

`FCBlock` содержит `id`, `cs_id`, `material_id`, `property_id`, `steps`, `material`. Поле `orientation_id` отсутствует.

**Воздействие**: Блоки с ориентациями потеряют `orientation_id` при roundtrip.

---

## 9. Отсутствующие поля в нагрузках и ГУ

### 9.1. FCLoad — отсутствующие поля

| Поле | Тип | Описание | Статус |
|------|-----|----------|--------|
| `step` | `[int]` | Шаги, на которых активна нагрузка | ❌ Отсутствует |
| `case` | `[int]` | Load cases | ❌ Отсутствует |

`FCSrcLoad` и `FCLoad` не содержат полей `step` и `case`. Спецификация описывает оба поля для всех нагрузок.

### 9.2. FCRestraint — отсутствующие поля

| Поле | Тип | Описание | Статус |
|------|-----|----------|--------|
| `case` | `[int]` | Load cases | ❌ Отсутствует |

`FCRestraint` имеет `step`, но не `case`.

### 9.3. FCInitialSet — отсутствующие поля

| Поле | Тип | Описание | Статус |
|------|-----|----------|--------|
| `name` | `str` | Human-readable IC name | ❌ Отсутствует |

`FCSrcInitialSet` и `FCInitialSet` не содержат поля `name`.

---

## 10. Отсутствующие поля в initial_sets

Уже описано в п. 9.3. `FCInitialSet` не имеет атрибута `name` и соответствующего поля в `FCSrcInitialSet`.

---

## 11. Header: отсутствует FCTYPE

Спецификация определяет в `header.types`:
```json
{
  "char": 1, "short_int": 2, "int": 4, "double": 8, "FCTYPE": 8
}
```

Библиотека по умолчанию (`__init__.py`, `FCModel.__init__`):
```python
"types": {"char": 1, "short_int": 2, "int": 4, "double": 8}
```

**Отсутствует**: `"FCTYPE": 8`.

**Воздействие**: При чтении существующего файла `FCTYPE` сохранится (через dict), но при создании новой модели с нуля он не будет записан. Парсер может ожидать это поле для корректного декодирования бинарных данных.

---

## 12. FCSettings TypedDict: неполнота

`FCSettings` в `__init__.py` описывает часть полей из спецификации. Следующие ключи из спецификации отсутствуют в TypedDict:

| Поле | Тип | Описание |
|------|-----|----------|
| `spectral_element` | `bool` | Использовать SEM |
| `spectral_order` | `int` | Порядок полинома для SEM (3–9) |
| `bc_tolerance` | `double` | Геометрический допуск для BC |
| `lump_agreed` | `bool` | Подавить предупреждение lump-mass |
| `viscosity` | `bool` | Включить вязкость |
| `xfem` | `bool` | Экспериментальный XFEM |
| `thermal_expansion` | `bool` | Effectiveprops: КТР |
| `poroelasticity` | `bool` | Effectiveprops: пороупругость |
| `permeability` | `bool` | Effectiveprops: проницаемость |
| `environment` | `dict` | Ref temperature |
| `link` | `dict` | Настройки incompatible mesh link |
| `mbd` | `dict` | Multi-body dynamics output |
| `table_interpolation` | `dict` | Пространственная интерполяция таблиц |
| `effectiveprops` | `dict` | Effectiveprops analysis settings |

**Воздействие**: Фактическое воздействие минимально — `settings` хранится как `Dict[str, Any]` и передаётся as-is. Но TypedDict не отражает полную структуру, что снижает пользу типизации.

---

## 13. Расширения библиотеки (нет в спецификации)

Следующие элементы присутствуют в библиотеке, но отсутствуют в спецификации `fc-input-format 1.md`. Это **допустимые расширения**, задокументированные в LLM-контексте:

### 13.1. Элементы

| fc_id | Имя | Описание |
|-------|-----|----------|
| 107 | `BAR2` | Bar element, линейный |
| 108 | `BAR3` | Bar element, квадратичный |
| 109 | `CABLE2` | Cable element, линейный |
| 110 | `CABLE3` | Cable element, квадратичный |

### 13.2. Константы материалов elasticity

| Индекс | Имя | Описание |
|--------|-----|----------|
| 11 | `VOIGT_YOUNG_MODULE` | Модуль Юнга (Voigt) |
| 36 | `VOIGT_POISSON_RATIO` | Коэффициент Пуассона (Voigt) |
| 79 | `VP` | P-wave velocity |
| 80 | `VS` | S-wave velocity |

### 13.3. Константы hardening

| Индекс | Имя | Описание |
|--------|-----|----------|
| 11 | `HARDENING_COMPR` | Multilinear hardening (compression) |

### 13.4. Константы preload (расширенный набор)

Библиотека содержит 49 констант preload (индексы 0–48), включая:
- `STRAIN_XX..XZ` (6–11)
- `PSI_XX..ZX` (12–20)
- `GRADIENT_XX..ZX` (21–29)
- `PLASTIC_STRAIN_XX..XZ` (30–35)
- `FINGER_STRAIN_XX..XZ` (36–41)
- `PLASTIC_STRAIN_MISES` (42)
- `THERMAL_STRESS_XX..XZ` (43–48)

Спецификация описывает только: `{0–5, 46–48}`.

### 13.5. Константы geomechanic (расширенные проницаемости)

Библиотека содержит дополнительные индексы, отсутствующие в спецификации:

| Индекс | Имя |
|--------|-----|
| 9 | `PERMEABILITY_YX` |
| 10 | `PERMEABILITY_YY` |
| 11 | `PERMEABILITY_YZ` |
| 12 | `PERMEABILITY_ZX` |
| 13 | `PERMEABILITY_ZY` |
| 14 | `PERMEABILITY_ZZ` |
| 17 | `PERMEABILITY_TL` |
| 18 | `PERMEABILITY_L` |

### 13.6. Restraint flag

| Код | Имя | Описание |
|-----|-----|----------|
| 16 | `Fluence` | ГУ по флюенсу (дозе) |

### 13.7. Swelling (пустая группа)

`swelling` определена в библиотеке как группа без констант и типов. Спецификация упоминает `swelling` в списке групп материалов, но не описывает её содержимое.

---

## 14. Сводная таблица

### Критичность

| # | Элемент | Категория | Критичность | Файл |
|---|---------|-----------|-------------|------|
| 1 | Top-level `orientations` | Отсутствует секция | 🔴 Высокая | `__init__.py` |
| 2 | Top-level `imported_sections` | Отсутствует секция | 🔴 Высокая | `__init__.py` |
| 3 | Материалы: `kinematic_hardening` | Отсутствует группа | 🔴 Высокая | `fc_materials.py` |
| 4 | Материалы: `hsdf` | Отсутствует группа | 🟡 Средняя | `fc_materials.py` |
| 5 | Load type 6 `GravityMassForce` | Отсутствует тип | 🔴 Высокая | `fc_conditions.py` |
| 6 | Load types 45–46 `*SloshingBC` | Отсутствует тип | 🟡 Средняя | `fc_conditions.py` |
| 7 | Load types 47–49 `Point*Force` | Отсутствует тип | 🟡 Средняя | `fc_conditions.py` |
| 8 | Coupling type 6 `CONSTRAINT_EQUATION` | Отсутствует тип | 🔴 Высокая | `fc_constraint.py` |
| 9 | Contact methods `pure/aug_lagrangian` | Отсутствует метод | 🟡 Средняя | `fc_constraint.py` |
| 10 | `thermal[2]` COEF_SPECIFIC_HEAT | Отсутствует константа | 🔴 Высокая | `fc_materials.py` |
| 11 | `thermal[3]` EMISSIVITY | Отсутствует константа | 🔴 Высокая | `fc_materials.py` |
| 12 | `plasticity[1]` TENSILE_STRAIN | Отсутствует константа | 🔴 Высокая | `fc_materials.py` |
| 13 | `plasticity[6]` TENSILE_STRAIN_COMPR | Отсутствует константа | 🔴 Высокая | `fc_materials.py` |
| 14 | `plasticity[22]` DPC_N→DPC_B | Расхождение имени | ⚠️ Уточнить | `fc_materials.py` |
| 15 | Block `orientation_id` | Отсутствует поле | 🟡 Средняя | `fc_blocks.py` |
| 16 | Load `step`, `case` | Отсутствует поле | 🟡 Средняя | `fc_conditions.py` |
| 17 | Restraint `case` | Отсутствует поле | 🟡 Средняя | `fc_conditions.py` |
| 18 | InitialSet `name` | Отсутствует поле | 🟢 Низкая | `fc_conditions.py` |
| 19 | Header `FCTYPE` | Отсутствует в default | 🟢 Низкая | `__init__.py` |
| 20 | FCSettings неполнота | TypedDict | 🟢 Низкая | `__init__.py` |

### Статистика

- **Отсутствующие top-level секции**: 2
- **Отсутствующие группы материалов**: 2
- **Отсутствующие константы материалов**: 4
- **Расхождения в именах**: 1
- **Отсутствующие типы нагрузок**: 6
- **Отсутствующие типы constraints**: 1
- **Отсутствующие методы contacts**: 2
- **Отсутствующие поля структур**: 5
- **Расширения библиотеки (не в спецификации)**: 7 категорий

---

## 15. Оценка трудоёмкости исправлений для корректного roundtrip

Цель: обеспечить, чтобы `FCModel.load() → FCModel.save()` не терял данные из файлов, соответствующих новой спецификации. Данные внутри могут храниться «сырыми» (dict/list), полная семантическая типизация не требуется.

### Категория A: Одна строка в словаре констант

Правки сводятся к добавлению записи `код: "ИМЯ"` в существующий словарь. Никаких структурных изменений. Все перечисленные правки — в `fc_materials.py` и `fc_conditions.py`.

| # | Что | Файл | Правка |
|---|-----|------|--------|
| 10 | `thermal[2]` COEF_SPECIFIC_HEAT | `fc_materials.py` | +1 строка в `FC_MATERIAL_PROPERTY_NAMES_KEYS["thermal"]` |
| 11 | `thermal[3]` EMISSIVITY | `fc_materials.py` | +1 строка там же |
| 12 | `plasticity[1]` TENSILE_STRAIN | `fc_materials.py` | +1 строка в `["plasticity"]` |
| 13 | `plasticity[6]` TENSILE_STRAIN_COMPR | `fc_materials.py` | +1 строка там же |
| 5 | Load `GravityMassForce` (6) | `fc_conditions.py` | +1 строка в `FC_LOADS_TYPES_KEYS` |
| 6 | Load `FaceSloshingBC` (45) | `fc_conditions.py` | +1 строка там же |
| 6 | Load `SegmentSloshingBC` (46) | `fc_conditions.py` | +1 строка там же |
| 7 | Load `PointDeadForce` (47) | `fc_conditions.py` | +1 строка там же |
| 7 | Load `PointTrackingForce` (48) | `fc_conditions.py` | +1 строка там же |
| 7 | Load `PointHydrodynamicForce` (49) | `fc_conditions.py` | +1 строка там же |
| 8 | Coupling `CONSTRAINT_EQUATION` (6) | `fc_constraint.py` | +1 строка в `FC_COUPLING_TYPES_KEYS` |
| 9 | Contact method `pure_lagrangian` | `fc_constraint.py` | +1 строка в `FC_CONTACT_METHODS` |
| 9 | Contact method `aug_lagrangian` | `fc_constraint.py` | +1 строка там же |
| 19 | Header `FCTYPE: 8` | `__init__.py` | +1 строка в default `types` |

**Итого**: ~14 однострочных правок. Тесты не должны сломаться (добавление новых ключей обратно совместимо). Обратные словари (`*_CODES`) генерируются автоматически через comprehension.

### Категория B: Добавление опциональных полей в существующие классы

Паттерн: добавить атрибут с дефолтом, прочитать из `src_data.get(...)` в `decode()`, записать в `encode()` если не None/пусто. Каждая правка — ~5–10 строк в одном файле.

| # | Что | Файл | Правка |
|---|-----|------|--------|
| 15 | Block `orientation_id` | `fc_blocks.py` | +атрибут `orientation_id: int = 0`, +get в decode, +set в encode. ~8 строк |
| 16 | Load `step`, `case` | `fc_conditions.py` | +2 Optional атрибута, +get/set. ~12 строк |
| 17 | Restraint `case` | `fc_conditions.py` | +1 Optional атрибут, +get/set. ~6 строк |
| 18 | InitialSet `name` | `fc_conditions.py` | +1 атрибут `name: str = ""`, +get/set. ~6 строк |

**Итого**: ~4 правки, ~32 строки. Полностью обратно совместимо — поля опциональные.

**Примечание по `compress()`**: Если `Load` получит `step`/`case`, а `Block` — `orientation_id`, нужно проверить, требуется ли их обработка в `FCModel.compress()`. Для `step`/`case` — нет (это индексы шагов, не ссылки на сущности). Для `orientation_id` — да, если `orientations` станут переиндексируемыми; но при pass-through подходе — нет.

### Категория C: Pass-through для новых top-level секций

Паттерн: хранить как `List[Dict[str, Any]]`, читать в `decode()`, писать в `encode()`. Не создавать отдельных классов — данные проходят без интерпретации.

| # | Что | Файл | Правка |
|---|-----|------|--------|
| 1 | `orientations` | `__init__.py` | +атрибут `orientations: List[Dict[str, Any]] = []`, +decode/encode. ~8 строк |
| 2 | `imported_sections` | `__init__.py` | +атрибут `imported_sections: List[Dict[str, Any]] = []`, +decode/encode. ~8 строк |

**Итого**: ~16 строк. Также нужно добавить поля в `FCSrcModel`.

### Категория D: Расширение Literal-типа и двух словарей для групп материалов

Паттерн: добавить строку в `FCMaterialPropertiesTypeLiteral`, пустые записи в `FC_MATERIAL_PROPERTY_NAMES_KEYS` и `FC_MATERIAL_PROPERTY_TYPES_KEYS`. Decode уже итерирует по ключам этих словарей — новые группы подхватятся автоматически.

| # | Что | Файл | Правка |
|---|-----|------|--------|
| 3 | `kinematic_hardening` | `fc_materials.py` | +1 строка в Literal, +пустой dict в NAMES, +пустой dict в TYPES. ~3 строки |
| 4 | `hsdf` | `fc_materials.py` | +1 строка в Literal, +пустой dict в NAMES, +пустой dict в TYPES. ~3 строки |

**Итого**: ~6 строк. С пустыми словарями группы будут корректно decode/encode — свойства пройдут как числовые коды вместо строковых имён, что допустимо для roundtrip.

**Важно**: `FCSrcMaterial` (TypedDict) тоже нужно расширить двумя опциональными полями (`kinematic_hardening`, `hsdf`). +2 строки.

### Категория E: Не требует правок / низкий приоритет

| # | Что | Почему |
|---|-----|--------|
| 14 | `DPC_N` → `DPC_B` | Требует уточнения у разработчика. Переименование — 1 строка, но ломает обратную совместимость для пользователей, использующих строку `"DPC_N"` |
| 20 | FCSettings TypedDict | Settings хранятся как `Dict[str, Any]` и проходят as-is. TypedDict — только для подсказок IDE, не влияет на roundtrip |

### Сводка по трудоёмкости

| Категория | Правок | Строк кода | Файлы | Риск регрессии |
|-----------|--------|------------|-------|----------------|
| A: Строки в словарях | ~14 | ~14 | `fc_materials.py`, `fc_conditions.py`, `fc_constraint.py`, `__init__.py` | Минимальный |
| B: Опциональные поля | ~4 | ~32 | `fc_blocks.py`, `fc_conditions.py` | Минимальный |
| C: Pass-through секции | ~2 | ~16 | `__init__.py` | Минимальный |
| D: Группы материалов | ~2 | ~8 | `fc_materials.py` | Минимальный |
| **Итого** | **~22** | **~70** | **5 файлов** | **Минимальный** |

Все правки обратно совместимы, не ломают существующие тесты и не требуют изменения логики `compress()` (при pass-through подходе для `orientations`/`imported_sections`).
