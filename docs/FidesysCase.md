# Формат Fidesys Case
 
Источник: страница Fidesys Wiki.
https://clare.office.saldlab.com/wiki/%D0%A4%D0%BE%D1%80%D0%BC%D0%B0%D1%82_Fidesys_Case

## Формат входного файла Fidesys

**Расширение**

```
.fc
```

**Формат:** JSON с бинарными вставками в Base64. Кодировка файла — UTF-8.


### Общая структура

```
{
   "header": {...},               // Заголовок файла
   "blocks": [...],               // Список данных о блоках
   "coordinate_systems": [...],   // Список данных о системах координат
   "mesh": {...},                 // Данные о сетке
   "materials": [...],            // Список данных о материалах
   "property_tables": [...],      // Список таблиц свойств (аналог Real Constants в Ansys)
   "loads":[...],                 // Список нагрузок
   "restraints":[...],            // Список закреплений
   "contact_constraints": [...],  // Список контактов
   "coupling_constraints": [...], // Список связей
   "periodic_constraints": [...], // Список периодических ГУ
   "receivers": [...],            // Список приёмников
   "initial_sets": [...],         // Список начальных условий
   "sets": {...},                 // Наборы узлов и сторон
   "settings": {...},             // Общие настройки
}
```

### header

```
{
   "description": <String>,          // Описание файла
   "version": <unsigned short int>,  // Версия формата
   "types": {...},                   // Настройки типов
   "binary": <bool>                  // Бинарный или текстовый формат
}
```

### types

Информация о размерах типов данных, используемых в бинарных частях.

```
{
   "char": <int>,                // sizeof(char)
   "short_int": <int>,           // sizeof(short int)
   "int": <int>,                 // sizeof(int)
   "double": <int>,              // sizeof(double)
}
```

### blocks

```
[
   {
      "id": <int>,             // Id блока
      "cs_id": <int>,          // Id системы координат блока
      "material":              // Материалы блока по шагам (необязательный параметр, если id материала не меняется во время расчета)
      {
         "ids": [int],         // Список id материалов
         "steps": [int]        // Номера шагов
      },
      "material_id": <int>,    // Id материала блока
      "property_id": <int>,    // Id свойств блока
      "steps": [int]           // Шаги для расчёта. Необязательный параметр
   },
   {...}                       // Следующий элемент с описанной выше структурой.
]
```

### coordinate_system

```
[
   {
      "id": <unsigned short int>,   // Id системы координат. Больше нуля. Под id = 1 должна быть глобальная декартова СК.
      "type": <string>,             // Тип СК. Варианты: "cartesian", "cylindrical", "spherical".
      "name": <string>,             // Название СК
      "origin": [double]            // Координаты начала СК. В Base64 кодируется весь массив как строка
      "dir1": [double]              // Координаты конца направляющего вектора вдоль направления 1. В Base64 кодируется весь массив как строка
      "dir2": [double]              // Координаты конца направляющего вектора вдоль направления 2. В Base64 кодируется весь массив как строка
   },
   {...}                           // Следующий элемент с описанной выше структурой.
]
```

### mesh

```
{
   "nodes_count": <unsigned int>,   // количество узлов. Должно совпадать с длиной массива nids.
   "nids": [int],                   // массив id узлов. В Base64 кодируется весь массив как одна строка.
   "nodes": [double],               // массив координат узлов в виде [x1 y1 z1 x2 y2 z2 и т.д.]. В Base64 кодируется весь массив как одна строка.
   "elems_count": <unsigned int>,   // количество элементов. Должно совпадать с длиной массива elemids.
   "elemids": [int],                // массив id элементов. В Base64 кодируется весь массив как одна строка.
   "elem_types": [unsigned char],   // массив типов элементов. В Base64 кодируется весь массив как одна строка.
   "elem_blocks": [int],            // массив id блока, которому принадлежит элемент. В Base64 кодируется весь массив как одна строка.
   "elem_orders": [int],            // массив порядков SEM элементов (игнорируется для FEM), от 3 до 9. В Base64 кодируется весь массив как одна строка.
   "elem_parent_ids": [int],        // массив id геометрии, которой принадлежит элемент. В Base64 кодируется весь массив как одна строка.
   "elems": [ [unsigned int] ],     // массив массивов id узлов, из которых состоит элемент. Разное для каждого элемента. В Base64 массив массивов кодируется как одна строка.
}
```

#### elem_types

```
Солидные FEM элементы (3D и 2D)
  0 = NONE,
  1 = TETRA4,
  2 = TETRA10,
  3 = HEX8,
  4 = HEX20,
  6 = WEDGE6,
  7 = WEDGE15,
  8 = PYR5,
  9 = PYR13,
  10 = TRI3,
  11 = TRI6,
  12 = QUAD4,
  13 = QUAD8,
```

```
Солидные SEM элементы (3D и 2D)
  15 = TETRA4S,
  16 = TETRA10S,
  17 = HEX8S,
  18 = HEX20S,
  20 = WEDGE6S,
  21 = WEDGE15S,
  22 = PYR5S,
  23 = PYR13S,
  24 = TRI3S,
  25 = TRI6S,
  26 = QUAD4S,
  27 = QUAD8S,
```

```
Оболочечные FEM и SEM элементы
  29 = MITC3,
  30 = MITC6,
  31 = MITC4,
  32 = MITC8,
  84 = SHELL3S,
  85 = SHELL4S,
  86 = SHELL6S,
  87 = SHELL8S,
```

```
Балочные FEM и SEM элементы, пружины
  36 = BEAM26,
  37 = BEAM36,
  39 = SPRING3D,
  41 = SPRING6D,
  83 = SPRING2D,
  89 = BEAM27,
  90 = BEAM37,
  95 = BEAM26S,
  96 = BEAM36S,
  97 = BEAM27S,
  98 = BEAM37S,
```

```
Точечные массы и точки
  38 = LUMPMASS3D,
  40 = LUMPMASS6D,
  82 = LUMPMASS2D,
  99 = POINT3D,
  100 = POINT2D,
  101 = POINT6D,
  105 = LUMPMASS2DR
```

### materials

```
[
   // Структура материала
   {
      "id": <int>,             // Id материала
      "name": <string>,        // Название материала
      // Группы свойств. Не все группы могут быть заданы. Не все группы и свойства групп сочетаются между собой. См. интерфейс для определения сочетаемости.
      "elasticity": [...],     // Упругость и вязкоупругость
      "common": [...],         // Общие свойства
      "thermal": [...]         // Температурные свойства
      "geomechanic": [...],    // Геомеханика
      "plasticity": [...],     // Пластичность
      "hardening": [...],      // Упрочнение
      "creep": [...],          // Позучесть
      "preload": [...],        // Преднагружение
      "strength": [...],       // Прочность
   },
   {...}                        // Следующий материал в списке
]
```

