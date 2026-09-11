"""Independent structural audit for condition and output sections."""
from __future__ import annotations

import base64
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, cast

Finding = Dict[str, object]

LOADS = {
    1: 1, 2: 1, 3: 1, 4: 1, 5: 6, 6: 3, 11: 1, 12: 1, 13: 2,
    14: 2, 15: 2, 16: 2, 17: 1, 18: 1, 19: 0, 20: 0, 21: 2,
    22: 1, 23: 1, 24: 4, 25: 2, 26: 2, 28: 1, 29: 2, 30: 2,
    31: 6, 32: 6, 33: 6, 34: 6, 35: 6, 36: 6, 37: 6, 38: 6,
    39: 1, 40: 1, 41: 1, 42: 1, 43: 1, 44: 3, 45: 0, 46: 0,
    47: 6, 48: 6, 49: 6,
}
LOAD_PAIRS = {1, 2, 3, 4, 11, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23, 24, 25, 26, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 45, 46}
RESTRAINTS = {0: None, 1: 6, 2: 6, 3: 1, 4: 2, 5: 2, 6: (1, 2), 7: (1, 2), 9: 6, 10: 1, 12: 1, 13: 1, 14: 1, 15: 3}
INITIAL = {0: 6, 1: 6, 2: 3, 3: 1, 4: 1}
COUPLING = set(range(7))
PERIODIC = set(range(6))
RECEIVERS = set(range(5))
CONTACT_TYPES = {"general", "tied", "tied_normal", "tied_tangent"}
CONTACT_METHODS = {"auto", "penalty", "mpc", "pure_lagrangian", "aug_lagrangian"}
DOFS = {"UX", "UY", "UZ", "RX", "RY", "RZ"}


def _f(rule: str, severity: str, path: str, message: str, actual: object,
       expected: object, line: int) -> Finding:
    return {"rule": rule, "severity": severity, "path": path, "message": message,
            "actual": actual, "expected": expected,
            "spec": "docs/FC_INPUT_FORMAT.md:%d" % line}


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _scalar_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all((_is_int(x) or isinstance(x, float)) if not isinstance(x, list) else _scalar_list(x) for x in value)


def _b64_count(value: object, width: int) -> Optional[int]:
    if not isinstance(value, str) or value == "":
        return 0 if value == "" else None
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception:
        return None
    return len(raw) // width if width and len(raw) % width == 0 else None


def _enum(out: List[Finding], path: str, value: object, allowed: Iterable[object], rule: str, line: int) -> None:
    if value not in allowed:
        out.append(_f(rule, "ambiguity", path, "Документ не определяет такой код/значение.", value, sorted(list(allowed), key=repr), line))


def _common(out: List[Finding], x: dict, path: str, line: int) -> None:
    for key, typ in (("id", int), ("apply_to_size", int), ("master_size", int), ("slave_size", int), ("cs", int)):
        if key in x and not (_is_int(x[key]) if typ is int else isinstance(x[key], typ)):
            out.append(_f("COND.TYPE", "violation", path + "." + key, "Поле имеет недопустимый тип.", x[key], "int", line))
    if "name" in x and not isinstance(x["name"], str):
        out.append(_f("COND.TYPE", "violation", path + ".name", "Имя должно быть строкой.", x["name"], "string", line))


def _payload(out: List[Finding], x: dict, path: str, key: str, size: Optional[int], binary: bool, width: Optional[int], line: int, allow_all: bool = False, allow_pairs: bool = False, stride: int = 1) -> None:
    if key not in x:
        return
    value = x[key]
    if size is not None:
        size *= stride
    if allow_all and value == "all":
        return
    if binary:
        if not isinstance(value, str):
            out.append(_f("COND.PAYLOAD", "violation", path + "." + key, "В binary-режиме payload должен быть Base64-строкой.", value, "Base64 string", line)); return
        if width is None or width <= 0:
            out.append(_f("COND.WIDTH_CONTEXT", "ambiguity", path + "." + key, "Размер бинарного типа не задан; длина payload не проверена.", None, "header.types", line))
            return
        count = _b64_count(value, width)
        if count is None:
            out.append(_f("COND.BASE64", "violation", path + "." + key, "Некорректный Base64 payload или размер не кратен header.types.", "invalid", "valid Base64", line))
        elif size is not None and count != size and not (allow_pairs and count == size * 2):
            out.append(_f("COND.SIZE", "violation", path + "." + key, "Размер payload не совпадает с полем размера.", count, (size, size * 2) if allow_pairs else size, line))
    elif not _scalar_list(value):
        out.append(_f("COND.PAYLOAD", "violation", path + "." + key, "В plain JSON payload должен быть числовым массивом.", value, "number[]", line))
    elif size is not None and len(cast(List[object], value)) != size and not (allow_pairs and len(cast(List[object], value)) == size * 2):
        out.append(_f("COND.SIZE", "violation", path + "." + key, "Размер payload не совпадает с полем размера.", len(cast(List[object], value)), (size, size * 2) if allow_pairs else size, line))


