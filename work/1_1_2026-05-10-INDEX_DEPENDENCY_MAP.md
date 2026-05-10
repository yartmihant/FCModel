# Карта индексных пространств и зависимостей FCModel

## Индексные пространства (ID-коллекции)

В модели `FCModel` существуют следующие самостоятельные индексные пространства:

| # | Пространство         | Хранение в FCModel                          | Тип ключа | Описание                                    |
|---|----------------------|----------------------------------------------|-----------|---------------------------------------------|
| 1 | **Node ID**          | `mesh.nodes_ids` (NDArray[int32])            | int       | Глобальные ID узлов сетки                   |
| 2 | **Element ID**       | `mesh.elements[type][elem_id]` (Dict)        | int       | Глобальные ID конечных элементов            |
| 3 | **Block ID**         | `blocks` (Dict[int, FCBlock])                | int       | ID блоков (группы элементов)                |
| 4 | **Material ID**      | `materials` (Dict[int, FCMaterial])           | int       | ID материалов                               |
| 5 | **PropertyTable ID** | `property_tables` (Dict[int, FCPropertyTable])| int      | ID таблиц свойств элементов                 |
| 6 | **CoordSystem ID**   | `coordinate_systems` (Dict[int, FCCoordSys]) | int       | ID систем координат                         |
| 7 | **Load ID**          | `loads` (List[FCLoad]), поле `.id`            | int       | ID нагрузок                                 |
| 8 | **Restraint ID**     | `restraints` (List[FCRestraint]), поле `.id`  | int       | ID закреплений                              |
| 9 | **InitialSet ID**    | `initial_sets` (List[FCInitialSet]), поле `.id`| int      | ID начальных условий                        |
|10 | **Constraint ID**    | `contact/coupling/periodic_constraints`, `.id`| int      | ID контактных/связных/периодич. ограничений |
|11 | **Receiver ID**      | `receivers` (List[FCReceiver]), поле `.id`    | int       | ID приёмников (receivers)                   |
|12 | **NodeSet ID**       | `nodesets` (Dict[int, FCSet])                | int       | ID наборов узлов                            |
|13 | **SideSet ID**       | `sidesets` (Dict[int, FCSet])                | int       | ID наборов граней                           |

---

## Граф зависимостей (что ссылается на что)

```
Node ID ◄──────────── Element.nodes[]          (каждый элемент хранит список node IDs)
Node ID ◄──────────── Load.apply               (FCValue: массив node IDs — или формула "all")
Node ID ◄──────────── Restraint.apply           (FCValue: массив node IDs — или формула)
Node ID ◄──────────── InitialSet.apply          (FCValue: массив node IDs — или формула)
Node ID ◄──────────── Constraint.master/slave   (FCValue: массив node IDs)
Node ID ◄──────────── Receiver.apply            (FCValue: массив node IDs)
Node ID ◄──────────── NodeSet.apply             (FCValue: массив node IDs)
Node ID ◄──────────── FCData.table[j].value     (при dependency_type = TABULAR_NODE_ID (11))

Element ID ◄────────── SideSet.apply            (FCValue: массив пар [elem_id, face_index, ...])
Element ID ◄────────── FCData.table[j].value    (при dependency_type = TABULAR_ELEMENT_ID (10))

Block ID ◄──────────── Element.block            (каждый элемент ссылается на свой блок)

Material ID ◄───────── Block.material_id        (основной материал блока)
Material ID ◄───────── Block.material.ids[]     (дополнительные материалы для мультишагов)

PropertyTable ID ◄──── Block.property_id        (таблица свойств элементов блока)

CoordSystem ID ◄────── Block.cs_id              (СК блока)
CoordSystem ID ◄────── Load.cs_id               (СК нагрузки)
CoordSystem ID ◄────── Restraint.cs_id           (СК закрепления)
CoordSystem ID ◄────── InitialSet.cs_id          (СК начальных условий)
```

---

## Детальное описание зависимостей

### 1. Node ID → кто ссылается

| Сущность-источник          | Поле                         | Описание                                                                 |
|---------------------------|------------------------------|--------------------------------------------------------------------------|
| `FCElement`               | `nodes: List[int]`           | Список ID узлов, образующих элемент                                      |
| `FCLoad`                  | `apply: FCValue`             | Массив int32 — ID узлов, к которым приложена нагрузка (или формула "all")|
| `FCRestraint`             | `apply: FCValue`             | Массив int32 — ID узлов с закреплением (или формула)                     |
| `FCInitialSet`            | `apply: FCValue`             | Массив int32 — ID узлов начальных условий (или формула)                  |
| `FCConstraint`            | `master: FCValue`            | Массив int32 — ID узлов мастер-поверхности                               |
| `FCConstraint`            | `slave: FCValue`             | Массив int32 — ID узлов слейв-поверхности                                |
| `FCReceiver`              | `apply: FCValue`             | Массив int32 — ID узлов приёмника                                        |
| `FCSet` (nodeset)         | `apply: FCValue`             | Массив int32 — ID узлов в наборе                                         |
| `FCData` (в материалах)   | `table[j].value` при `TABULAR_NODE_ID` | Массив float64 с ID узлов в табличной зависимости              |