### Структура группы свойств материала

Группа записывается как массив из одного элемента, содержащего данные о свойствах группы.

```
[
   {
      "constants": [double],                     // Массив массивов значений свойств группы.
                                                 // В Base64 кодируется каждый элемент (константа или массив) основного
                                                 // массива, формулы записываются строкой без кодирования.
      "const_types": [ [unsigned short int] ],   // Массив  массивов типов зависимостей каждого свойства группы.
                                                 // При многомерных табличных зависимостях у одного свойства может быть несколько TABULAR_* зависимостей.
      "const_dep": [double],                     // Массив массивов аргументов табличной зависимости. Пустая строка для константы и формулы.
                                                 // В Base64 каждый элемент основного массива кодируется отдельно.
      "const_dep_size": [int],                   // Массив размерностей табличной зависимости каждого свойства (количество строк таблицы).
                                                 // Равно 0 для константы и формулы
      "const_names": [int]                       // Имена констант свойства группы
      "type": <int>,                             // Тип свойства
   }
]
```

#### const_types

```
0 = CONSTANT,
1 = TABULAR_X,
2 = TABULAR_Y,
3 = TABULAR_Z,
4 = TABULAR_TIME,
5 = TABULAR_TEMPERATURE,
6 = FORMULA,
7 = TABULAR_FREQUENCY,
8 = TABULAR_STRAIN,
10 = TABULAR_ELEMENT_ID,
11 = TABULAR_NODE_ID,
12 = TABULAR_MODE_ID
```

#### type

```
elasticity:
  0 = HOOK,
  1 = HOOK_ORTHOTROPIC,
  2 = HOOK_TRANSVERSAL_ISOTROPIC,
  3 = BLATZ_KO,
  4 = MURNAGHAN,
  11 = COMPR_MOONEY,
  20 = NEO_HOOK,
  21 = ANISOTROPIC
common:
  0 = USUAL
thermal:
  0 = ISOTROPIC,
  1 = ORTHOTROPIC,
  2 = TRANSVERSAL_ISOTROPIC
geomechanic:
  0 = BIOT_ISOTROPIC,
  1 = BIOT_ORTHOTROPIC,
  2 = BIOT_TRANSVERSAL_ISOTROPIC
plasticity:
  0 = MISES,
  1 = DRUCKER_PRAGER,
  4 = DRUCKER_PRAGER_CREEP
  9 = MOHR_COULOMB
hardening:
  0 = LINEAR,
  1 = MULTILINEAR
creep:
  0 = NORTON
preload:
  0 = INITIAL
strength:
  0 = ISOTROPIC
```

#### const_names

```
elasticity
 // HOOK
   0 = YOUNG_MODULE,
   1 = POISSON_RATIO,
 // HOOK, MURNAGHAN
   2 = SHEAR_MODULUS,
   3 = BULK_MODULUS,
 // BLATZ_KO
   4 = MU,
   5 = ALPHA,
   6 = BETA,
 // MURNAGHAN
   7 = LAME_MODULE,
   8 = C3,
   9 = C4,
   10 = C5,
 // HOOK_TRANSVERSAL_ISOTROPIC
   16 = E_T,     17 = E_L,
   18 = PR_T,    19 = PR_TL,
   20 = G_TL,
 // HOOK_ORTHOTROPIC
   21 = G12,     22 = G23,     23 = G13,
   24 = PRXY,    25 = PRYZ,    26 = PRXZ,
 // COMPR_MOONEY
   27 = C1,
   28 = C2,
   29 = D,
 // ANISOTROPIC
   82 = C_1111,    83 = C_1112,    84 = C_1113,    85 = C_1122,    86 = C_1123,    87 = C_1133,
   88 = C_1212,    89 = C_1213,    90 = C_1222,    91 = C_1223,    92 = C_1233,
   93 = C_1313,    94 = C_1322,    95 = C_1323,    96 = C_1333,
   97 = C_2222,    98 = C_2223,    99 = C_2233,
   100 = C_2323,   101 = C_2333,
   102 = C_3333
```

```
common
 // USUAL
  0 = DENSITY,
  1 = STRUCTURAL_DAMPING_RATIO,
  2 = MASS_DAMPING_RATIO,
  3 = STIFFNESS_DAMPING_RATIO
```

```
thermal
 // ISOTROPIC
   0 = COEF_LIN_EXPANSION,
   1 = COEF_THERMAL_CONDUCTIVITY,
 // ORTHOTROPIC
   5 = COEF_THERMAL_CONDUCTIVITY_XX,    9 = COEF_THERMAL_CONDUCTIVITY_YY,    13 = COEF_THERMAL_CONDUCTIVITY_ZZ,
   14 = COEF_LIN_EXPANSION_X,           15 = COEF_LIN_EXPANSION_Y,           16 = COEF_LIN_EXPANSION_Z,
 // TRANSVERSAL_ISOTROPIC
   17 = COEF_THERMAL_CONDUCTIVITY_T,    18 = COEF_THERMAL_CONDUCTIVITY_L,
   19 = COEF_LIN_EXPANSION_T,           20 = COEF_LIN_EXPANSION_L
```

```
geomechanic
   1 = FLUID_VISCOSITY,
   2 = POROSITY,
   3 = FLUID_BULK_MODULUS,
   4 = SOLID_BULK_MODULUS,
   19 = FLUID_DENSITY,
   20 = BIOT_MODULUS,
 // BIOT_ISOTROPIC
   0 = PERMEABILITY,
   5 = BIOT_ALPHA,
 // BIOT_ORTHOTROPIC
   6 = PERMEABILITY_XX,      7 = PERMEABILITY_XY,     8 = PERMEABILITY_XZ,
   9 = PERMEABILITY_YX,      10 = PERMEABILITY_YY,    11 = PERMEABILITY_YZ,
   12 = PERMEABILITY_ZX,     13 = PERMEABILITY_ZY,    14 = PERMEABILITY_ZZ,
   21 = BIOT_ALPHA_X,        22 = BIOT_ALPHA_Y,       23 = BIOT_ALPHA_Z
 // BIOT_TRANSVERSAL_ISOTROPIC
   15 = PERMEABILITY_T,      16 = PERMEABILITY_TT,
   17 = PERMEABILITY_TL,     18 = PERMEABILITY_L,
   24 = BIOT_ALPHA_T,        25 = BIOT_ALPHA_L
```

