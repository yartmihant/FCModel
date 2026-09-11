"""Literal document-derived structural and settings checks, independent of FCModel."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple, Sequence

SPEC = Path(__file__).resolve().parents[2] / "docs/FC_INPUT_FORMAT.md"
Finding = Dict[str, object]


def schema_from_document() -> Dict[str, Dict[str, Tuple[str, int]]]:
    """Extract typed fields from the document's header/settings example blocks."""
    schemas: Dict[str, Dict[str, Tuple[str, int]]] = {}
    section = ""
    in_code = False
    stack: List[str] = []
    for lineno, line in enumerate(SPEC.read_text().splitlines(), 1):
        if line.startswith("## ") or line.startswith("### settings."):
            section = line.lstrip("# ").strip()
        if line.startswith("```"):
            in_code = not in_code
            stack = []
            continue
        if not in_code or not (section == "header" or section == "settings" or section.startswith("settings.")):
            continue
        match = re.match(r'\s*"([^"]+)":\s*(.*)', line)
        if match:
            key, value = match.groups()
            parent = ".".join([section] + stack)
            target = schemas.setdefault(parent, {})
            typed = re.match(r'"(?:<([^>]+)>|(\[[^\"]+\]))"', value)
            if typed:
                target[key] = (typed.group(1) or typed.group(2), lineno)
            elif value.startswith("{") or value.startswith('"{'):
                target[key] = ("object", lineno)
                if value.startswith("{") and "}" not in value:
                    stack.append(key)
            elif section == "header" and stack == ["types"]:
                target[key] = ("int", lineno)
        elif re.match(r"\s*}", line) and stack:
            stack.pop()
    return schemas


SCHEMAS = schema_from_document()


def numeric(value: object) -> bool:
    return type(value) in (int, float)


def matches(value: object, expected: str) -> bool:
    if " | " in expected:
        return any(matches(value, x) for x in expected.split(" | "))
    if expected in ("int", "unsigned short"):
        return type(value) is int
    if expected == "double":
        return numeric(value)
    if expected == "bool":
        return type(value) is bool
    if expected == "string":
        return isinstance(value, str)
    if expected == "object":
        return isinstance(value, dict)
    if expected.startswith("["):
        items = expected[1:-1].split(",")
        return isinstance(value, list) and (len(items) == 1 or len(value) == len(items)) and all(matches(x, items[0].strip()) for x in value)
    raise ValueError("Unimplemented schema type: " + expected)