### 2. Element ID → кто ссылается

| Сущность-источник          | Поле                         | Описание                                                                 |
|---------------------------|------------------------------|--------------------------------------------------------------------------|
| `FCSet` (sideset)         | `apply: FCValue`             | Массив int32 — пары [elem_id, face_idx, ...] для сторон элементов        |
| `FCData` (в материалах)   | `table[j].value` при `TABULAR_ELEMENT_ID` | Массив float64 с ID элементов в табличной зависимости        |
| `FCElement`               | `parent_id: int`             | Ссылка на родительский элемент (0 если нет)                              |

### 3. Block ID → кто ссылается

| Сущность-источник | Поле              | Описание                               |
|-------------------|--------------------|----------------------------------------|
| `FCElement`       | `block: int`       | Каждый элемент принадлежит блоку       |

### 4. Material ID → кто ссылается

| Сущность-источник | Поле              | Описание                                              |
|-------------------|--------------------|-------------------------------------------------------|
| `FCBlock`         | `material_id: int` | Основной материал блока                               |
| `FCBlock`         | `material['ids']`  | Список доп. материалов для мультишагового расчёта     |

### 5. PropertyTable ID → кто ссылается

| Сущность-источник | Поле              | Описание                               |
|-------------------|--------------------|----------------------------------------|
| `FCBlock`         | `property_id: int` | Таблица свойств, привязанная к блоку   |

### 6. CoordinateSystem ID → кто ссылается

| Сущность-источник | Поле         | Описание                                |
|-------------------|--------------|-----------------------------------------|
| `FCBlock`         | `cs_id: int` | Система координат блока                 |
| `FCLoad`          | `cs_id: int` | Система координат нагрузки              |
| `FCRestraint`     | `cs_id: int` | Система координат закрепления           |
| `FCInitialSet`    | `cs_id: int` | Система координат начальных условий     |

### 7–9. Load / Restraint / InitialSet ID

Собственные ID (`load.id`, `restraint.id`, `initial_set.id`) — автономные, не имеют входящих ссылок из других сущностей.

### 10. Constraint ID

Собственный ID (`constraint.id`) — автономный, не имеет входящих ссылок.

### 11. Receiver ID

Собственный ID (`receiver.id`) — автономный, не имеет входящих ссылок.

### 12–13. NodeSet / SideSet ID

Собственные ID — автономные, не имеют входящих ссылок.

---

## Порядок переиндексации для `compress()`

Рекомендуемый порядок (от «листовых» к «корневым» по графу зависимостей):

1. **Coordinate Systems** — переиндексировать `coordinate_systems`, обновить `cs_id` в `Block`, `Load`, `Restraint`, `InitialSet`.
2. **Materials** — переиндексировать `materials`, обновить `material_id` и `material.ids[]` в `Block`.
3. **Property Tables** — переиндексировать `property_tables`, обновить `property_id` в `Block`.
4. **Blocks** — переиндексировать `blocks`, обновить `element.block` в `mesh`.
5. **Nodes** — переиндексировать `mesh.nodes_ids`, обновить `element.nodes[]`, а также `apply` в `Load`, `Restraint`, `InitialSet`, `Constraint.master/slave`, `Receiver`, `NodeSet` и `TABULAR_NODE_ID` в `FCData`.
6. **Elements** — переиндексировать `mesh.elements`, обновить `element.parent_id`, `SideSet.apply`, `TABULAR_ELEMENT_ID` в `FCData`.
7. **Loads** — переиндексировать `.id` (автономный).
8. **Restraints** — переиндексировать `.id` (автономный).
9. **Initial Sets** — переиндексировать `.id` (автономный).
10. **Constraints** — переиндексировать `.id` (автономный).
11. **Receivers** — переиндексировать `.id` (автономный).
12. **NodeSets** — переиндексировать ключи в dict (автономный).
13. **SideSets** — переиндексировать ключи в dict (автономный).

---

## Примечания

- `FCValue` может содержать формулу (строка `"all"`) вместо массива ID — в этом случае переиндексация не нужна.
- `SideSet.apply` содержит reshape-ированный массив пар `[elem_id, face_index]` — переиндексировать нужно только `elem_id` (чётные позиции при flat-виде или столбец 0 при 2D reshape).
- `FCData.table[j].value` при `TABULAR_NODE_ID` / `TABULAR_ELEMENT_ID` содержит float64-массив ID — необходим каст к int для lookup и обратно к float64.
- `Block.material` (мультишаг): поле `material['ids']` — список material IDs, `material['steps']` — соответствующие шаги (steps не перeиндексируются).
- `Element.parent_id = 0` означает отсутствие родителя — не переиндексируется.