```
plasticity
 // MISES
   0 = YIELD_STRENGTH,
 // DRUCKER_PRAGER, MOHR_COULOMB
   5 = YIELD_STRENGTH_COMPR,
   7 = COHESION,
   8 = INTERNAL_FRICTION_ANGLE,
   9 = DILATANCY_ANGLE
 // DRUCKER_PRAGER_CREEP
   21 = DPC_A,
   22 = DPC_B,
   23 = DPC_M
```

```
hardening
 //LINEAR
   2 = E_TAN,             10 = E_TAN_COMPR,
   1 = TENSILE_STRAIN,    6 = TENSILE_STRAIN_COMPR,
 //MULTILINEAR
   3 = HARDENING,
   11 = HARDENING_COMPR,
   41 = HARDENING_COHES,
```

```
creep
 // NORTON
   38 = C1,
   39 = C2,
   40 = C3
```

```
preload
 // INITIAL
   0 = STRESS_XX,             1 = STRESS_YY,             2 = STRESS_ZZ,
   3 = STRESS_XY,             4 = STRESS_YZ,             5 = STRESS_XZ,
   6 = STRAIN_XX,             7 = STRAIN_YY,             8 = STRAIN_ZZ,
   9 = STRAIN_XY,             10 = STRAIN_YZ,            11 = STRAIN_XZ,
   12 = PSI_XX,               13 = PSI_YY,               14 = PSI_ZZ,
   15 = PSI_XY,               16 = PSI_YZ,               17 = PSI_XZ,
   18 = PSI_YX,               19 = PSI_ZY,               20 = PSI_ZX,
   21 = GRADIENT_XX,          22 = GRADIENT_YY,          23 = GRADIENT_ZZ,
   24 = GRADIENT_XY,          25 = GRADIENT_YZ,          26 = GRADIENT_XZ,
   27 = GRADIENT_YX,          28 = GRADIENT_ZY,          29 = GRADIENT_ZX,
   30 = PLASTIC_STRAIN_XX,    31 = PLASTIC_STRAIN_YY,    32 = PLASTIC_STRAIN_ZZ,
   33 = PLASTIC_STRAIN_XY,    34 = PLASTIC_STRAIN_YZ,    35 = PLASTIC_STRAIN_XZ,
   36 = FINGER_STRAIN_XX,     37 = FINGER_STRAIN_YY,     38 = FINGER_STRAIN_ZZ,
   39 = FINGER_STRAIN_XY,     40 = FINGER_STRAIN_YZ,     41 = FINGER_STRAIN_XZ,
   42 = PLASTIC_STRAIN_MISES,
   43 = THERMAL_STRESS_XX,    44 = THERMAL_STRESS_YY,    45 = THERMAL_STRESS_ZZ,
   46 = THERMAL_STRESS_XY,    47 = THERMAL_STRESS_YZ,    48 = THERMAL_STRESS_XZ
```

```
strength
 // ISOTROPIC
   0 = TENSILE_STRENGTH,
   1 = TENSILE_STRENGTH_COMPR
```

### property_tables

```
[
   {
       "id": <unsigned short int>,        // Номер таблицы свойств
       "name": <string>,                  // Описание таблицы свойств
       "type": <int>,                     // Тип таблицы свойтв
       "direction_normal": <bool>         // Определяет направление слоев для типа SHELL.
                                          // True - вдоль нормали, False - против нормали.
       "thickness_change": <bool>         // Определяет, нужно ли включать изменение по толщине оболочки в SEM
       "properties": {...}                // Cвойства
       "layers":                          // Свойства слоев оболочек. Для типа SHELL.
       {
          "properties":
          [
             {
                "angle" : <double>,       // Угол поворота слоя относительно локальной СК элемента
                "material_id" : <int>,    // ID материала слоя
                "t" : <double>            // Толщина слоя
             },
             {...}                        // Свойства следующего слоя
          ]
       }

   },
   {...}         // Следующая таблица свойств
]
```

#### type

```
0 = SHELL,
1 = BEAM,
5 = LUMPMASS,
6 = SPRING
```

#### properties

```
Здесь описаны задаваемые свойства в зависимости от типа таблицы.
//SHELL
  {
     "e": <double>    // Эксцентриситет заданной геометрии относительно срединной поверхности.
                      // Меняется от 0 (нижняя поверхность), до 1 (верхняя поверхность).
  }
```

```
//LUMPMASS
  {
     "mass": <double>,               // Масса. Взаимоисключающее свойство с набором
                                     // свойств mass_x, mass_y, mass_z
     "mass_x": <double>,             // Распределение массы по оси X.
     "mass_y": <double>,             // Распределение массы по оси Y.
     "mass_z": <double>,             // Распределение массы по оси Z.
     "mass_inertia": <double>,       // Момент инерции. Взаимоисключающее свойство с набором
                                     // свойств mass_inertia_x, mass_inertia_y, mass_inertia_z
     "mass_inertia_x" : <double>,    // Момент инерции вокруг оси X
     "mass_inertia_y" : <double>,    // Момент инерции вокруг оси Y
     "mass_inertia_z" : <double>     // Момент инерции вокруг оси Z
  }
```

```
//SPRING
  {
     "spring_type": <string>,                           // Тип пружины. Варианты: "linear_spring", "combined_spring".

     //Свойства linear_spring:
     "stiffness": <double>,                             // Жесткость на растяжение
     "spring_constant_damping": <double>,               // Коэффициент постоянного демпфирования
     "spring_linear_damping": <double>,                 // Линейный коэффициент демпфирования
     "spring_mass" : <double>,                          // Масса
     "stiffness_torsional": <double>,                   // Жесткость при кручении
     "spring_constant_damping_torsional" : <double>,    // Коэффициент демпфирования при кручении
     "spring_linear_damping_torsional" : <double>,      // Коэффициент линейного демпфирования при кручении
     "spring_inertia" : <double>,                       // Момент инерции

     //Свойства combined_spring:
     "k1": <double>,                                    // Жесткость пружины 1
     "k2": <double>,                                    // Жесткость пружины 2
     "gap": <double>,                                   // Зазор
     "limit_sliding_force": <double>,                   // Предельная сила скольжения
     "damping": <double>,                               // Коэффициент постоянного демпфирования
     "mass": <double>,                                  // Масса пружины
     "mass_distribution": <int>,                        // Распределение массы между узлами.
                                                        // Варианты:
                                                        // -1 - распределение на узел 0;
                                                        // 1 - распределение на узел 1;
                                                        // 0 - равномерное распределение между узлами 0 и 1.
  }
```

