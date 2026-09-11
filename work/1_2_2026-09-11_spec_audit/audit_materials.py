"""Independent audit of material and property-table sections of an FC JSON file."""

import base64
import binascii
import math
import struct
from typing import Dict, List, Optional, Sequence, Tuple, cast


Finding = Dict[str, object]

SPEC = "docs/FC_INPUT_FORMAT.md"
MATERIAL_LINE = "491"
PROPERTY_LINE = "811"
COMPONENT_LINE = "1822"

GROUP_TYPES = {
    "elasticity": {0, 1, 2, 3, 4, 11, 20, 21},
    "common": {0},
    "thermal": {0, 1, 2},
    "geomechanic": {0, 1, 2},
    "plasticity": {0, 1, 4, 9},
    "hardening": {0, 1},
    "creep": {0},
    "preload": {0},
    "strength": {0},
    # The specification names this group but does not publish a type table.
    "hsdf": None,
    "kinematic_hardening": None,
    "swelling": None,
}
GROUP_FIELDS = {"type", "const_names", "const_types", "const_dep_size", "constants", "const_dep"}
DEPENDENCY_CODES = {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12}
PROPERTY_TYPES = {0, 1, 5, 6}
SECTION_TYPES = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12}

NAME_CODES = {
    "elasticity": set(range(0, 11)) | set(range(16, 22)) | set(range(21, 30)) | set(range(82, 103)),
    "common": {0, 1, 2, 3},
    "thermal": {0, 1, 2, 3, 5, 9, 13, 14, 15, 16, 17, 18, 19, 20},
    "geomechanic": set(range(0, 26)),
    "plasticity": {0, 1, 5, 6, 7, 8, 9, 21, 22, 23},
    "hardening": {1, 2, 3, 6, 10, 11, 41},
    "creep": {38, 39, 40},
    "preload": set(range(49)),
    "strength": {0, 1},
}


def _f(rule: str, severity: str, path: str, message: str, actual: object,
       expected: object, line: str) -> Finding:
    return {"rule": rule, "severity": severity, "path": path, "message": message,
            "actual": actual, "expected": expected, "spec": f"{SPEC}:{line}"}


def _type_name(value: object) -> str:
    if isinstance(value, bool):
        return "bool"
    return type(value).__name__


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _decoded_length(value: object, item_size: int) -> Optional[int]:
    if isinstance(value, list):
        return len(value)
    if not isinstance(value, str):
        return None
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        return None
    if item_size <= 0 or len(raw) % item_size:
        return None
    return len(raw) // item_size


def _value_kind(value: object, item_size: int, binary: Optional[bool]) -> str:
    if isinstance(value, list):
        if binary is True:
            return "JSON array in binary mode"
        return "array" if all(_is_number(x) for x in value) else "invalid array"
    if isinstance(value, str):
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error):
            return "string"
        if item_size <= 0:
            return "base64 unknown width"
        return "base64" if len(raw) % item_size == 0 else "invalid base64"
    return _type_name(value)