def _dependencies(out: List[Finding], x: dict, path: str, line: int, binary: bool, width: Optional[int], double_width: Optional[int]) -> None:
    dep = x.get("dependency_type")
    if dep is None:
        if x.get("data"):
            out.append(_f("COND.DEP_CONTEXT", "ambiguity", path + ".dependency_type", "Для интерпретации data не задано описание зависимостей.", "missing", "dependency_type", 1822))
        return
    if not isinstance(dep, list):
        out.append(_f("COND.DEP_TYPE", "violation", path + ".dependency_type", "dependency_type должен быть массивом компонентов.", type(dep).__name__, "array", 1822))
        return
    fields = {}
    for key in ("data", "dep_var_num", "dep_var_size"):
        value = x.get(key)
        if key not in x:
            out.append(_f("COND.DEP_CONTEXT", "ambiguity", path + "." + key, "Не задано поле для однозначной интерпретации компонента.", "missing", key, 1830))
        elif not isinstance(value, list):
            out.append(_f("COND.COMPONENTS", "violation", path + "." + key, "Компонентная структура должна быть массивом.", type(value).__name__, "array", 1830))
        else:
            fields[key] = value
            if len(value) != len(dep):
                out.append(_f("COND.ALIGN", "violation", path + "." + key, "Число компонентов не совпадает с dependency_type.", len(value), len(dep), 1830))
    for i, code in enumerate(dep):
        cp = path + ".dependency_type[%d]" % i
        table = isinstance(code, list)
        codes = code if table else [code]
        if table and not code:
            out.append(_f("COND.TABLE_CODES", "violation", cp, "Таблица должна иметь хотя бы одну колонку зависимости.", [], "непустой массив кодов", 1829))
        for c in codes:
            if c == "" and not table:
                continue
            if not _is_int(c):
                out.append(_f("COND.DEP_CODE", "violation", cp, "Код зависимости должен быть целым.", c, "int", 1829))
            elif c not in {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12}:
                out.append(_f("COND.DEP_CODE", "ambiguity", cp, "Код зависимости не описан.", c, "0..8,10..12", 536))
            elif (table and c in (0, 6)) or (not table and c not in (0, 6)):
                out.append(_f("COND.DEP_LAYOUT", "violation", cp, "Для TABLE нужен массив табличных кодов; CONSTANT/FORMULA используют скаляр 0/6.", code, "0, 6 или массив табличных кодов", 1828))
        rows_list = fields.get("dep_var_size", [])
        rows = rows_list[i] if i < len(rows_list) else None
        if rows is not None and (not _is_int(rows) or rows < 0):
            out.append(_f("COND.ROWS_TYPE", "violation", path + ".dep_var_size[%d]" % i, "Число строк должно быть неотрицательным целым.", rows, "int >= 0", 1834))
        if not table and code in (0, 6) and rows not in (None, 0):
            out.append(_f("COND.CONST_ROWS", "violation", path + ".dep_var_size[%d]" % i, "Для CONSTANT/FORMULA число строк равно нулю.", rows, 0, 1828))
        args_list = fields.get("dep_var_num", [])
        args = args_list[i] if i < len(args_list) else None
        if not table and code in (0, 6) and i < len(args_list) and args != "":
            out.append(_f("COND.CONST_DEP", "violation", path + ".dep_var_num[%d]" % i, "Для CONSTANT/FORMULA ожидается пустая строка аргументов.", type(args).__name__, "empty string", 1828))
        values = fields.get("data", [])
        if i >= len(values) or code == "":
            continue
        value = values[i]
        vp = path + ".data[%d]" % i
        if not table and code == 6:
            if not isinstance(value, str):
                out.append(_f("COND.FORMULA", "violation", vp, "Формула должна быть строкой.", type(value).__name__, "string", 1826))
            continue
        if table:
            if not isinstance(args, list) or len(args) != len(codes):
                out.append(_f("COND.TABLE_COLUMNS", "violation", path + ".dep_var_num[%d]" % i, "Число колонок аргументов не совпадает с dependency_type.", len(args) if isinstance(args, list) else type(args).__name__, len(codes), 1829))
            payloads = [(vp, value)] + ([(path + ".dep_var_num[%d][%d]" % (i, j), v) for j, v in enumerate(args)] if isinstance(args, list) else [])
        else:
            payloads = [(vp, value)]
        for pp, payload in payloads:
            if binary:
                if double_width is None or double_width <= 0:
                    continue  # The missing binary context is reported by audit().
                count = _b64_count(payload, double_width)
                if count is None:
                    out.append(_f("COND.NUMERIC_PAYLOAD", "violation", pp, "Числовой компонент не является корректным Base64-буфером ожидаемого типа.", type(payload).__name__, "Base64 double[]", 1826))
                    continue
            elif isinstance(payload, list) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in payload):
                count = len(payload)
            elif payload == "":
                count = 0
            elif isinstance(payload, str):
                out.append(_f("COND.PLAIN_ENCODING", "ambiguity", pp, "binary=false задаёт JSON-массивы, а компонентная схема отдельно описывает Base64; найден строковый числовой payload.", "string", "Уточнение правил binary=false для компонентов", 1822))
                continue
            else:
                out.append(_f("COND.NUMERIC_PAYLOAD", "violation", pp, "Числовой компонент должен содержать числовой массив.", type(payload).__name__, "number[]", 1826))
                continue
            if table and _is_int(rows) and count != rows:
                out.append(_f("COND.TABLE_ROWS", "violation", pp, "Длина табличного буфера не совпадает с dep_var_size.", count, rows, 1829))
            elif not table and code == 0 and count not in (0, 1):
                out.append(_f("COND.CONSTANT_SIZE", "violation", pp, "Скалярная константа содержит несколько значений.", count, "0 или 1 (пустой компонент разрешён)", 1826))


