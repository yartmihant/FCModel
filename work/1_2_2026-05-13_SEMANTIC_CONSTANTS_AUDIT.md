# Аудит семантики магических констант — fc_model

**Дата:** 2026-05-13  
**Версия проекта:** 1.2.1

---

## 1. Общий принцип

Внутри объектной модели (FCModel) числовые коды из формата .fc должны быть разрешены в человекочитаемые строки. JSON-формат использует `int`-коды для компактности, но API библиотеки должен предоставлять пользователю строковые имена. Обратное преобразование (строка → код) происходит только при `encode()`.

---

## 2. Текущее состояние по классам

### ✅ Уже используют строки (эталон)

| Класс | Поле | Маппинг | Пример |
|-------|------|---------|--------|
| `FCLoad` | `type: str` | `FC_LOADS_TYPES_KEYS[code]` при decode, `FC_LOADS_TYPES_CODES[name]` при encode | `"FaceDeadStress"` |
| `FCRestraint` | `flags: List[str]` | `FC_RESTRAINT_FLAGS_KEYS[code]` при decode, `FC_RESTRAINT_FLAGS_CODES[name]` при encode | `["Displacement", "Displacement", ...]` |
| `FCInitialSet` | `type: str` | `FC_INITIAL_SET_TYPES_KEYS[code]` при decode, `FC_INITIAL_SET_TYPES_CODES[name]` при encode | `"Temperature"` |
| `FCCoordinateSystem` | `type: str` | Строки в JSON (`"cartesian"`, `"cylindrical"`, `"spherical"`) — маппинг не нужен | `"cylindrical"` |
| `FCElement` | — | `FC_ELEMENT_TYPES_KEYID` / `FC_ELEMENT_TYPES_KEYNAME` — используются строковые имена | `"HEX8"` |
| `FCDependencyColumn` | `type: str` | `FC_DEPENDENCY_TYPES_KEYS[code]` при decode | `"TABULAR_TIME"` |
| `FCMaterialProperty` | `type`, `name` | Маппятся через `FC_MATERIAL_PROPERTY_TYPES_KEYS` / `FC_MATERIAL_PROPERTY_NAMES_KEYS` с fallback на raw-код | `"HOOK"`, `"YOUNG_MODULE"` |

### ❌ Хранят сырые числовые коды

| Класс | Поле | Тип | Доступный маппинг | Проблема |
|-------|------|-----|-------------------|----------|
| **FCReceiver** | `type` | `int` | `FC_RECEIVER_TYPES_KEYS` | decode хранит raw int из JSON; encode пишет raw int. Пользователь видит `0` вместо `"DISPLACEMENT"` |
| **FCPropertyTable** | `type` | `int` | `FC_PROPERTY_TABLE_TYPES_KEYS` | decode хранит raw int из JSON; encode пишет raw int. Пользователь видит `0` вместо `"SHELL"` |
| **FCConstraint** (coupling) | `type` | `Union[int, str]` | `FC_COUPLING_TYPES_KEYS` | decode для coupling_constraints хранит raw int (0-6). Пользователь видит `0` вместо `"ELASTICITY"` |
| **FCConstraint** (periodic) | `type` | `Union[int, str]` | `FC_PERIODIC_TYPES_KEYS` | decode для periodic_constraints хранит raw int (0-5). Пользователь видит `0` вместо `"ALL"` |
| **FCData** | `type` | `Union[int, str]` | `FC_DEPENDENCY_TYPES_KEYS` | Простые зависимости хранят raw int: `0` (CONSTANT), `6` (FORMULA). Таблицы — sentinel `-1`. Magic numbers `0`, `6`, `-1` разбросаны по коду |

### ⚠️ Частично проблемные

| Класс | Поле | Замечание |
|-------|------|-----------|
| **FCConstraint** (contact) | `type` | Строка из JSON (`"general"`, `"tied"`, …) — OK |
| **FCPropertyTable** | `properties.section_type` | Внутри generic-словаря `properties` для BEAM — raw int (0-12). Маппинг: `FC_BEAM_SECTION_TYPES_KEYS`. Но это внутри opaque dict, а не поле класса |