def _audit_component(group: str, component: object, path: str, data: dict,
                     out: List[Finding]) -> None:
    if not isinstance(component, dict):
        out.append(_f("MAT.COMPONENT_TYPE", "violation", path,
                      "Компонент группы должен быть объектом.", _type_name(component), "object", COMPONENT_LINE))
        return
    for key in component:
        if key not in GROUP_FIELDS:
            out.append(_f("MAT.UNKNOWN_FIELD", "ambiguity", f"{path}.{key}",
                          "Неизвестное поле компонента не описано спецификацией.", "unknown", sorted(GROUP_FIELDS), MATERIAL_LINE))
    for key in ("type", "const_names", "const_types", "const_dep_size", "constants", "const_dep"):
        if key not in component:
            out.append(_f("MAT.COMPONENT_FIELD", "ambiguity", f"{path}.{key}",
                          "В компоненте отсутствует поле, нужное для однозначной интерпретации.",
                          "missing", "поле присутствует", COMPONENT_LINE))
    gtype = component.get("type")
    allowed_types = GROUP_TYPES.get(group)
    if allowed_types is None and group in GROUP_TYPES:
        out.append(_f("MAT.GROUP_SCHEMA", "ambiguity", f"{path}.type",
                      "Для этой группы спецификация не публикует таблицу типов.", "undocumented", "type table", MATERIAL_LINE))
    if not _is_int(gtype):
        out.append(_f("MAT.GROUP_TYPE", "ambiguity", f"{path}.type",
                      "Тип группы должен быть целым кодом.", _type_name(gtype), "int", MATERIAL_LINE))
    elif allowed_types is not None and gtype not in allowed_types:
        out.append(_f("MAT.GROUP_TYPE", "ambiguity", f"{path}.type",
                      "Код типа группы отсутствует в таблице спецификации.", gtype,
                      sorted(allowed_types), MATERIAL_LINE))
    names = component.get("const_names")
    types = component.get("const_types")
    sizes = component.get("const_dep_size")
    constants = component.get("constants")
    deps = component.get("const_dep")
    arrays = [("const_names", names), ("const_types", types), ("const_dep_size", sizes),
              ("constants", constants), ("const_dep", deps)]
    for key, value in arrays:
        if not isinstance(value, list):
            out.append(_f("MAT.COMPONENT_ARRAY", "violation", f"{path}.{key}",
                          "Компонентное поле должно быть JSON-массивом.", _type_name(value), "array", COMPONENT_LINE))
    if not all(isinstance(x[1], list) for x in arrays):
        return
    names_list = cast(List[object], names)
    types_list = cast(List[object], types)
    sizes_list = cast(List[object], sizes)
    constants_list = cast(List[object], constants)
    deps_list = cast(List[object], deps)
    lengths = {key: len(value) for key, value in arrays if isinstance(value, list)}
    if len(set(lengths.values())) != 1:
        out.append(_f("MAT.COMPONENT_LENGTH", "violation", path,
                      "Массивы компонента должны иметь одинаковое число свойств.", lengths,
                      "одинаковые длины", COMPONENT_LINE))
        return
    type_size = data.get("header", {}).get("types", {}) if isinstance(data.get("header"), dict) else {}
    double_size = type_size.get("double", 0) if isinstance(type_size, dict) else 0
    header = data.get("header")
    binary = header.get("binary") if isinstance(header, dict) and isinstance(header.get("binary"), bool) else None
    for index, (name, dep_type, dep_size, value, dep) in enumerate(zip(names_list, types_list, sizes_list, constants_list, deps_list)):
        p = f"{path}.const_names[{index}]"
        if not _is_int(name):
            out.append(_f("MAT.CONST_NAME", "violation", p, "Индекс свойства должен быть целым кодом.",
                          _type_name(name), "int", MATERIAL_LINE))
        elif group in NAME_CODES and name not in NAME_CODES[group]:
            out.append(_f("MAT.CONST_NAME", "ambiguity", p, "Индекс свойства отсутствует в опубликованной таблице группы; спецификация не устанавливает исчерпываемость индексов.",
                          name, sorted(NAME_CODES[group]), MATERIAL_LINE))
        dep_size_num = cast(int, dep_size) if _is_int(dep_size) else -1
        if dep_size_num < 0:
            out.append(_f("MAT.DEP_SIZE", "violation", f"{path}.const_dep_size[{index}]",
                          "Размер таблицы должен быть неотрицательным целым.", dep_size, "целое >= 0", COMPONENT_LINE))
        dep_codes: Sequence[object]
        is_table = isinstance(dep_type, list)
        dep_codes = dep_type if isinstance(dep_type, list) else [dep_type]
        if not is_table and not _is_int(dep_type):
            out.append(_f("MAT.DEP_TYPE", "violation", f"{path}.const_types[{index}]",
                          "Для константы или формулы код зависимости должен быть целым.",
                          _type_name(dep_type), "int", COMPONENT_LINE))
        if not is_table and _is_int(dep_type) and dep_type not in (0, 6):
            out.append(_f("MAT.DEP_TYPE", "violation", f"{path}.const_types[{index}]",
                          "Скалярный dependency-код должен быть CONSTANT или FORMULA; табличные коды требуют списка.",
                          dep_type, [0, 6], COMPONENT_LINE))
        if is_table and not dep_type:
            out.append(_f("MAT.DEP_TYPE", "violation", f"{path}.const_types[{index}]",
                          "Табличный код зависимости не может быть пустым.", [], "массив кодов", COMPONENT_LINE))
        for code in dep_codes:
            if not _is_int(code) or code not in DEPENDENCY_CODES:
                out.append(_f("MAT.DEP_TYPE", "ambiguity", f"{path}.const_types[{index}]",
                              "Код зависимости отсутствует в таблице спецификации.", code,
                              sorted(DEPENDENCY_CODES), MATERIAL_LINE))
        if dep_size_num == 0 and is_table:
            out.append(_f("MAT.DEP_SIZE", "violation", f"{path}.const_dep_size[{index}]",
                          "Табличная зависимость должна содержать число строк больше нуля.", dep_size, "> 0", COMPONENT_LINE))
        if dep_size_num > 0 and not is_table:
            out.append(_f("MAT.DEP_TYPE", "violation", f"{path}.const_types[{index}]",
                          "При ненулевом числе строк код зависимости должен быть массивом.", dep_type, "массив кодов", COMPONENT_LINE))
        formula = dep_type == 6
        if formula and not isinstance(value, str):
            out.append(_f("MAT.VALUE_ENCODING", "violation", f"{path}.constants[{index}]",
                          "Формула должна храниться строкой.", _type_name(value), "string", COMPONENT_LINE))
        elif not formula:
            kind = _value_kind(value, double_size, binary)
            if binary is False and kind == "base64":
                out.append(_f("MAT.VALUE_ENCODING", "ambiguity", f"{path}.constants[{index}]",
                              "Base64 payload при binary=false конфликтует с plain-JSON и компонентной схемой.",
                              kind, "plain numeric array", COMPONENT_LINE))
            if kind not in ("array", "base64", "base64 unknown width"):
                out.append(_f("MAT.VALUE_ENCODING", "violation", f"{path}.constants[{index}]",
                              "Числовое значение должно быть массивом чисел или корректным Base64-буфером.",
                              kind, "array или Base64", COMPONENT_LINE))
        if dep_size_num == 0:
            if not formula and value not in ("", None):
                scalar_length = len(value) if isinstance(value, list) else (_decoded_length(value, double_size) if double_size else None)
                if scalar_length is None and isinstance(value, str):
                    out.append(_f("MAT.TYPE_SIZE", "ambiguity", f"{path}.constants[{index}]",
                                  "Невозможно проверить длину scalar Base64 без header.types.double.",
                                  "missing", "header.types.double", COMPONENT_LINE))
                elif scalar_length is not None and scalar_length != 1:
                    out.append(_f("MAT.VALUE_LENGTH", "violation", f"{path}.constants[{index}]",
                                  "Скалярная числовая константа должна содержать ровно один элемент.", scalar_length, 1, COMPONENT_LINE))
            if dep != "":
                out.append(_f("MAT.DEP_ENCODING", "violation", f"{path}.const_dep[{index}]",
                              "Для константы или формулы аргументная колонка должна быть пустой строкой.",
                              _type_name(dep) if not isinstance(dep, str) else dep, "", COMPONENT_LINE))
        elif dep_size_num > 0:
            if not isinstance(dep, list) or len(dep) != len(dep_codes):
                out.append(_f("MAT.DEP_ENCODING", "violation", f"{path}.const_dep[{index}]",
                              "Табличные аргументы должны быть массивом колонок по числу кодов.",
                              len(dep) if isinstance(dep, list) else _type_name(dep), len(dep_codes), COMPONENT_LINE))
            elif not double_size:
                out.append(_f("MAT.TYPE_SIZE", "ambiguity", f"{path}.const_dep[{index}]",
                              "Невозможно проверить длину аргументного буфера без header.types.double.",
                              "missing", "header.types.double", COMPONENT_LINE))
            else:
                for col, payload in enumerate(dep):
                    decoded = None if binary is True and isinstance(payload, list) else _decoded_length(payload, double_size)
                    if binary is False and _value_kind(payload, double_size, binary) == "base64":
                        out.append(_f("MAT.DEP_ENCODING", "ambiguity", f"{path}.const_dep[{index}][{col}]",
                                      "Base64 argument payload при binary=false конфликтует с plain-JSON схемой.",
                                      "base64", "plain numeric array", COMPONENT_LINE))
                    if decoded is None or decoded != dep_size_num:
                        out.append(_f("MAT.DEP_LENGTH", "violation", f"{path}.const_dep[{index}][{col}]",
                                      "Длина аргументной колонки должна совпадать с числом строк.",
                                      decoded if decoded is not None else _value_kind(payload, double_size, binary), dep_size_num, COMPONENT_LINE))
        if dep_size_num > 0 and not formula and double_size:
            decoded_values = _decoded_length(value, double_size)
            if decoded_values is not None and decoded_values != dep_size_num:
                out.append(_f("MAT.VALUE_LENGTH", "violation", f"{path}.constants[{index}]",
                              "Длина табличного массива значений должна совпадать с числом строк.",
                              decoded_values, dep_size_num, COMPONENT_LINE))
        if is_table and any(code in (0, 6) for code in dep_codes):
            out.append(_f("MAT.DEP_TYPE", "violation", f"{path}.const_types[{index}]",
                          "Табличный список dependency-кодов не может содержать CONSTANT или FORMULA.",
                          list(dep_codes), "только табличные коды", COMPONENT_LINE))