def _unknown(out: List[Finding], x: dict, path: str, allowed: Sequence[str]) -> None:
    for key in x:
        if key not in allowed:
            out.append(_f("COND.UNKNOWN_KEY", "ambiguity", path + "." + key, "Вложенное поле не описано для этой секции спецификацией.", key, "documented field", 1812))


def _section(data: dict, name: str, out: List[Finding]) -> List[Tuple[int, dict]]:
    raw = data.get(name)
    if raw is None:
        return []
    if not isinstance(raw, list):
        out.append(_f("COND.SECTION", "violation", "$." + name, "Секция должна быть массивом записей.", raw, "array", 1031)); return []
    result: List[Tuple[int, dict]] = []
    for i, item in enumerate(raw):
        if isinstance(item, dict): result.append((i, item))
        else: out.append(_f("COND.RECORD", "violation", "$.%s[%d]" % (name, i), "Запись секции должна быть объектом.", item, "object", 1031))
    return result


def _present_types(data: dict, out: List[Finding]) -> None:
    """Validate all remaining literal field types, including nested records."""
    from audit_document import matches

    def fields(record: dict, path: str, mapping: Dict[str, str], line: int, unknown: bool = False) -> None:
        for key, value in record.items():
            if key not in mapping:
                if unknown:
                    out.append(_f("COND.NESTED_UNKNOWN", "ambiguity", path + "." + key, "Вложенное поле не описано в схеме.", key, "documented field", line))
                continue
            if not matches(value, mapping[key]):
                out.append(_f("COND.FIELD_TYPE", "violation", path + "." + key, "Тип или длина поля расходится с указанным в схеме.", {"type": type(value).__name__, "length": len(value) if isinstance(value, (list, dict, str)) else None}, mapping[key], line))

    common = {"step": "[int]", "case": "[int]"}
    contact = {k: "double" for k in "friction tolerance offset preload distance min_angle detection_tolerance search_radius max_overlap normal_stiffness tangent_stiffness thermo_penalty_mult gap_tension thermo_penalty_relax".split()}
    contact.update({k: "bool" for k in "ignoreoverlap ignore_overlap ignore_tied_stiffness".split()})
    contact.update({"type": "string", "method": "string", "gap_gas_material": "int", "gap_gas_fractions": "object", "lagrange_settings": "object"})
    lagrange = {k: "double" for k in "tangent_rate criteria_smoothing stability_normal stability_tangent shear_stress_limit tensile_stress_limit direction_tolerance augmented_tolerance".split()}
    lagrange.update({k: "bool" for k in "use_tangent use_stick_predictor overconstraint_normal overconstraint_tangent".split()})
    for section in ("loads", "restraints", "initial_sets", "coupling_constraints", "contact_constraints", "periodic_constraints", "receivers"):
        values = data.get(section)
        if not isinstance(values, list):
            continue
        for index, record in enumerate(values):
            if not isinstance(record, dict):
                continue
            path = "$.%s[%d]" % (section, index)
            mapping = dict(common)
            if section in ("loads", "initial_sets", "coupling_constraints", "periodic_constraints", "receivers"):
                mapping["type"] = "int"
            if section == "initial_sets":
                mapping["flag"] = "[int]"
                flags = record.get("flag")
                if isinstance(flags, list):
                    if any(v not in (0, 1) or isinstance(v, bool) for v in flags):
                        out.append(_f("INITIAL.FLAG_VALUES", "violation", path + ".flag", "Активность начального условия кодируется 0 или 1.", flags, "0/1 flags", 1197))
                    if isinstance(record.get("data"), list) and len(record["data"]) != len(flags):
                        out.append(_f("INITIAL.DATA_FLAG", "violation", path + ".data", "Число data компонентов не совпадает с flag.", len(record["data"]), len(flags), 1832))
            if section == "contact_constraints":
                mapping.update(contact)
                nested = record.get("lagrange_settings")
                if isinstance(nested, dict):
                    fields(nested, path + ".lagrange_settings", lagrange, 1390, True)
                gas = record.get("gap_gas_fractions")
                if isinstance(gas, dict):
                    fields(gas, path + ".gap_gas_fractions", {"helium": "double", "krypton": "double", "xenon": "double", "caesium": "double", "user_defined": "[double]"}, 1374, True)
            if section == "coupling_constraints":
                mapping.update({"coordinate_system_id": "int", "dofs": "[int]", "master_dofs": "[int]", "slave_dofs": "[int]", "direction": "[double, double, double]", "distance_weighting": "bool", "factor": "double", "equation": "object", "enforcement_method": "string"})
                mapping["stiffness"] = "double" if record.get("type") == 4 else "[double]"
                mapping["damping"] = "[double]"
                for key in ("dofs", "master_dofs", "slave_dofs"):
                    value = record.get(key)
                    if isinstance(value, list) and len(value) != 6:
                        out.append(_f("COUPLING.DOFS_SIZE", "violation", path + "." + key, "Схема требует 6 компонент DOF.", len(value), 6, 1257))
                equation = record.get("equation")
                if isinstance(equation, dict):
                    fields(equation, path + ".equation", {"rhs": "double"}, 1298)
                    for key in equation:
                        if key not in ("rhs", "terms"):
                            out.append(_f("COND.NESTED_UNKNOWN", "ambiguity", path + ".equation." + key, "Поле уравнения не описано.", key, "rhs/terms", 1298))
                    terms = equation.get("terms")
                    if "terms" in equation and not isinstance(terms, list):
                        out.append(_f("COUPLING.TERMS", "violation", path + ".equation.terms", "terms должен быть массивом объектов.", type(terms).__name__, "array", 1298))
                    elif isinstance(terms, list):
                        for j, term in enumerate(terms):
                            tp = path + ".equation.terms[%d]" % j
                            if isinstance(term, dict):
                                fields(term, tp, {"node": "int", "dof": "string", "coefficient": "double", "coef": "double"}, 1298, True)
                            else:
                                out.append(_f("COUPLING.TERMS", "violation", tp, "Член уравнения должен быть объектом.", type(term).__name__, "object", 1298))
            if section == "periodic_constraints":
                mapping["sectors"] = "int"
            if section == "receivers":
                mapping.update({"dofs": "[int, int, int]", "output_step": "int"})
            fields(record, path, mapping, {"loads": 1031, "restraints": 1143, "initial_sets": 1188, "coupling_constraints": 1225, "contact_constraints": 1315, "periodic_constraints": 1411, "receivers": 1441}[section])