```
//BEAM
  {
     "section_type": <int>,               // Тип балочного сечения
     "angle": <double>,                   // Угол поворота сечения
     "ey": <double>,                      // Эксцентриситет по локальной оси Y
     "ez": <double>,                      // Эксцентриситет по локальной оси Z
     "mesh_quality" : <double>,           // Качество сетки сечения для отображения в 3D виде.
     "warping_dof" : <double>,            // Включение дополнительной степени свободы на кручение сечения

     // Параметры сечения POINT, не имеющего сетки
     "area": <double>,                    // Площадь сечения
     "Ip": <double>,                      // Момент инерции отн. оси х
     "Iy": <double>,                      // Момент инерции отн. оси y
     "Iyz": <double>,                     // Центробежный момент инерции
     "Iz": <double>,                      // Момент инерции отн. оси z
     "It": <double>,                      // Геометрическая жесткость при кручении
     "Iw" :<double>,                      // Момент инерции Iw
     "max_y": <double>,                   // Координата максимального отдаления по Y от центра масс со знаком
     "max_z": <double>,                   // Координата максимального отдаления по Z от центра масс со знаком
     "shear_coefficient_yy": <double>,    // Коэффициент сдвига YY
     "shear_coefficient_zz": <double>,    // Коэффициент сдвига ZZ
     "shear_coefficient_zy": <double>,    // Коэффициент сдвига ZY
     "shear_center_y": <double>,          // Координата Y центра изгиба
     "shear_center_z": <double>,          // Координата Z центра изгиба

     // Параметры отображения сечений, имеющих сетку
     geometry:
     {
        //RECTANGLE
        "B": <double>,                    // Ширина
        "H": <double>,                    // Высота

        //ELLIPSE
        "a": <double>,                    // Большая ось
        "b": <double>,                    // Малая ось

        //I_BEAM
        "B1": <double>,                   // Нижняя ширина
        "B2": <double>,                   // Верхняя ширина
        "H": <double>,                    // Высота
        "c2": <double>,                   // Верхняя толщина
        "c1": <double>,                   // Нижняя толщина
        "d": <double>                     // Толщина

        //CIRCLE_WITH_A_CUT
        "D1": <double>,                   // Внешний диаметр
        "D2": <double>,                   // Внутренний диаметр
        "e": <double>,                    // Смещение

        //C_BEAM
        "H": <double>,                    // Высота (H)
        "B2": <double>,                   // Верхняя ширина (B2)
        "B1": <double>,                   // Нижняя ширина (B1)
        "c2": <double>,                   // Верхняя толщина (c2)
        "c1": <double>,                   // Нижняя толщина (c1)
        "d": <double>                     // Толщина (d)

        //L_BEAM
        "H": <double>,                    // Высота (H)
        "B": <double>,                    // Нижняя ширина (B)
        "d": <double>,                    // Верхняя толщина (d)
        "c1": <double>,                   // Нижняя толщина (c1)

        //Z_BEAM
        "H": <double>,                    // Высота (H)
        "B2": <double>,                   // Верхняя ширина (B2)
        "B1": <double>,                   // Нижняя ширина (B1)
        "c2": <double>,                   // Верхняя толщина (c2)
        "c1": <double>,                   // Нижняя толщина (c1)
        "d": <double>                     // Толщина (d)

        //T_BEAM
        "H": <double>,                    // Высота (H)
        "B": <double>,                    // Нижняя ширина (B)
        "d": <double>,                    // Верхняя толщина (d)
        "c1": <double>,                   // Нижняя толщина (c1)

        //RECTANGLE_WITH_A_CUT
        "H": <double>,                    // Высота (H)
        "B": <double>,                    // Ширина (B)
        "d1": <double>,                   // Левая толщина (d1)
        "d2": <double>                    // Правая толщина (d2)
        "c2": <double>,                   // Верхняя толщина (c2)
        "c1": <double>,                   // Нижняя толщина (c1)

        //HAT_BEAM
        "H": <double>,                    // Высота (H)
        "B3": <double>,                   // Верхняя ширина (B3)
        "B1": <double>,                   // Нижняя левая ширина (B1)
        "B2": <double>,                   // Нижняя правая ширина (B2)
        "d1": <double>,                   // Левая толщина (d1)
        "d2": <double>                    // Правая толщина (d2)
        "c3": <double>,                   // Верхняя толщина (c3)
        "c1": <double>,                   // Нижняя левая толщина (c1)
        "c2": <double>,                   // Нижняя правая толщина (c2)

        //PIPE
        "d1" : <double>,                  // Внешний диаметр
        "d2" : <double>,                  // Внутренний диаметр
        "p1" : <double>,                  // Внешнее давление
        "p2" : <double>                   // Внутреннее давление
     }
  }
```

##### section_type

```
0 = RECTANGLE,               // Прямоугольник
1 = ELLIPSE,                 // Эллипс
2 = I_BEAM,                  // Двутавр
3 = CIRCLE_WITH_A_CUT,       // Круг со смещенным отверстием
4 = POINT,                   // Ручная настройка параметров сечения
5 = C_BEAM,                  // Швеллер
6 = L_BEAM,                  // Уголок
7 = Z_BEAM,                  // Z-сечение
8 = T_BEAM,                  // Тавр
9 = RECTANGLE_WITH_A_CUT,    // Полый прямоугольник
10 = HAT_BEAM,               // Корытный профиль
12 = PIPE                    // Труба
```

### sets

```
{
   "nodesets":                            // Наборы узлов
   [
      {
         "id": <int>,                     // Номер набора узлов
         "name": <string>,                // Имя набора узлов
         "apply_to": [int],               // Массив id узлов. В Base64 кодируется одной строкой
         "apply_to_size": <int>           // Количество узлов в наборе
      }
   ],
   "sidesets":                            // Наборы сторон
   [
      {
         "id": <int>,                     // Номер набора сторон
         "name": <string>,                // Имя набора сторон
         "apply_to": [ [int, int] ],      // Массив массивов размерности 2, содержащих [id элемента, номер грани/ребра].
                                          // В Base64 кодируется весь массив массивов как одна строка.
         "apply_to_size": <int>           // Количество сторон элементов в наборе
      }
   ]
}
```

### loads