def _audit_materials(data: dict, out: List[Finding]) -> None:
    materials = data.get("materials")
    if materials is None:
        return
    if not isinstance(materials, list):
        out.append(_f("MAT.SECTION_TYPE", "violation", "$.materials", "materials должен быть массивом.",
                      _type_name(materials), "array", MATERIAL_LINE))
        return
    header = data.get("header")
    version = header.get("version") if isinstance(header, dict) else None
    legacy_version = _is_int(version) and cast(int, version) < 3
    known_groups = set(GROUP_TYPES)
    for mi, material in enumerate(materials):
        path = f"$.materials[{mi}]"
        if not isinstance(material, dict):
            out.append(_f("MAT.RECORD_TYPE", "violation", path, "Запись материала должна быть объектом.",
                          _type_name(material), "object", MATERIAL_LINE))
            continue
        for key, expected in (("id", "int"), ("name", "string")):
            if key in material and ((expected == "int" and not _is_int(material[key])) or
                                    (expected == "string" and not isinstance(material[key], str))):
                out.append(_f("MAT.RECORD_FIELD", "violation", f"{path}.{key}",
                              f"Поле материала должно иметь тип {expected}.", _type_name(material[key]), expected, MATERIAL_LINE))
        for key, value in material.items():
            if key in ("id", "name", "constants"):
                continue
            if key not in known_groups:
                out.append(_f("MAT.UNKNOWN_GROUP", "ambiguity", f"{path}.{key}",
                              "Неизвестная группа материала отсутствует в закрытом перечне спецификации.",
                              "unknown", sorted(known_groups), MATERIAL_LINE))
                continue
            if not isinstance(value, list):
                severity = "legacy" if legacy_version else "violation"
                out.append(_f("MAT.GROUP_ARRAY", severity, f"{path}.{key}",
                              "Группа материала должна быть массивом в grouped layout.", _type_name(value), "array", MATERIAL_LINE))
                continue
            if len(value) > 1:
                out.append(_f("MAT.GROUP_CARDINALITY", "violation", f"{path}.{key}",
                              "Группа материала должна содержать ровно один объект.", len(value), "0 или 1", MATERIAL_LINE))
            for ci, component in enumerate(value):
                _audit_component(key, component, f"{path}.{key}[{ci}]", data, out)
        if isinstance(material.get("constants"), dict):
            out.append(_f("MAT.LEGACY_LAYOUT", "legacy", f"{path}.constants",
                          "Материал использует документированный плоский legacy-layout v1/v2.", "object", "v3 grouped layout", "1846"))
        elif "constants" in material:
            out.append(_f("MAT.LEGACY_LAYOUT", "ambiguity", f"{path}.constants",
                          "Поле constants присутствует, но его структура не соответствует описанному legacy-объекту.",
                          _type_name(material["constants"]), "object", "1846"))