def audit(data: dict) -> List[Finding]:
    out: List[Finding] = []

    def emit(rule: str, severity: str, path: str, message: str, actual: object, expected: object, line: int) -> None:
        out.append(dict(rule=rule, severity=severity, path=path, message=message,
                        actual=actual, expected=expected, spec="docs/FC_INPUT_FORMAT.md:" + str(line)))

    def brief(value: object) -> object:
        if isinstance(value, (list, dict)):
            return {"type": type(value).__name__, "length": len(value)}
        return value

    def structural(obj: dict, section: str) -> None:
        schema = SCHEMAS[section]
        for key, value in obj.items():
            path = "$." + section + "." + str(key)
            if key not in schema:
                emit("DOC.UNKNOWN_FIELD", "ambiguity", path, "Поле не описано в актуальной схеме этого раздела; допустимость не установлена.", brief(value), "Описание поля в спецификации", 47 if section.startswith("header") else 1467)
                continue
            expected, line = schema[key]
            if not matches(value, expected):
                emit("DOC.FIELD_TYPE", "violation", path, "Тип значения расходится с указанным в спецификации.", brief(value), expected, line)
            elif expected == "unsigned short" and not 0 <= value <= 65535:
                emit("DOC.UNSIGNED_SHORT", "violation", path, "Значение не представимо как unsigned short.", value, "0..65535", line)
            if isinstance(value, dict) and section + "." + key in SCHEMAS:
                structural(value, section + "." + key)

    top_objects = {"header", "mesh", "sets", "settings"}
    top_arrays = {"materials", "property_tables", "coordinate_systems", "blocks", "loads", "restraints", "initial_sets", "coupling_constraints", "contact_constraints", "periodic_constraints", "receivers", "orientations", "imported_sections"}
    for key, value in data.items():
        if key in top_objects | top_arrays:
            expected = dict if key in top_objects else list
            if not isinstance(value, expected):
                emit("DOC.SECTION_TYPE", "violation", "$." + key, "Тип верхней секции расходится со схемой.", brief(value), expected.__name__, 21)
        elif key in {"load_sets", "restraint_sets"}:
            emit("DOC.LEGACY_SECTION", "legacy", "$." + key, "Документированная отключённая legacy-секция; в актуальном формате не используется.", brief(value), "loads/restraints", 2028)
        elif key == "contacts":
            emit("DOC.CONTACTS_CONFLICT", "ambiguity", "$.contacts", "Матрица совместимости называет contacts активным, но верхняя схема и описание его структуры отсутствуют.", brief(value), "Согласованная схема contacts", 2028)
        else:
            emit("DOC.UNKNOWN_SECTION", "ambiguity", "$." + key, "Верхняя секция не описана в спецификации.", brief(value), "Документированная секция", 21)
    for section in ("header", "settings"):
        section_data = data.get(section)
        if isinstance(section_data, dict):
            structural(section_data, section)
        elif section not in data:
            emit("DOC.MISSING_CONTEXT", "ambiguity", "$." + section, "Отсутствует контекст для выбора правил; обязательность секции не формализована.", None, "Контекст " + section, 21)
    for section in ("orientations", "imported_sections"):
        if data.get(section):
            emit("DOC.OPAQUE_SECTION", "ambiguity", "$." + section, "Секция названа, но схема её записей не определена; содержимое не проверено.", brief(data[section]), "Схема записей", 21)
    header = data.get("header", {})
    if isinstance(header, dict):
        version = header.get("version")
        if type(version) is int and version < 3:
            emit("DOC.LEGACY_VERSION", "legacy", "$.header.version", "Файл использует предыдущую версию формата.", version, "Текущая версия 3", 47)
        elif type(version) is int and version > 3:
            emit("DOC.UNKNOWN_VERSION", "ambiguity", "$.header.version", "Версия не описана документом.", version, 3, 47)
        types = header.get("types")
        if isinstance(types, dict):
            for key, width in types.items():
                if type(width) is int and width <= 0:
                    emit("DOC.TYPE_WIDTH", "violation", "$.header.types." + key, "Размер бинарного типа должен быть положительным.", width, "sizeof(type) > 0", 55)
        for key in ("version", "binary", "types"):
            if key not in header:
                emit("DOC.MISSING_CONTEXT", "ambiguity", "$.header." + key, "Не определён необходимый контекст интерпретации; значение по умолчанию не задано.", None, key, 47)
    settings = data.get("settings")
    if not isinstance(settings, dict):
        return out

    def obj(name: str) -> dict:
        value = settings.get(name, {})
        return value if isinstance(value, dict) else {}

    def enum(o: dict, path: str, key: str, allowed: Sequence[object], line: int, closed: bool = True) -> None:
        if key in o and isinstance(o[key], (str, int)) and o[key] not in allowed:
            emit("SET.ENUM" if closed else "SET.UNLISTED_MODE", "violation" if closed else "ambiguity", path + "." + key, "Значение не входит в перечисление документа." if closed else "Режим отсутствует в явно неполном перечне спецификации.", o[key], allowed, line)

    def required(o: dict, path: str, keys: List[str], line: int) -> None:
        for key in keys:
            if key not in o:
                emit("SET.REQUIRED", "violation", path + "." + key, "Отсутствует поле, явно требуемое для выбранного режима.", None, "Поле присутствует", line)

    def positive(o: dict, path: str, keys: List[str], line: int) -> None:
        for key in keys:
            if key in o and numeric(o[key]) and o[key] <= 0:
                emit("SET.POSITIVE", "violation", path + "." + key, "Требуется строго положительное значение.", o[key], "> 0", line)

    def exclusive(o: dict, path: str, keys: List[str], exactly_one: bool, line: int) -> None:
        present = [k for k in keys if k in o]
        if len(present) > 1 or (exactly_one and not present):
            emit("SET.EXCLUSIVE", "violation", path, "Нарушено документированное правило взаимоисключающих полей.", present, ("Ровно одно: " if exactly_one else "Не более одного: ") + ", ".join(keys), line)

    enum(settings, "$.settings", "type", ["static", "dynamic", "eigenfrequencies", "buckling", "spectrum", "harmonic", "effectiveprops"], 1513, False)
    enum(settings, "$.settings", "dimensions", ["2D", "3D"], 1472)
    # dimensions is simultaneously part of the current schema and marked unread legacy.
    if "dimensions" in settings:
        emit("DOC.DIMENSIONS_CONFLICT", "ambiguity", "$.settings.dimensions", "Основная схема описывает dimensions, legacy-раздел называет поле не читаемым; актуальность противоречива.", settings["dimensions"], "Уточнение противоречия документа", 1974)
    enum(settings, "$.settings", "plane_state", ["p-stress", "p-strain", "axisym_x", "axisym_y"], 1473)
    order = settings.get("spectral_order")
    if type(order) is int and not 3 <= order <= 9:
        emit("SET.SPECTRAL_ORDER", "violation", "$.settings.spectral_order", "Порядок вне указанного диапазона.", order, "3..9", 1489)
    linear = obj("linear_solver")
    for key, choices in {"method": ["auto", "direct", "iterative"], "use_cuda": ["yes", "no", "auto"], "precision": ["single", "double", "auto"], "use_uzawa": ["auto", "yes", "no"]}.items():
        enum(linear, "$.settings.linear_solver", key, choices, 1527)
    it = linear.get("iter_opts")
    if isinstance(it, dict):
        enum(it, "$.settings.linear_solver.iter_opts", "preconditioner", "auto none diagonal ilu0 ilut ssor multigrid multigrid_ilu1 algmultigrid ic ilu amg ainv_standart ainv_static ainv_novel ainv_unsym".split(), 1539)
    nonlinear = obj("nonlinear_solver")
    if settings.get("finite_deformations") is True:
        required(nonlinear, "$.settings.nonlinear_solver", ["min_load_steps", "max_load_steps", "max_iterations", "tolerance"], 1566)
    if nonlinear.get("arc_method") is True:
        required(nonlinear, "$.settings.nonlinear_solver", ["min_arc_length"], 1567)
    eigen = obj("eigen_solver")
    # Missing required fields are only errors for a selected eigenvalue analysis.
    active_eigen = settings.get("type") in ("eigenfrequencies", "buckling")
    if active_eigen:
        required(eigen, "$.settings.eigen_solver", ["solver", "relative_tolerance", "eps_max_iterations", "linear_solver"], 1570)
    if eigen:
        enum(eigen, "$.settings.eigen_solver", "solver", ["Auto", "krylovschur", "arnoldi", "lanczos", "gd", "jd", "blocklanczos"], 1612)
        enum(eigen, "$.settings.eigen_solver", "prime_solver", ["SLEPc", "BLOCK LANCZOS", "MKLES", "NECH"], 1621)
        if isinstance(eigen.get("number"), str):
            enum(eigen, "$.settings.eigen_solver", "number", ["all"], 1575)
        positive(eigen, "$.settings.eigen_solver", ["relative_tolerance", "eps_max_iterations"], 1578)
        target = eigen.get("target")
        if isinstance(target, list) and len(target) == 2 and numeric(target[0]) and target[0] < 0:
            emit("SET.TARGET_RANGE", "violation", "$.settings.eigen_solver.target", "Нижняя граница интервала должна быть неотрицательной.", target, "min >= 0", 1641)
        trans = eigen.get("spectr_trans")
        if isinstance(trans, dict):
            enum(trans, "$.settings.eigen_solver.spectr_trans", "name", ["auto", "shift", "shift_invert", "general_cayley"], 1628)
            if active_eigen:
                required(trans, "$.settings.eigen_solver.spectr_trans", ["name"], 1594)
            if trans.get("name") in ("shift", "shift_invert", "general_cayley"):
                required(trans, "$.settings.eigen_solver.spectr_trans", ["shift_value"] + (["anti_shift_value"] if trans["name"] == "general_cayley" else []), 1628)
        inner = eigen.get("linear_solver")
        if isinstance(inner, dict):
            if active_eigen:
                required(inner, "$.settings.eigen_solver.linear_solver", ["method", "preconditioner"], 1600)
            enum(inner, "$.settings.eigen_solver.linear_solver", "solver", ["direct", "iterative", "auto"], 1600)
            enum(inner, "$.settings.eigen_solver.linear_solver", "method", "auto preonly cg gmres richardson chebyshev bicg bcgs tfqmr minres cr gcr".split(), 1633)
            enum(inner, "$.settings.eigen_solver.linear_solver", "preconditioner", "auto lu none jacobi bjacobi sor ssor ilu asm".split(), 1637)
            if inner.get("preconditioner") == "lu" and inner.get("solver") != "direct":
                emit("SET.LU_DIRECT", "violation", "$.settings.eigen_solver.linear_solver", "Предобуславливатель lu требует solver=direct.", {"solver": inner.get("solver")}, "solver=direct", 1637)
            opts = inner.get("iter_opts")
            keys = ["linear_relative_tolerance", "linear_absolute_tolerance", "linear_divergence_tolerance", "linear_max_iterations"]
            if isinstance(opts, dict):
                if active_eigen:
                    required(opts, "$.settings.eigen_solver.linear_solver.iter_opts", keys, 1604)
                positive(opts, "$.settings.eigen_solver.linear_solver.iter_opts", keys, 1604)
    options = ["result_output_iter", "result_output_time", "result_number"]
    static = obj("statics")
    if static or settings.get("type") == "static":
        exclusive(static, "$.settings.statics", options, settings.get("type") == "static", 1685)
    dynamic = obj("dynamics")
    if dynamic or settings.get("type") == "dynamic":
        enum(dynamic, "$.settings.dynamics", "method", ["full_solution", "mode_superposition"], 1708)
        enum(dynamic, "$.settings.dynamics", "scheme", ["explicit", "implicit"], 1709)
        exclusive(dynamic, "$.settings.dynamics", options, settings.get("type") == "dynamic", 1711)
        exclusive(dynamic, "$.settings.dynamics", ["time_step", "steps_count"], dynamic.get("scheme") == "implicit", 1709)
        if dynamic.get("scheme") == "explicit":
            required(dynamic, "$.settings.dynamics", ["courant", "max_steps_count"], 1709)
        gamma = dynamic.get("newmark_gamma")
        if isinstance(gamma, (float, int)) and not isinstance(gamma, bool) and not 0 <= gamma <= .4:
            emit("SET.GAMMA", "violation", "$.settings.dynamics.newmark_gamma", "Параметр вне документированного диапазона.", gamma, "[0, 0.4]", 1700)
    harmonic = obj("harmonic")
    if harmonic:
        enum(harmonic, "$.settings.harmonic", "method", ["mode_superposition"], 1717)
        exclusive(harmonic, "$.settings.harmonic", ["frequency_step", "steps_count"], False, 1724)
        if harmonic.get("method") == "mode_superposition" and settings.get("type") == "harmonic":
            required(eigen, "$.settings.eigen_solver", ["modal_result_filename"], 1717)
    enum(obj("mbd"), "$.settings.mbd", "output_format", ["binary", "text"], 1761)
    enum(obj("table_interpolation"), "$.settings.table_interpolation", "interp_type", ["near", "LRBF_lin", "LRBF", "Triangle", "MC_lin"], 1772)
    enum(obj("table_interpolation"), "$.settings.table_interpolation", "func_type", ["gauss", "multiquad", "inv_multiquad", "inv_quad", "thin_plate", "wendland"], 1773)
    return out