```
[
   {
      "id": <int>,                          // Номер нагрузки
      "name": string,                       // Описание нагрузки
      "type": <int>,                        // Тип нагрузки
      "data": [double],                     // Массив массивов значений компонент нагрузки.
                                            // В Base64 кодируется каждый элемент (константа или массив) основного
                                            // массива, формулы записываются строкой без кодирования.
                                            // Пустая строка для неактивной компоненты нагрузки.
      apply_to_size: <int>,                 // Количество объектов, к которым прикладывается нагрузка
      apply_to: [int]",                     // Массив объектов, к которым применяется нагрузка. Кодируется в Base64 одной строкой.
                                            // Тип объекта (узел, сторона, элемент) зависит от типа нагрузки.
                                            // Может иметь строковое значение "all", если применяется ко всем объектам.
      "dep_var_num": [double]               // Массив размерностей табличной зависимости каждой компоненты нагрузки (количество строк таблицы).
                                            // В Base64 каждый элемент основного массива кодируется отдельно.
                                            // Равно 0 для константы и формулы
      "dep_var_size": [int],                // Массив размерностей табличной зависимости каждой компоненты нагрузки(количество строк таблицы).
                                            // Равно 0 для константы и формулы
      "dependency_type": [int | string],    // Массив массивов типов зависимостей каждой компоненты нагрузки.
                                            // При многомерных табличных зависимостях у одной компоненты может быть несколько TABULAR_* зависимостей.
                                            // Компонента массива равна пустой строке для неактивной компоненты нагрузки
   }
]
```

#### type

```
// Типы нагрузок и объекты приложения
// Нагрузки на грань
1 = FaceDeadStress,                      // Давление на грань. 1 компонента в data
3 = FaceTrackingStress,                  // Следящее давление на грань. 1 компонента в data
11 = FaceHeatFlux,                       // Тепловой поток на грани. 1 компонента в data
13 = FaceConvection,                     // Конвекция на грани. 2 компоненты в data:
                                         // температура внешней среды, коэффициент теплоотдачи
15 = FaceRadiation,                      // Излучение на грани. 2 компоненты в data:
                                         // температура внешней среды, излучательная способность
19 = FaceAbsorbingBC,                    // Поглощающее ГУ на грани. Нет компонент в data
21 = ShellHeatfluxTopBottom,             // Тепловой поток верх и низ. 2 компоненты в data:
                                         // тепловой поток верха и тепловой поток низа.
22 = ShellHeatfluxTop,                   // Тепловой поток верх. 1 компонента в data
23 = ShellHeatfluxBottom,                // Тепловой поток низ. 1 компонента в data
24 = ShellConvectionTopBottom,           // Конвекция верх и низ. 4 компоненты в data:
                                         // температура внешней среды сверху, коэффициент теплоотдачи сверху,
                                         // температура внешней среды снизу, коэффициент теплоотдачи снизу
25 = ShellConvectionTop,                 // Конвекция верх. 2 компоненты в data:
                                         // температура внешней среды сверху, коэффициент теплоотдачи сверху
26 = ShellConvectionBottom,              // Конвекция низ. 2 компоненты в data:
                                         // температура внешней среды снизу, коэффициент теплоотдачи снизу
35 = FaceDistributedForce,               // Распределенная сила на грань. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
36 = FaceEquivalentForce,                // Равнодействующая сила на грань. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
37 = FaceTrackingDistributedForce,       // Следящая распределенная сила на грань. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
38 = FaceTrackingEquivalentForce,        // Следящая равнодействующая сила на грань. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
39 = FaceFluidFlux,                      // Поток жидкости через грань. 1 компонента в data
// Нагрузки на ребро
2 = SegmentDeadStress,                   // Давление на ребро. 1 компонента в data
4 = SegmentTrackingStress,               // Следящее давление на ребро. 1 компонента в data
12 = SegmentHeatFlux,                    // Тепловой поток на ребре. 1 компонента в data
14 = SegmentConvection,                  // Конвективный теплообмен на ребре. 2 компоненты в data:
                                         // температура внешней среды, коэффициент теплоотдачи
16 = SegmentRadiation,                   // Излучение на ребре. 2 компоненты в data:
                                         // температура внешней среды, излучательная способность
20 = SegmentAbsorbingBC,                 // Поглощающее ГУ на ребре. Нет компонент в data
31 = SegmentDistributedForce,            // Распределенная сила на ребро. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
32 = SegmentEquivalentForce,             // Равнодействующая сила на ребро. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
33 = SegmentTrackingDistributedForce,    // Следящая распределенная сила на ребро. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
34 = SegmentTrackingEquivalentForce,     // Следящая равнодействующая сила на ребро. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
40 = SegmentFluidFlux,                   // Поток жидкости через ребро. 1 компонента в data
// Нагрузки на узел
5 = NodeForce,                           // Узловая сила. 6 компонент в data:
                                         // сила по X, Y, Z, момент по X, Y, Z
18 = HeatSource,                         // Узловой источник тепла. 1 компонента в data
28 = NodeHeatFlux,                       // Узловой тепловой поток. 1 компонента в data
29 = NodeConvection,                     // Узловая конвекция. 2 компоненты в data:
                                         // температура внешней среды, коэффициент теплоотдачи
30 = NodeRadiation,                      // Узловое излучение. 2 компоненты в data:
                                         // температура внешней среды, излучательная способность
41 = NodeFluidFlux,                      // Поток жидкости через узел. 1 компонента в data
43 = FluidSource,                        // Узловой источник жидкости. 1 компонента в data
// Нагрузки на элемент
17 = VolumeHeatSource,                   // Объемный источник тепла. 1 компонента в data
42 = VolumeFluidSource,                  // Объемный источник жидкости. 1 компонента в data
44 = VolumeGravityMassForce              // Гравитация. 3 компоненты в data:
                                         // по X, Y, Z
```

### restraints

```
[
   {
      "id": <int>,                           // Номер закрепления
      "name": <string>,                      // Описание закрепления
      "flag": [int],                         // Массив типов закрепления по каждому направлению.
       "data": [double | string]             // Массив массивов значений компонент ГУ.
                                             // В Base64 кодируется каждый элемент (константа или массив) основного
                                             // массива, формулы записываются строкой без кодирования.
                                             // Пустая строка для неактивной компоненты ГУ.
       "apply_to":[int] | <string>,          // Массив объектов, к которым применяется ГУ. Кодируется в Base64 одной строкой.
                                             // Тип объекта (узел, сторона, элемент) зависит от применяемого ГУ.
                                             // Может иметь строковое значение "all", если применяется ко всем объектам.
       "apply_to_size": <unsigned int>,      // Количество объектов, к которым прикладывается закрепление.
       "dep_var_num": [double]               // Массив размерностей табличной зависимости каждой компоненты ГУ (количество строк таблицы).
                                             // В Base64 каждый элемент основного массива кодируется отдельно.
                                             // Равно 0 для константы и формулы
       "dep_var_size": [int],                // Массив размерностей табличной зависимости каждой компоненты ГУ (количество строк таблицы).
                                             // Равно 0 для константы и формулы
       "dependency_type": [int | string],    // Массив массивов типов зависимостей каждой компоненты ГУ.
                                             // При многомерных табличных зависимостях у одной компоненты может быть несколько TABULAR_* зависимостей.
                                             // Компонента массива равна пустой строке для неактивной компоненты ГУ
       "step" :
   },
   {...}                                   // Следующее ГУ
]
```