def _audit_property_tables(data: dict, out: List[Finding]) -> None:
    tables = data.get("property_tables")
    if tables is None:
        return
    if not isinstance(tables, list):
        out.append(_f("PT.SECTION_TYPE", "violation", "$.property_tables", "property_tables должен быть массивом.",
                      _type_name(tables), "array", PROPERTY_LINE))
        return
    for i, table in enumerate(tables):
        path = f"$.property_tables[{i}]"
        if not isinstance(table, dict):
            out.append(_f("PT.RECORD_TYPE", "violation", path, "Запись property table должна быть объектом.",
                          _type_name(table), "object", PROPERTY_LINE))
            continue
        known_table_fields = {"id", "name", "type", "direction_normal", "thickness_change", "properties", "layers"}
        for key in table:
            if key not in known_table_fields:
                out.append(_f("PT.UNKNOWN_FIELD", "ambiguity", f"{path}.{key}",
                              "Неизвестное поле property table не описано спецификацией.", "unknown",
                              sorted(known_table_fields), PROPERTY_LINE))
        for key in ("id", "type", "direction_normal", "thickness_change"):
            if key not in table:
                continue
            value = table[key]
            good = ((_is_int(value) if key in ("id", "type") else isinstance(value, bool)))
            if not good:
                out.append(_f("PT.FIELD_TYPE", "violation", f"{path}.{key}",
                              "Поле property table имеет неверный тип.", _type_name(value),
                              "int" if key in ("id", "type") else "bool", PROPERTY_LINE))
        if "id" in table and _is_int(table["id"]) and not 0 <= table["id"] <= 65535:
            out.append(_f("PT.ID_RANGE", "violation", f"{path}.id", "ID property table должен помещаться в unsigned short.",
                          table["id"], "0..65535", PROPERTY_LINE))
        ptype = table.get("type")
        if _is_int(ptype) and ptype not in PROPERTY_TYPES:
            severity = "ambiguity"
            out.append(_f("PT.TYPE", severity, f"{path}.type", "Код property table отсутствует в актуальной таблице; -1 встречается как legacy section-properties layout.",
                          ptype, sorted(PROPERTY_TYPES), PROPERTY_LINE))
        props = table.get("properties")
        section: object = None
        if "properties" in table and not isinstance(props, dict):
            out.append(_f("PT.PROPERTIES_TYPE", "violation", f"{path}.properties",
                          "properties должен быть объектом.", _type_name(props), "object", PROPERTY_LINE))
        if isinstance(props, dict):
            section = props.get("section_type")
            common_property_fields = {"geometry", "section_type", "spring_type", "e", "mass", "mass_x", "mass_y", "mass_z", "mass_inertia", "mass_inertia_x", "mass_inertia_y", "mass_inertia_z", "stiffness", "spring_constant_damping", "spring_linear_damping", "spring_mass", "stiffness_torsional", "spring_constant_damping_torsional", "spring_linear_damping_torsional", "spring_inertia", "k1", "k2", "gap", "limit_sliding_force", "damping", "mass_distribution", "angle", "ey", "ez", "mesh_quality", "warping_dof", "imported_section_id", "area", "A", "Ix", "Ip", "Iy", "Iz", "Iyz", "It", "Iw", "max_y", "max_z", "shear_coefficient_yy", "shear_coefficient_zz", "shear_coefficient_zy", "shear_center_y", "shear_center_z"}
            for key in props:
                if key not in common_property_fields:
                    out.append(_f("PT.UNKNOWN_FIELD", "ambiguity", f"{path}.properties.{key}",
                                  "Неизвестное поле properties не описано спецификацией.", "unknown",
                                  sorted(common_property_fields), PROPERTY_LINE))
            numeric_fields = {
                "e", "mass", "mass_x", "mass_y", "mass_z", "mass_inertia", "mass_inertia_x",
                "mass_inertia_y", "mass_inertia_z", "stiffness", "spring_constant_damping",
                "spring_linear_damping", "spring_mass", "stiffness_torsional",
                "spring_constant_damping_torsional", "spring_linear_damping_torsional", "spring_inertia",
                "k1", "k2", "gap", "limit_sliding_force", "damping", "mass_distribution",
                "angle", "ey", "ez", "mesh_quality", "warping_dof", "imported_section_id", "area", "A",
                "Ix", "Ip", "Iy", "Iz", "Iyz", "It", "Iw", "max_y", "max_z",
                "shear_coefficient_yy", "shear_coefficient_zz", "shear_coefficient_zy",
                "shear_center_y", "shear_center_z",
            }
            integer_fields = {"mass_distribution", "mesh_quality", "warping_dof", "imported_section_id"}
            for key in numeric_fields:
                if key in props:
                    value = props[key]
                    good = _is_int(value) if key in integer_fields else _is_number(value)
                    if not good:
                        out.append(_f("PT.PROPERTY_FIELD", "violation", f"{path}.properties.{key}",
                                      "Числовое поле properties имеет неверный тип.", _type_name(value),
                                      "int" if key in integer_fields else "number", PROPERTY_LINE))
            if "spring_type" in props:
                spring_type = props["spring_type"]
                if not isinstance(spring_type, str) or spring_type not in {"linear_spring", "combined_spring"}:
                    out.append(_f("PT.SPRING_TYPE", "violation", f"{path}.properties.spring_type",
                                  "Тип пружины должен быть одним из документированных строковых кодов.", spring_type,
                                  ["linear_spring", "combined_spring"], PROPERTY_LINE))
            if _is_int(ptype) and ptype == 5:
                if "mass" in props and any(key in props for key in {"mass_x", "mass_y", "mass_z"}):
                    out.append(_f("PT.MASS_EXCLUSIVE", "violation", f"{path}.properties",
                                  "mass взаимоисключается с mass_x/mass_y/mass_z.", "both forms", "одна форма", PROPERTY_LINE))
                if "mass_inertia" in props and any(key in props for key in {"mass_inertia_x", "mass_inertia_y", "mass_inertia_z"}):
                    out.append(_f("PT.MASS_EXCLUSIVE", "violation", f"{path}.properties",
                                  "mass_inertia взаимоисключается с per-axis inertia.", "both forms", "одна форма", PROPERTY_LINE))
                if "mass_distribution" in props and (not _is_int(props["mass_distribution"]) or props["mass_distribution"] not in {-1, 0, 1}):
                    out.append(_f("PT.MASS_DISTRIBUTION", "violation", f"{path}.properties.mass_distribution",
                                  "mass_distribution должен быть -1, 0 или 1.", props["mass_distribution"], [-1, 0, 1], PROPERTY_LINE))
            geometry = props.get("geometry")
            if geometry is not None:
                if not isinstance(geometry, dict):
                    out.append(_f("PT.GEOMETRY_TYPE", "violation", f"{path}.properties.geometry",
                                  "geometry должен быть объектом.", _type_name(geometry), "object", "946"))
                else:
                    section_geometry_fields = {
                        0: {"B", "H"}, 1: {"a", "b"}, 2: {"B1", "B2", "H", "c1", "c2", "d"},
                        3: {"D1", "D2", "e"}, 5: {"H", "B1", "B2", "c1", "c2", "d"},
                        6: {"H", "B", "d", "c1"}, 7: {"H", "B1", "B2", "c1", "c2", "d"},
                        8: {"H", "B", "d", "c1"}, 9: {"H", "B", "d1", "d2", "c1", "c2"},
                        10: {"H", "B3", "B1", "B2", "d1", "d2", "c3", "c1", "c2"},
                        12: {"d1", "d2", "p1", "p2"},
                    }
                    allowed_geometry = section_geometry_fields.get(cast(int, section), set()) if _is_int(section) else set()
                    for key, value in geometry.items():
                        if key not in allowed_geometry:
                            out.append(_f("PT.UNKNOWN_FIELD", "ambiguity", f"{path}.properties.geometry.{key}",
                                          "Поле geometry не описано для данного section_type.", "unknown",
                                          sorted(allowed_geometry), "946"))
                        if not _is_number(value):
                            out.append(_f("PT.GEOMETRY_FIELD", "violation", f"{path}.properties.geometry.{key}",
                                          "Значение geometry должно быть числом.", _type_name(value), "number", "946"))
        if _is_int(ptype) and ptype == 1 and isinstance(props, dict):
            if "section_type" in props and (not _is_int(section) or section not in SECTION_TYPES):
                out.append(_f("PT.SECTION_TYPE", "ambiguity", f"{path}.properties.section_type",
                              "Код сечения BEAM отсутствует в таблице section_type.", section,
                              sorted(SECTION_TYPES), PROPERTY_LINE))
        layers = table.get("layers")
        if "layers" in table:
            if not isinstance(layers, list):
                out.append(_f("PT.LAYERS_TYPE", "violation", f"{path}.layers", "layers должен быть массивом в grouped layout.",
                              _type_name(layers), "array", PROPERTY_LINE))
            else:
                if _is_int(ptype) and ptype != 0 and layers:
                    out.append(_f("PT.LAYERS_CONTEXT", "violation", f"{path}.layers",
                                  "Слои описаны только для SHELL property table.", ptype, 0, PROPERTY_LINE))
                for li, layer in enumerate(layers):
                    lp = f"{path}.layers[{li}]"
                    if not isinstance(layer, dict):
                        out.append(_f("PT.LAYER_TYPE", "violation", lp, "Слой должен быть объектом.",
                                      _type_name(layer), "object", PROPERTY_LINE))
                        continue
                    for key in layer:
                        if key not in {"t", "angle", "material_id"}:
                            out.append(_f("PT.UNKNOWN_FIELD", "ambiguity", f"{lp}.{key}",
                                          "Неизвестное поле слоя не описано спецификацией.", "unknown",
                                          ["t", "angle", "material_id"], PROPERTY_LINE))
                    for key, expected in (("t", "number"), ("angle", "number"), ("material_id", "int")):
                        if key in layer:
                            value = layer[key]
                            good = _is_number(value) if expected == "number" else _is_int(value)
                            if not good:
                                out.append(_f("PT.LAYER_FIELD", "violation", f"{lp}.{key}",
                                              "Поле слоя имеет неверный тип.", _type_name(value), expected, PROPERTY_LINE))


def audit(data: dict) -> List[Finding]:
    """Return JSON-compatible findings for materials and property tables."""
    out: List[Finding] = []
    if not isinstance(data, dict):
        return [_f("MAT.INPUT_TYPE", "violation", "$", "Корень файла должен быть объектом.",
                    _type_name(data), "object", MATERIAL_LINE)]
    _audit_materials(data, out)
    _audit_property_tables(data, out)
    return out