---

## 3. Подробный план исправлений

### 3.1. FCReceiver — `type: int` → `type: str`

**Текущее:**
```python
class FCReceiver:
    type: int  # raw code
    def decode(cls, src_data):
        ...type_val=src_data['type']...  # raw int
    def encode(self):
        ...  "type": self.type  # raw int
```

**Предлагаемое:**
- `type` хранит строку: `FC_RECEIVER_TYPES_KEYS.get(code, str(code))`
- encode: `FC_RECEIVER_TYPES_CODES[self.type]`
- Аннотация: `type: str`
- Конструктор принимает `type_val: str = "DISPLACEMENT"`

**Сложность:** Низкая (~10 LOC)

[Одобряю]

---

### 3.2. FCPropertyTable — `type: int` → `type: str`

**Текущее:**
```python
class FCPropertyTable:
    type: int  # raw code
```

**Предлагаемое:**
- `type` хранит строку: `FC_PROPERTY_TABLE_TYPES_KEYS.get(code, str(code))`
- encode: `FC_PROPERTY_TABLE_TYPES_CODES[self.type]`
- Аннотация: `type: str`
- Конструктор принимает `type_val: str = "SHELL"`

**Сложность:** Низкая (~10 LOC)

[Одобряю]

---

### 3.3. FCConstraint — `type: Union[int, str]` → `type: str`

**Проблема:** `FCConstraint` — generic-класс для трёх семейств (contact, coupling, periodic). У каждого своя таблица кодов. Сам класс не знает, к какому семейству принадлежит.

**Варианты:**

**(A) Маппинг в `FCModel.decode()`** — после `FCConstraint.decode()` пост-обработка:
```python
for cc in fc_model.coupling_constraints:
    cc.type = FC_COUPLING_TYPES_KEYS.get(cc.type, str(cc.type))
for pc in fc_model.periodic_constraints:
    pc.type = FC_PERIODIC_TYPES_KEYS.get(pc.type, str(pc.type))
```
Аналогично в `FCModel.encode()` — обратное преобразование.

**(B) Параметр `kind` в decode/encode:**
```python
@classmethod
def decode(cls, src_data, kind: str = "contact"):
    ...
```

**(C) Подклассы:** `FCCouplingConstraint`, `FCPeriodicConstraint`, `FCContactConstraint`.

[Одобряю вариант B. Так же: там FCConstraint.type: Union[int, str]. В спецификации прямо написано: periodic_constraints."type": "<int>" но contact_constraints."type": "<str>". Однако это неудачный дизайн; пусть у нас будет FCConstraint.type: str, который будет декодироваться (или нет) в зависимости от kind]

**Рекомендация:** Вариант **(A)** — минимальные изменения, не ломает API.  
**Сложность:** Низкая (~15 LOC)

---

### 3.4. FCData — `type: Union[int, str]` → `type: str`

**Текущее:** magic numbers `0` (CONSTANT), `6` (FORMULA), `-1` (TABLE sentinel).

**Предлагаемое:**
- `type` хранит строку: `"CONSTANT"`, `"FORMULA"`, `"TABLE"` (вместо `-1`)
- Обновить `FCData.constant()` → `self.type = "CONSTANT"`
- Обновить `FCData.formula()` → `self.type = "FORMULA"`
- `decode()` для таблиц: `self.type = "TABLE"` (вместо `-1`)
- `decode()` для простых: `FC_DEPENDENCY_TYPES_KEYS.get(code, str(code))`
- `encode()`: обратный маппинг через `FC_DEPENDENCY_TYPES_CODES` + особый случай `"TABLE"` → список
- `__repr__()`: обновить условия (заменить `== -1`, `== 6`, `== 0` на строковые сравнения)

**Затронутые места:**
- `FCData.decode()`, `FCData.encode()`, `FCData.constant()`, `FCData.formula()`
- `FCData.__repr__()`, `FCData.remap_column()`
- Тесты: `test_data.py`, `test_value.py`, `test_model.py`