#### flag

```
// Здесь перечислены вырианты значений и величина массива типов закреплений
0 = EmptyRestraint,            // Отсутствует закрепление. Применяется в массивах вместе с остальными вариантами.
1 = Displacement,              // ГУ по перемещениям и поворотам для узлов.
                               // Длина массива равна 6.
                               // Пример. "flag": [1, 0, 0, 0, 1, 0]
2 = Velocity,                  // ГУ по скоростям и скоростям поворотов для узлов.
                               // Длина массива равна 6
3 = Temperature,               // ГУ по температуре для узлов.
                               // Длина массива равна 1.
                               // Пример. "flag": [3]
4 = TemperatureTop,            // Температура на верхней поверхности. Для для узлов оболочечных элементов.
                               // Применяется вместе с TemperatureBottom.
                               // Длина массива равна 2.
                               // Пример. "flag": [4, 5]
5 = TemperatureBottom,         // Температура на нижней поверхности. Для для узлов оболочечных элементов.
                               // Применяется вместе с TemperatureTop.
                               // Длина массива равна 2
6 = TemperatureMiddle,         // Температура для узлов на срединной поверхности оболочечного элемента.
                               // Может применяться самостоятельно или вместе с TemperatureGradient.
                               // Длина массива равна 1 или 2.
                               // Пример 1. "flag": [6].
                               // Пример 2. "flag": [6, 7]
7 = TemperatureGradient,       // Градиент температуры для узлов оболочечного элемента.
                               // Может применяться самостоятельно или вместе с TemperatureMiddle.
                               // Длина массива равна 1 или 2
                               // Пример 1. "flag": [7]
9 = Acceleration,              // ГУ по ускорениям и угловым ускорениям для узлов.
                               // Длина массива равна 6.
                               // Пример. "flag": [9, 0, 9, 0, 0, 0]
10 = PorePressure,             // ГУ по поровому давлению для узлов.
                               // Длина массива равна 1.
                               // Пример. "flag": [10]
12 = DirectionDisplacement,    // ГУ по направлению по перемещениям. Применяется к граням элементов.
                               // Длина массива равна 1
13 = DirectionVelocity,        // ГУ по направлению по скоростям. Применяется к граням элементов.
                               // Длина массива равна 1
14 = DirectionAcceleration,    // ГУ по направлению по ускорениям. Применяется к граням элементов.
                               // Длина массива равна 1
15 = VolumeAngularVelocity,    // ГУ по угловым скоростям. Применяется к элементам.
                               // Длина массива равна 3.
                               // Пример. "flag": [15, 15, 0]
```

### initial_sets

```
[
   {
      "id": <int>,                    // Номер начальных условий (НУ)
      "name": <string>,               // Название НУ
      "type": <int>,                  // Тип НУ
      "flag": [int],                  // Массив флагов, указывающих для каких параметров заданы начальные условия.
                                      // 0 - не задано НУ, 1 - есть НУ
                                      // Размер массива равен 6 для типов НУ  Displacement и Velocity,
                                      // равен 3 для типа AngularVelocity, равен 1 для типов Temperature и PorePressure.
      "apply_to":[int] | <string>,    // Массив номеров узлов, к которым применяется НУ. Кодируется в Base64 как одна строка.
                                      // Может быть заменен на строку "all", если НУ применяется ко всем узлам модели.
      "apply_to_size": <int>,         // Количество узлов, к которым прикладывается НУ
      "dep_var_size": [int]           // Массив размерностей табличной зависимости каждой компоненты (количество строк таблицы).
                                      // Равно 0 для константы и формулы
      "dep_var_num": [double]         // Массив аргументов табличной зависимости (по столбцам, если зависимостей больше 1).
                                      // Кодируется в Base64 одной строкой.
                                      // Равно пустой строке "" для константы и формулы
      "data": [[double]|<string>]     // Массив длиной равный длине flag. Компоненты масси max_dof_bc содержащий табличные значения (в Base64) или формулу (покомпонентно).
      "dependency_type": [int]        // Тип зависимости компонент начальных условий. См. const_types в разделе с материалами.
   }
]
```

#### type

```
0 = Displacement,
1 = Velocity,
2 = AngularVelocity,
3 = Temperature,
4 = PorePressure
```

### contact_constraints

```
[
   {
      "detection_tolerance": <double>,    // точность поиска контакта по касательной
      "friction": <double>,               // Коэффициент трения. Применяется для контакта типа "general".
      "id": <int>,                        // Номер контакта
      "ignore_overlap": <bool>,           // Игнорирует начальный нахлест. Применяется для контакта типа "general".
      "name": <string>,                   // Имя контакта
      "step": [int],                      // Шаги, на которых контакт активен
      "master_size": <int>,               // Количество узлов главной сущности
      "master": "[int, int]",             // Массив пар [id_элемента, id_стороны] главной сущности. Кодируется в Base64 единой строкой.
      "slave_size": <int>,                // Количество узлов побочной сущности.
      "slave": "[elem_id, face_id]",      // Массив пар [id_элемента, id_стороны] побочной сущности. Кодируется в Base64 единой строкой.
      "type": <string>,                   // Тип контакта. Варианты: "general", "tied", "tied_normal", "tied_tangent".
      "method": <string>,                 // Метод задания контакта. Варианты: "auto", "penalty", "mpc".
      "tolerance": <double>,              // Точность поиска контакта "general", "tied", "tied_normal".
      "offset": <double>,                 // Зазор. Применяется для контакта типов.
      "preload": <double>,                // Преднатяг. Применяется для контакта типа "tied_tangent".
      "normal_stiffness": <double>,       // Жесткость контакта по нормали. Применяется для метода "penalty".
      "tangent_stiffness": <double>,      // Жесткость контакта по касательной. Применяется для метода "penalty".
      "search_radius": <double>,          // Радиус поиска контактной поверхности.
      "max_overlap": <double>,            // Максимальное проникновение.
   }
]
```

### coupling_constraints