def audit(data: dict) -> List[Finding]:
    out: List[Finding] = []
    _present_types(data, out)
    header = data.get("header")
    binary = bool(isinstance(header, dict) and header.get("binary", False))
    types = header.get("types", {}) if isinstance(header, dict) else {}
    width = types.get("int") if isinstance(types, dict) and _is_int(types.get("int")) else None
    double_width = types.get("double") if isinstance(types, dict) and _is_int(types.get("double")) else None
    if binary and width is None:
        out.append(_f("COND.WIDTH_CONTEXT", "ambiguity", "$.header.types.int", "Для binary payload отсутствует размер int в header.types.", "missing", "header.types.int", 1812))
    if binary and double_width is None:
        out.append(_f("COND.WIDTH_CONTEXT", "ambiguity", "$.header.types.double", "Для binary component payload отсутствует размер double в header.types.", "missing", "header.types.double", 1812))
    for i, x in _section(data, "loads", out):
        p = "$.loads[%d]" % i; _common(out, x, p, 1033); t = x.get("type")
        _unknown(out, x, p, ("id", "name", "type", "apply_to_size", "apply_to", "dependency_type", "dep_var_size", "dep_var_num", "data", "step", "case", "cs"))
        if not _is_int(t): out.append(_f("LOAD.TYPE", "violation", p + ".type", "Тип нагрузки должен быть целым кодом.", t, "int", 1067)); continue
        _enum(out, p + ".type", t, LOADS, "LOAD.TYPE_CODE", 1067)
        _payload(out, x, p, "apply_to", x.get("apply_to_size") if _is_int(x.get("apply_to_size")) else None,
                 binary, double_width if t in (47, 48, 49) else width, 1056,
                 t not in (47, 48, 49), False, 3 if t in (47, 48, 49) else 2 if t in LOAD_PAIRS else 1)
        _dependencies(out, x, p, 1812, binary, width, double_width)
        if t in LOADS and isinstance(x.get("data"), list) and len(x["data"]) not in (0, LOADS[t]):
            out.append(_f("LOAD.COMPONENT_COUNT", "violation", p + ".data", "Число компонент data не соответствует типу нагрузки.", len(x["data"]), LOADS[t], 1069))
    for i, x in _section(data, "restraints", out):
        p = "$.restraints[%d]" % i; _common(out, x, p, 1143); flags = x.get("flag")
        _unknown(out, x, p, ("id", "name", "flag", "apply_to_size", "apply_to", "dependency_type", "dep_var_size", "dep_var_num", "data", "step", "case", "cs", "campbell", "campbell_axis"))
        if not isinstance(flags, list) or not all(_is_int(v) for v in flags): out.append(_f("RESTRAINT.FLAG_TYPE", "violation", p + ".flag", "flag должен быть массивом целых кодов.", flags, "int[]", 1169))
        else:
            lengths = {RESTRAINTS.get(v) for v in flags if v in RESTRAINTS and v != 0}
            unknown = [v for v in flags if v not in RESTRAINTS]
            if unknown: out.append(_f("RESTRAINT.FLAG_CODE", "ambiguity", p + ".flag", "Код flag не определён таблицей спецификации.", unknown, sorted(RESTRAINTS), 1169))
            if len(lengths) == 1:
                expected = next(iter(lengths)); expected_values = expected if isinstance(expected, tuple) else (expected,)
                if len(flags) not in expected_values: out.append(_f("RESTRAINT.FLAG_SIZE", "violation", p + ".flag", "Длина flag не соответствует числу DOF данного типа.", len(flags), expected_values, 1166))
        _payload(out, x, p, "apply_to", x.get("apply_to_size") if _is_int(x.get("apply_to_size")) else None, binary, width, 1149, True, any(v in (12, 13, 14) for v in flags) if isinstance(flags, list) else False); _dependencies(out, x, p, 1812, binary, width, double_width)
    for i, x in _section(data, "initial_sets", out):
        p = "$.initial_sets[%d]" % i; _common(out, x, p, 1190); t = x.get("type"); _enum(out, p + ".type", t, INITIAL, "INITIAL.TYPE_CODE", 1225)
        _unknown(out, x, p, ("id", "name", "type", "flag", "apply_to_size", "apply_to", "dependency_type", "dep_var_size", "dep_var_num", "data", "cs"))
        flags = x.get("flag")
        if isinstance(flags, list) and _is_int(t) and t in INITIAL and len(flags) != INITIAL[t]: out.append(_f("INITIAL.FLAG_SIZE", "violation", p + ".flag", "Длина flag не соответствует типу initial set.", len(flags), INITIAL[t], 1213))
        _payload(out, x, p, "apply_to", x.get("apply_to_size") if _is_int(x.get("apply_to_size")) else None, binary, width, 1196, True); _dependencies(out, x, p, 1812, binary, width, double_width)
    for i, x in _section(data, "coupling_constraints", out):
        p = "$.coupling_constraints[%d]" % i; _common(out, x, p, 1233); t=x.get("type"); _enum(out,p+".type",t,COUPLING,"COUPLING.TYPE_CODE",1245)
        _unknown(out, x, p, ("id", "name", "type", "master_size", "master", "slave_size", "slave", "step", "case", "cs", "coordinate_system_id", "dofs", "stiffness", "damping", "direction", "master_dofs", "slave_dofs", "distance_weighting", "factor", "equation", "enforcement_method"))
        _payload(out,x,p,"master",x.get("master_size") if _is_int(x.get("master_size")) else None,binary,width,1233); _payload(out,x,p,"slave",x.get("slave_size") if _is_int(x.get("slave_size")) else None,binary,width,1233)
        if "coordinate_system_id" in x and "cs" not in x: out.append(_f("COUPLING.CS_ALIAS", "legacy", p + ".coordinate_system_id", "Использована документированная совместимая альтернатива cs.", "present", "cs", 1992))
        if t == 4 and (not isinstance(x.get("direction"), list) or len(x["direction"]) != 3): out.append(_f("COUPLING.DIRECTION", "violation", p + ".direction", "Для DIRECTION требуется трёхкомпонентный вектор.", x.get("direction"), "[double,double,double]", 1290))
        if t == 6:
            eq=x.get("equation"); terms=eq.get("terms") if isinstance(eq,dict) else None
            if terms is not None and isinstance(terms,list):
                for j,term in enumerate(terms):
                    if isinstance(term,dict) and term.get("dof") not in DOFS: out.append(_f("COUPLING.DOF", "violation", "%s.equation.terms[%d].dof"%(p,j), "Неизвестное имя DOF уравнения.", term.get("dof"), sorted(DOFS), 1303))
        _enum(out,p+".enforcement_method",x.get("enforcement_method"),{"elimination","penalty"},"COUPLING.ENFORCEMENT",1310) if "enforcement_method" in x else None
        if x.get("enforcement_method") == "penalty" and "stiffness" not in x:
            out.append(_f("COUPLING.PENALTY_FIELDS", "violation", p, "Для penalty требуется stiffness.", "missing", "stiffness", 1310))
    for i,x in _section(data,"contact_constraints",out):
        p="$.contact_constraints[%d]"%i; _common(out,x,p,1324); _enum(out,p+".type",x.get("type"),CONTACT_TYPES,"CONTACT.TYPE",1360); _enum(out,p+".method",x.get("method"),CONTACT_METHODS,"CONTACT.METHOD",1360)
        _unknown(out, x, p, ("id", "name", "type", "method", "step", "master_size", "master", "slave_size", "slave", "friction", "tolerance", "offset", "preload", "ignoreoverlap", "ignore_overlap", "distance", "min_angle", "detection_tolerance", "search_radius", "max_overlap", "normal_stiffness", "tangent_stiffness", "thermo_penalty_mult", "gap_tension", "ignore_tied_stiffness", "thermo_penalty_relax", "gap_gas_material", "gap_gas_fractions", "lagrange_settings"))
        for k,cond,exp in (("friction",lambda v:isinstance(v,(int,float)) and not isinstance(v,bool) and v>=0,">= 0"),("gap_tension",lambda v:isinstance(v,(int,float)) and not isinstance(v,bool) and v>=0,">= 0"),("search_radius",lambda v:isinstance(v,(int,float)) and not isinstance(v,bool) and v>0,"> 0"),("normal_stiffness",lambda v:isinstance(v,(int,float)) and not isinstance(v,bool) and v>0,"> 0")):
            if k in x and not cond(x[k]): out.append(_f("CONTACT.VALUE", "violation", p+"."+k, "Числовое значение не удовлетворяет ограничению спецификации.", x[k], exp, 1367))
        for k in ("ignore_overlap","ignoreoverlap"):
            if k in x and not isinstance(x[k],bool): out.append(_f("CONTACT.BOOL", "violation", p+"."+k, "Флаг должен быть bool.", x[k], "bool", 1332))
        if x.get("method") == "penalty":
            for required in ("normal_stiffness", "tangent_stiffness"):
                if required not in x:
                    out.append(_f("CONTACT.PENALTY_FIELDS", "violation", p, "Для метода penalty требуется поле penalty stiffness.", "missing", required, 2158))
            if "damping" not in x:
                out.append(_f("CONTACT.PENALTY_DAMPING", "ambiguity", p, "Правило penalty требует damping, но поле отсутствует в основной схеме contact_constraints.", "missing", "damping", 2158))
        if x.get("method") in ("pure_lagrangian", "aug_lagrangian") and "lagrange_settings" not in x:
            out.append(_f("CONTACT.LAGRANGE_FIELDS", "violation", p, "Для Lagrangian метода требуется lagrange_settings.", "missing", "lagrange_settings", 1390))
        if isinstance(x.get("gap_gas_fractions"),dict):
            u=x["gap_gas_fractions"].get("user_defined")
            if u is not None and (not isinstance(u,list) or len(u)%4): out.append(_f("CONTACT.GAS_STRIDE", "violation", p+".gap_gas_fractions.user_defined", "user_defined должен иметь длину, кратную 4.", len(u) if isinstance(u,list) else u, "multiple of 4", 1380))
        _payload(out,x,p,"master",x.get("master_size") if _is_int(x.get("master_size")) else None,binary,width,1324,False,True); _payload(out,x,p,"slave",x.get("slave_size") if _is_int(x.get("slave_size")) else None,binary,width,1324,False,True)
    for i,x in _section(data,"periodic_constraints",out):
        p="$.periodic_constraints[%d]"%i; _common(out,x,p,1414); _enum(out,p+".type",x.get("type"),PERIODIC,"PERIODIC.TYPE_CODE",1430); _payload(out,x,p,"master",x.get("master_size") if _is_int(x.get("master_size")) else None,binary,width,1414,False,False,2); _payload(out,x,p,"slave",x.get("slave_size") if _is_int(x.get("slave_size")) else None,binary,width,1414,False,False,2)
        _unknown(out, x, p, ("id", "name", "cs", "step", "type", "sectors", "master_size", "master", "slave_size", "slave"))
    for i,x in _section(data,"receivers",out):
        p="$.receivers[%d]"%i; _common(out,x,p,1448); _enum(out,p+".type",x.get("type"),RECEIVERS,"RECEIVER.TYPE_CODE",1457); _payload(out,x,p,"apply_to",x.get("apply_to_size") if _is_int(x.get("apply_to_size")) else None,binary,width,1448)
        _unknown(out, x, p, ("id", "name", "type", "apply_to_size", "apply_to", "dofs", "output_step"))
        if x.get("type") != 3 and "dofs" in x and (not isinstance(x["dofs"],list) or len(x["dofs"]) != 3): out.append(_f("RECEIVER.DOFS", "violation", p+".dofs", "dofs должен иметь три флага для этого типа receiver.", x.get("dofs"), "int[3]", 1448))
    return out