**Сложность:** Средняя (~30 LOC, изменения в нескольких файлах)

[Одобряю]


---

## 4. Отсутствующие коды

### 4.1. Коды, присутствующие в спецификации, но отсутствующие в маппингах библиотеки

| Маппинг | Код | Имя | Замечание |
|---------|-----|-----|-----------|
| `FC_DEPENDENCY_TYPES_KEYS` | `9` | — | **Код 9 пропущен** (между 8=TABULAR_STRAIN и 10=TABULAR_ELEMENT_ID). В спецификации тоже нет кода 9 — это не пропуск, а зарезервированный код |
| `FC_RESTRAINT_FLAGS_KEYS` | `8` | — | Код 8 пропущен (между 7=TemperatureGradient и 9=Acceleration). В спецификации тоже нет — зарезервирован |
| `FC_RESTRAINT_FLAGS_KEYS` | `11` | — | Код 11 пропущен (между 10=PorePressure и 12=DirectionDisplacement). В спецификации тоже нет |

Все пропуски в нумерации соответствуют спецификации — **недостающих кодов не обнаружено**.

### 4.2. Коды, присутствующие в библиотеке, но отсутствующие в спецификации

| Маппинг | Код | Имя | Замечание |
|---------|-----|-----|-----------|
| `FC_RESTRAINT_FLAGS_KEYS` | `16` | `Fluence` | Расширение библиотеки (задокументировано в LLM-контексте) |
| `FC_ELEMENT_TYPES` | — | `BAR2`, `BAR3`, `CABLE2`, `CABLE3` | Расширения библиотеки |

Эти расширения допустимы и задокументированы.

### 4.3. Пустые маппинги

| Группа | Маппинг `_NAMES_KEYS` | Маппинг `_TYPES_KEYS` | Статус |
|--------|----------------------|----------------------|--------|
| `swelling` | `{}` | `{}` | Пустой — ожидает реализации |
| `kinematic_hardening` | `{}` | `{}` | Пустой — ожидает реализации |
| `hsdf` | `{}` | `{}` | Пустой — ожидает реализации |

Данные группы были добавлены в текущей сессии как pass-through. Коды свойств и типов из спецификации для них не описаны — требуется уточнение у разработчика формата.

---

## 5. Прочие семантические замечания

### 5.1. `FCPropertyTable.properties["section_type"]` (BEAM)

Внутри opaque-словаря `properties` для BEAM section_type хранится как raw int. Маппинг `FC_BEAM_SECTION_TYPES_KEYS` существует, но не применяется автоматически. Для полной семантизации нужен специальный хук в decode/encode для BEAM-таблиц. Это выходит за рамки текущего аудита — помечаю как **future work**.

### 5.2. settings

`settings` — pass-through `Dict[str, Any]`. Строковые значения (`"static"`, `"dynamic"`, `"eigenfrequencies"`, `"buckling"`, `"spectrum"`, `"harmonic"`, `"effectiveprops"`) не кодируются числами. Семантизация не требуется.

---

## 6. Приоритеты реализации

| Приоритет | Класс | Сложность | Влияние на пользователя |
|-----------|-------|-----------|------------------------|
| **1** | FCReceiver | Низкая | Высокое — `type` используется постоянно |
| **2** | FCPropertyTable | Низкая | Высокое — `type` используется при создании таблиц |
| **3** | FCConstraint (coupling/periodic) | Низкая | Среднее — `type` важен для coupling |
| **4** | FCData | Средняя | Среднее — внутренний API, но magic numbers `-1`/`0`/`6` неудобны |

---

## 7. Резюме

- **4 класса** хранят сырые числовые коды вместо строк
- **Отсутствующих кодов** относительно спецификации не обнаружено
- **3 группы** материалов (`swelling`, `kinematic_hardening`, `hsdf`) имеют пустые маппинги — требуют данных от разработчика
- Рекомендуемый порядок: FCReceiver → FCPropertyTable → FCConstraint → FCData