```
[
   {
      "id": <int>,                    // Номер связи
      "name": <string>,               // Имя связи
      "cs": <int>,                    // СК, в которой задана связь
      "step": [int],                  // Шаги, на которых связь активна
      "master": [int],                // Массив узлов главной сущности. В Base64 кодируется единой строкой
      "master_size": <int>,           // Количество узлов главной сущности
      "slave": [int],                 // Массив узлов побочной сущности. В Base64 кодируется единой строкой
      "slave_size": <int>,            // Количество узлов побочной сущности
      "type": <int>,                  // Тип связи
      "dofs": [int],                  // Массив степеней свободы. Всегда 6 компонент, включенные степени свободы равны 1,
                                      // остальные равны 0. Для связей типа ELASTICITY.
      "stiffness": [double],          // Жёсткость связи. Используется для типов связей ELASTICITY или DIRECTION.
      "direction": [double]           // Направление
      "master_dofs": [int],           // Массив степеней свободы главной сущности. Всегда 6 компонент,
                                      // включенные степени свободы равны 1, остальные равны 0. Для связей типа INTERPOLATION.
      "slave_dofs": [int],            // Массив степеней свободы побочной сущности. Всегда 6 компонент,
                                      // включенные степени свободы равны 1, остальные равны 0. Для связей типа INTERPOLATION.
      "distance_weighting": <bool>    // Включает расчет весовых коэффициентов связи в зависимости от расстояния между сущностями
                                      // Для связей типа INTERPOLATION.
      "factor": <int>                 // Множитель для весов связей типа INTERPOLATION.
   }
]
```

#### type

```
0 = ELASTICITY,       // Связь по перемещениям/поворотам
1 = TEMPERATURE,      // Связь по температуре
2 = DISTANCE,         // Связь по расстоянию (RBE2)
3 = PORE_PRESSURE,    // Связь по поровому давлению
4 = DIRECTION,        // Связь по направлению
5 = INTERPOLATION     // Интерполяционная связь (RBE3)
```

### periodic_constraints

```
[
   {
      id: <int>,             // Номер ГУ
      name: <string>,        // Имя ГУ
      cs: <int>,             // Система координат, в котрой применяется ГУ
      step: [int],           // Шаги, на которых ГУ активно
      master_size: <int>,    // Количество сторон, принадлежащих главной сущности
      master: [int, int],    // Массив сторон главной сущности, представленный в виде пар [id элемента, id грани/ребра].
                             // В Base64 кодируется одной строкой
      slave_size: <int>,     // Количество сторон, принадлежащих побочной сущности
      slave: [int, int],     // Массив сторон побочной сущности, представленный в виде пар [id элемента, id грани/ребра].
                             // В Base64 кодируется одной строкой
      type: <int>,           // Тип периодического ГУ
      sectors: <int>         // Количество секторов
   }
]
```

#### type

```
 0 = ALL,
 1 = DISPLACEMENT,
 2 = THERMAL_CONDUCTION,
 3 = PORE_PRESSURE_CONDUCTION,
 4 = VELOCITY,
 5 = ACCELERATION
```

### receivers

```
[
   {
      id: <int>,               // Номер набора приемников
      name: <string>,          // Имя набора приёмника
      apply_to: [<int>],       // Id узлов, которые являются приемниками в наборе
      apply_to_size: <int>,    // Количество приемников в наборе
      type: <int>,             // Тип набора приёмников
      dofs: [<int>],           // Степени свободы, которые нужно выводить. Обязательный параметр для наборов всех типов, кроме PRESSURE.
      output_step: <int>       // Сохранять результаты каждые output_step шагов
   },
   {...}                       // Следующий набор приемников
]
```

#### type

```
 0 = DISPLACEMENT,
 1 = VELOCITY,
 2 = PRINCIPAL_STRESS,
 3 = PRESSURE,
 4 = ACCELERATION
```

### settings

```
{
   "type": <string>,                       // Тип расчета
                                           // Варианты: "static", "dynamic", "eigenfrequencies",
                                           // "buckling", "spectrum", "harmonic", "effectiveprops"
   "dimensions": <string>,                 // Размерность задачи. Варианты: "2D", "3D"
   "plane_state": <string> ,               // Выды расчетов для размерности "2D". Варианты: "p-stress", "p-strain", "axisym_x", "axisym_y"
   "permission_write": <bool>,             // Разрешить запись на жесткий диск, если недостаточно оперативной памяти
   "periodic_bc": <bool>,                  // Периодические ГУ для расчета эффективных свойств
   "finite_deformations": <bool>,          // Включить конечные деформации
   "elasticity": <bool>,                   // Включить упругость
   "plasticity": <bool>,                   // Включить пластичность
   "heat_transfer": <bool>,                // Включить теплопроводность
   "porefluid_transfer" : <bool>,          // Включить пьезопроводность
   "slm" : <bool>,                         // Включить аддитивное производство
   "incompressibility": <bool>,            // Включить несжимаемость
   "preload": <bool>,                      // Преднагруженная модель
   "lumpmass": <bool>,                     // Использовать лумпингованую диагональную матрицу масс
   "radiation_among_surfaces" : <bool>,    // Включить лучистый теплообмен
   "linear_solver": {...},                 // Настройки линейного решателя
   "nonlinear_solver": {...},              // Настройки нелинейного решателя
   "damping": {...},                       // Настройки демпфирования
   "thermal_gap_settings": {...},          // Настройки решателя для газового зазора
   "eigen_solver": {...},                  // Настройки решателя собственных частот
   "dynamics": {...},                      // Настройки динамического расчета
   "statics" : {...},                      // Настройки статического расчета
   "harmonic": {...},                      // Настройки гармонического расчета
   "output": {...},                        // Настройки вывода данных
   "test_opts": {...}                      // Настройки отладочной версии ядра
}
```

#### linear_solver

```
{
   "method": <string>,                  // Метод решения СЛАУ. Варианты: "auto", "direct", "iterative"
   "iter_opts":                         // Настройки итерационного решателя
   {
      "epsilon": <double>,              // Относительная точность
      "stopping_criteria": <double>,    // Абсолютная точность
      "max_iterations": <int>,          // Максимальное число итераций
      "preconditioner": <string>        // Выбор прекондиционера
                                        // Варианты: "auto", "no", "diagonal", "ilu0", "ilu2", "ilut"
   }
   "on_fail": <bool>,                   // Использовать другие методы при ошибке. Только для метода "auto"
   "use_uzawa": <string>,               // Использовать метод Узавы. Варианты: "auto", "yes", "no"
   "uzawa_max_iterations": <int>,       // Максимальное количество итераций метода Узавы
   "uzawa_rel_precision": <double>      // Относительная точность метода Узавы
}
```

#### nonlinear_solver

