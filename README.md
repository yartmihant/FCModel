# FCModel

Строго типизированная объектная модель для формата Fidesys Case (.fc)

FCModel — это библиотека для чтения/создания/записи файлов формата Fidesys Case (`.fc`). Она отражает структуру формата в виде Python‑классов, обеспечивает кодирование/декодирование бинарных полей (Base64) и помогает программно собирать и анализировать модели.

## Обзор 

FCModel предназначена для автоматизации работы с моделями конечных элементов в формате Fidesys Case. Библиотека позволяет:
* Загружать существующие модели из файлов .fc
* Программно создавать новые модели
* Модифицировать параметры материалов, нагрузок, закреплений
* Сохранять изменения в новый файл формата .fc

Поддерживаемые версии Python: ≥ 3.8

## Преимущества

FCModel предоставляет значительные преимущества по сравнению с прямым редактированием файлов формата [[Формат_Fidesys_Case|Fidesys Case]]:

* **Строгая типизация**: Все сущности модели имеют четко определенные типы данных.
* **Автоматическое кодирование бинарных данных**: Библиотека автоматически обрабатывает Base64-кодирование массивов координат, сеток и других бинарных полей.
* **Объектная модель** Вместо работы с вложенными JSON-структурами предоставляется удобная объектная модель с понятными методами и свойствами.
* **Валидация данных** Автоматическая проверка корректности данных при загрузке и сохранении файлов.
* **Безопасность операций**: Типизированные операции предотвращают случайное повреждение структуры файла.

## Установка

```bash
pip install fc_model
```

Либо скачать этот репозиторий и установить из исходников:
```bash
python3 -m pip install -e .
```

## Быстрый старт

```python
from fc_model import FCModel

# Загрузка модели из файла
m = FCModel("path/to/model.fc")

# ... чтение/изменение данных модели ...

# Сохранение в файл
m.save("path/to/output.fc")
```

Если путь не передан в конструктор, создаётся пустая модель с инициализированными коллекциями.

## Основные классы

- FCModel: корневой класс модели. Поля соответствуют разделам спецификации: `header`, `coordinate_systems`, `mesh`, `blocks`, `materials`, `property_tables`, `loads`, `restraints`, `initial_sets`, `sets`, `contact_constraints`, `coupling_constraints`, `periodic_constraints`, `receivers`, `settings`.
- FCMesh, FCElement: сетка (узлы/элементы) и элемент. Mesh кодирует/декодирует массивы `nids`, `nodes`, `elemids`, `elem_types`, `elem_blocks`, `elem_orders`, `elem_parent_ids`, `elems`.
- FCBlock: блок элементов (связь элементов с материалами и свойствами). Поддерживает опциональные поля `steps` и `material` (многошаговая привязка материалов).
- FCCoordinateSystem: система координат (id, type, name, origin, dir1, dir2) с Base64‑кодированием векторов.
- FCMaterial, FCMaterialProperty: материал и его свойства, сгруппированные по разделам (elasticity/common/thermal/...). Поддерживаются константы/табличные зависимости/формулы.
- FCPropertyTable: таблица свойств (SHELL/BEAM/LUMPMASS/SPRING);
- FCLoad, FCRestraint, FCInitialSet: нагрузки, закрепления, начальные условия. Поддерживают массивы назначения `apply_to` (в т.ч. строку "all"), зависимости компонент и шаги.
- FCSet: узловые/граневые наборы (`nodesets`, `sidesets`).
- FCConstraint: контактные/связывающие/периодические ограничения (структуры переносятся как есть, с дополнительными свойствами).
- FCReceiver: набор приёмников результатов.
- FCValue, FCData, FCDependencyColumn: служебные классы для представления значений (массив/формула) и табличных зависимостей (тип + столбцы аргументов).

## Константы и таблицы кодов

В модуле реэкспортированы основные карты из доменных модулей, чтобы их можно было импортировать напрямую:

- Материалы (`from fc_model import ...`):
  - `FC_MATERIAL_PROPERTY_NAMES_KEYS`, `FC_MATERIAL_PROPERTY_NAMES_CODES`
  - `FC_MATERIAL_PROPERTY_TYPES_KEYS`, `FC_MATERIAL_PROPERTY_TYPES_CODES`

- Нагрузки/ГУ/НУ:
  - `FC_LOADS_TYPES_KEYS`, `FC_LOADS_TYPES_CODES`
  - `FC_RESTRAINT_FLAGS_KEYS`, `FC_RESTRAINT_FLAGS_CODES`
  - `FC_INITIAL_SET_TYPES_KEYS`, `FC_INITIAL_SET_TYPES_CODES`

- Сетка:
  - `FC_ELEMENT_TYPES_KEYID`, `FC_ELEMENT_TYPES_KEYNAME`

- Зависимости (`FCData`):
  - `FC_DEPENDENCY_TYPES_KEYS`, `FC_DEPENDENCY_TYPES_CODES`

Пример использования констант:
```python
from fc_model import FC_MATERIAL_PROPERTY_NAMES_KEYS
names = FC_MATERIAL_PROPERTY_NAMES_KEYS["elasticity"]
print(names[0])  # YOUNG_MODULE
```

## Пример: модификация материала
```python
from fc_model import FCModel, FCMaterial, FCMaterialProperty, FCData

m = FCModel("case.fc")
mat_id = next(iter(m.materials))
mat = m.materials[mat_id]

# Добавим свойство плотности (common.USUAL -> DENSITY) как константу
prop = FCMaterialProperty(
    type="USUAL",
    name="DENSITY",
    data=FCData(data="", dep_type=0, dep_data="")
)
mat.properties.setdefault("common", [[]])[0].append(prop)

m.save("case_updated.fc")
```

## Соответствие спецификации

Библиотека полностью соответствует спецификации формата Fidesys Case `docs/FidesysCase.md`.:
* Структура файла: JSON с бинарными вставками в Base64
* Кодировка: UTF-8
* Версия формата: 3
* Автоматическое кодирование/декодирование бинарных полей
* Поддержка всех разделов спецификации

## Обратная связь

Если вы нашли ошибку или у вас есть предложение по улучшению — напишите на antonov@cae-fidesys.com.


## Смотрите так же

* [https://pypi.org/project/fc-model/ FCModel на PyPI]
* [https://github.com/artmihant/fcmodel FCModel на github]