```
{
   "arc_method": <bool>,       // Включить метод окаймляющих дуг
   "line_search": <bool>,      // Включить линейный поиск
   "max_iterations": <int>,    // Максимальное число итераций
   "min_load_steps": <int>,    // Минимальное число подшагов нагружения
   "max_load_steps": <int>,    // Максимальное число подшагов нагружения
   "tolerance": <double>,      // Точность
   "target_iter": <int>        // Целевое число итераций
}
```

#### eigen_solver

```
{
      number: <int> | <string>,                      // Количество собственных частот.
                                                     // Если нужно вывести все в диапазоне, тогда параметр становится строкой со значением "all"
      target: <double> | [double],                   // Целевое значение частоты или диапазон частот (2 значения в массиве)
      solver: <string>,                              // Метод решения. Варианты: "auto", "krylovschur", "arnoldi", "lanczos", "gd", "jd"
      spectr_trans:                                  // Настройки спектрального преобразования
      {
         "name": <string>,                           // Название спектрального преобразования.
                                                     // Варианты: "auto" | "shift" | "shift_invert" | "general_cayley",
         "shift_value": <double>,                    // Значение сдвига для методов "shift", "shift_invert" или "general_cayley"
         "anti_shift_value": <double>                // Значение обратного сдвига для метода "general_cayley"
      },
      linear_solver:                                 // Настройки линейного решателя для СЧ
      {
         solver: <string>,                           // Решатель СЛАУ. Варианты: "auto", "direct", "iterative"
         method: <string>,                           // Тип итерационного решателя.
                                                     // Варианты: "auto", "preonly", "cg", "gmres","richardson",
                                                     // "chebyshev", "bicg", "bcgs", "minres", "tfqmr", "cr", "gcr"
         preconditioner:                             // Тип прекондиционера.
                                                     // Варианты: "auto", "lu", "none", "jacobi", "bjacobi", "sor", "ssor", "ilu", "asm"
         iter_opts:                                  // Настройки итерационного решателя для СЧ
         {
            linear_absolute_tolerance: <double>,     // Абсолютная точность
            linear_relative_tolerance: <double>,     // Относительная точность
            linear_max_iterations: <int>,            // Максимальное число итераций
            linear_divergence_tolerance: <double>    // Допустимое отклонение
         }
      }
      relative_tolerance: <float value>,             // Относительная точность решателя СЧ
      absolute_tolerance: <float value>,             // Абсолютная точность решателя СЧ
      eps_max_iterations: <int value>,               // Максимальное число итераций решателя СЧ
      evaluate_effective_mass: <bool value>,         // Вычислять эффективные массы
      rotation_center: [double]                      // Массив из 3х значений, определяющих точку, относительно
                                                     // которой считать моменты инерции модели при включенном evaluate_effective_mass
}
```

#### damping

```
{
   "use" : <bool>,                  // Использовать демпфирование в расчете
   "structural": <double>,          // Значение конструкционного демпфирования
   "mass_matrix": <double>,         // Значение демпфирования матрицы масс
   "stiffness_matrix": <double>,    // Значение демпфирования матрицы жесткости
   "coriolis" : <bool>,             // Учитывать эффект Кориолиса
}
```

#### thermal_gap_settings

```
{
   "start_temp" : <double>,       // Начальная температура
   "end_temp" : <double>,         // Конечная температура
   "step_temp" : <double>,        // Шаг по температуре
   "scatangle_eps" : <double>,    // Точность угла рассеяния
   "impact_eps" : <double>,       // Точность по прицельному параметру
   "velocity_eps" : <double>      // Точность по относительной скорости
}
```

#### statics

```
   {
      "result_output_time": <double>        // Вывод результатов каждый result_output_time временной интервал.
                                            // Взаимоисключающий параметр с параметрами "result_output_iter" и "result_number"
      "result_output_iter": <int>,          // Вывод результатов каждый result_output_iter шаг
      "result_number": <int>,               // Общее количество выводимых шагов
      "steps_count": <int>                  // Количество статических шагов
   }
```

#### dynamics

```
   {
      method: <string>,                     // Метод решения. Варианты: "full_solution", "mod_superposition"
      scheme: <string>,                     // Схема решения. Варианты: "explicit", "implicit"
      max_time: <double>,                   // Максимальное время решения
      time_step: <double>,                  // Шаг по времени
      steps_count: <int>,                   // Количество шагов по времени
      courant: <double >=0 <=1>,            // Число Куранта. Только для явной схемы
      max_steps_count: <int>,               // Максимальное число шагов. Только для явной схемы
      newmark_gamma: <double>,              // Параметр схемы Ньюмарка. Только для неявной схемы
      "result_output_time": <double>        // Вывод результатов каждый result_output_time временной интервал.
                                            // Взаимоисключающий параметр с параметрами "result_output_iter" и "result_number"
      "result_output_iter": <int>,          // Вывод результатов каждый result_output_iter шаг
      "result_number": <int>,               // Общее количество выводимых шагов
      mod_count: <int>
   },
```

#### harmonic

```
   {
      "method": <string>,                   // Метод решения. Значение только "mod_superposition"
      "frequency_step": <double>,           // Шаг по частоте для выбранного диапазона.
                                            // Взаимоисключающий параметр с "steps_count"
      "steps_count": <int>                  // Количество шагов в выбранном диапазоне.
   }
```

#### test_opts

```
   {
      "print_matrix_full": <bool>,          //Выводить полный вариант матрицы
      "print_matrix_txt": <bool>,           //Выводить текстовый вариант матрицы
      "print_matrix_bin": <bool>,           //Выводить бинарный вариант матрицы
      "print_matrix_ccs": <bool>,           //Выводить ccs вариант матрицы
      "precision": <int>,                   //Количество знаков после запятой при выводе матрицы
      "output_iteration_results": <bool>    //Выводить результат на итерациях
   }
```

#### output

```
   {
      "energy": <bool>,                     // Вычислять кинетическую энергию и энергию деформации
      "intermediate_results": <bool>,       // Выводить промежуточный результат. Только для нелинейных задач
      "log": <bool>,                        // Выводить Log
      "normal_force": <bool>,               // Вычислять силу реакции опоры
      "record3d": <bool>,                   // Запись 3D-вида для балочных/оболочечных моделей
      "vtu": <bool>,                        // Выводить VTU
      "full_periodic" : <bool>,             // Выводить полную модель для периодических ГУ
      "material" : <bool>,                  // Выводить свойства материалов
      "model_properties" : <bool>,          // Выводить свойства модели
      "without_smoothing" : <bool>          // Выключить результаты без сглаживания
   }
```