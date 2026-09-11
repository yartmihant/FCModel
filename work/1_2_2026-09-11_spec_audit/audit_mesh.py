"""Independent checks for mesh, coordinate systems, sets and blocks.

The checker deliberately consumes JSON-shaped data and does not import fc_model.
It checks structural claims made by the format document; geometry and byte order
are outside its remit.
"""
from base64 import b64decode
from typing import Dict, List, Optional, Tuple

from audit_types import is_integer

Finding = Dict[str, object]

_SPEC = "docs/FC_INPUT_FORMAT.md"
_MESH_FIELDS = ("nids", "nodes", "elemids", "elem_types", "elems")
_CURRENT_FIELDS = ("elem_blocks", "elem_orders", "elem_parent_ids")
_ELEMENT_CODES = {0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18,
                  20, 21, 22, 23, 24, 25, 26, 27, 29, 30, 31, 32, 36, 37,
                  38, 39, 40, 41, 82, 83, 84, 85, 86, 87, 89, 90, 95, 96,
                  97, 98, 99, 100, 101, 105}
_NODE_COUNTS = {1: 4, 2: 10, 3: 8, 4: 20, 6: 6, 7: 15, 8: 5, 9: 13,
                10: 3, 11: 6, 12: 4, 13: 8}


def _finding(rule: str, severity: str, path: str, message: str,
             actual: object, expected: object, line: int) -> Finding:
    return {"rule": rule, "severity": severity, "path": path,
            "message": message, "actual": actual, "expected": expected,
            "spec": "%s:%d" % (_SPEC, line)}


def _type(value: object, name: str, path: str, out: List[Finding], line: int) -> bool:
    if name == "int":
        good = is_integer(value)
    elif name == "bool":
        good = isinstance(value, bool)
    elif name == "string":
        good = isinstance(value, str)
    else:
        good = isinstance(value, (int, float)) and not isinstance(value, bool)
    if not good:
        out.append(_finding("MESH.TYPE", "violation", path,
                            "Поле имеет неверный тип", type(value).__name__, name, line))
    return good


def _array(value: object, path: str, binary: bool, width: int,
           expected_count: Optional[int], out: List[Finding], line: int) -> Optional[List[object]]:
    if binary:
        if not isinstance(value, str):
            out.append(_finding("MESH.ARRAY_ENCODING", "violation", path,
                                "В binary=true массив должен быть Base64-строкой",
                                type(value).__name__, "Base64 string", line))
            return None
        try:
            raw = b64decode(value, validate=True)
        except Exception:
            out.append(_finding("MESH.BASE64", "violation", path,
                                "Массив не является корректным Base64", "invalid", "valid Base64", line))
            return None
        if width <= 0:
            out.append(_finding("MESH.TYPE_SIZE", "ambiguity", path,
                                "Размер типа отсутствует или некорректен; размер массива не установлен",
                                width, "> 0", 54))
            return None
        if len(raw) % width:
            out.append(_finding("MESH.BUFFER_SIZE", "violation", path,
                                "Длина бинарного массива не кратна размеру типа",
                                len(raw), "multiple of %d" % width, line))
            return None
        count = len(raw) // width
        if expected_count is not None and count != expected_count:
            out.append(_finding("MESH.ARRAY_SIZE", "violation", path,
                                "Размер бинарного массива не совпадает с *_count",
                                count, expected_count, line))
        return None
    if not isinstance(value, list):
        out.append(_finding("MESH.ARRAY_TYPE", "violation", path,
                            "В binary=false массив должен быть JSON-массивом",
                            type(value).__name__, "array", line))
        return None
    if expected_count is not None and len(value) != expected_count:
        out.append(_finding("MESH.ARRAY_SIZE", "violation", path,
                            "Размер JSON-массива не совпадает с *_count",
                            len(value), expected_count, line))
    return value


def _plain_numbers(values: Optional[List[object]], path: str, out: List[Finding], integers: bool = False) -> None:
    if values is not None:
        bad = [type(v).__name__ for v in values if not (is_integer(v) if integers else isinstance(v, (int, float)) and not isinstance(v, bool))]
        if bad:
            out.append(_finding("MESH.ITEM_TYPE", "violation", path, "Типы элементов массива расходятся с указанным типом", bad[:8], "int items" if integers else "numeric items", 69))


def _size(types: Dict[str, object], key: str) -> int:
    value = types.get(key)
    return int(value) if isinstance(value, (int, float)) and is_integer(value) else 0


def _id_set(values: Optional[List[object]]) -> set:
    result = set()
    for value in values or []:
        candidate = value.get("id") if isinstance(value, dict) else value
        if is_integer(candidate):
            result.add(candidate)
    return result


def audit(data: dict) -> list:
    out: List[Finding] = []
    if not isinstance(data, dict):
        return [_finding("MESH.ROOT", "violation", "$", "Ожидался JSON-объект", type(data).__name__, "object", 64)]
    header = data.get("header")
    h = header if isinstance(header, dict) else {}
    binary = h.get("binary") is True
    raw_types = h.get("types")
    types: Dict[str, object] = {str(k): v for k, v in raw_types.items()} if isinstance(raw_types, dict) else {}
    int_width = _size(types, "int")
    double_width = _size(types, "double")
    version = h.get("version", 3)
    mesh = data.get("mesh")
    if not isinstance(mesh, dict):
        out.append(_finding("MESH.OBJECT", "violation", "$.mesh", "Секция mesh должна быть объектом", type(mesh).__name__, "object", 64))
        mesh = {}
    legacy = is_integer(version) and version < 3
    if legacy:
        out.append(_finding("MESH.LEGACY_LAYOUT", "legacy", "$.mesh", "Используется документированный legacy layout mesh для версии до 3", version, "version < 3", 2079))
    ncount = mesh.get("nodes_count")
    ecount = mesh.get("elems_count")
    ncount_int = int(ncount) if isinstance(ncount, (int, float)) and is_integer(ncount) else None
    ecount_int = int(ecount) if isinstance(ecount, (int, float)) and is_integer(ecount) else None
    if _type(ncount, "int", "$.mesh.nodes_count", out, 69):
        if ncount_int is not None and ncount_int < 0:
            out.append(_finding("MESH.COUNT", "violation", "$.mesh.nodes_count", "Количество узлов не может быть отрицательным", ncount, ">= 0", 69))
    if _type(ecount, "int", "$.mesh.elems_count", out, 71):
        if ecount_int is not None and ecount_int < 0:
            out.append(_finding("MESH.COUNT", "violation", "$.mesh.elems_count", "Количество элементов не может быть отрицательным", ecount, ">= 0", 71))
    for key in ("nids", "elemids", "elem_types", "elems"):
        if legacy:
            # Old packing is explicitly mentioned but not specified; the v3
            # width/arity requirements cannot adjudicate a legacy buffer.
            continue
        if key not in mesh:
            out.append(_finding("MESH.FIELD", "violation", "$.mesh.%s" % key, "Отсутствует поле mesh, необходимое для текущей схемы", "missing", "present", 69))
            continue
        expected = None
        if key in ("nids",): expected = ncount_int
        if key in ("elemids", "elem_types"): expected = ecount_int
        plain = _array(mesh[key], "$.mesh.%s" % key, binary, 1 if key == "elem_types" else int_width, expected, out, 73 if key == "elem_types" else 69)
        if key != "elems":
            _plain_numbers(plain, "$.mesh.%s" % key, out, integers=True)
    if "nodes" in mesh:
        node_expected = ncount_int * 3 if ncount_int is not None else None
        vals = _array(mesh["nodes"], "$.mesh.nodes", binary, double_width, node_expected, out, 70)
        if vals is not None and any(isinstance(row, (list, dict, str, bool)) for row in vals):
            out.append(_finding("MESH.NODE_LAYOUT", "violation", "$.mesh.nodes", "В plain JSON координаты должны быть плоским массивом чисел", "nested/non-numeric", "flat [x0,y0,z0,...]", 70))
        if vals is not None and not any(isinstance(row, list) for row in vals):
            _plain_numbers(vals, "$.mesh.nodes", out)
    else:
        out.append(_finding("MESH.NODES_MISSING", "ambiguity", "$.mesh.nodes", "Отсутствуют координаты узлов; mesh невозможно полноценно интерпретировать", "missing", "nodes array", 70))
    for key in _CURRENT_FIELDS:
        if key in mesh and not legacy:
            expected = ecount_int
            _array(mesh[key], "$.mesh.%s" % key, binary, int_width, expected, out, 74)
    allowed_mesh = {"nodes_count", "nids", "nodes", "elems_count", "elemids", "elem_types", "elems"}
    allowed_mesh |= set(_CURRENT_FIELDS) if not legacy else {"elem_materials", "elem_properties"}
    if legacy:
        out.append(_finding("MESH.LEGACY_LAYOUT_FIELDS", "ambiguity", "$.mesh", "Набор полей старого mesh layout не раскрыт актуальной спецификацией", sorted(mesh), "legacy layout", 2079))
    else:
        for key in mesh:
            if key not in allowed_mesh:
                out.append(_finding("MESH.UNKNOWN_FIELD", "ambiguity", "$.mesh.%s" % key, "Неизвестное поле mesh не описано спецификацией", key, sorted(allowed_mesh), 64))
    # ``elem_types`` was already checked above; retain its plain JSON value for
    # the additional code/connectivity checks without duplicating findings.
    types_values = mesh.get("elem_types") if not binary and isinstance(mesh.get("elem_types"), list) else None
    if types_values is not None:
        unknown = [v for v in types_values if not is_integer(v) or v not in _ELEMENT_CODES]
        if unknown:
            out.append(_finding("MESH.ELEM_TYPE", "ambiguity", "$.mesh.elem_types", "Встречены коды элементов, не перечисленные в актуальной таблице; их поддержка не определена", unknown[:8], sorted(_ELEMENT_CODES), 87))
    # Connectivity shape can be checked only for plain JSON; binary byte order is unspecified.
    if not binary and isinstance(mesh.get("elems"), list) and isinstance(types_values, list):
        if any(isinstance(row, list) for row in mesh["elems"]):
            out.append(_finding("MESH.CONNECTIVITY_LAYOUT", "ambiguity", "$.mesh.elems", "Спецификация описывает packed flat connectivity, а найден nested JSON layout требует уточнения", "nested arrays", "flat packed array", 76))
        elif all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in mesh["elems"]):
            expected_total = sum(_NODE_COUNTS.get(code, 0) for code in types_values if is_integer(code))
            if expected_total and all(code in _NODE_COUNTS for code in types_values) and len(mesh["elems"]) != expected_total:
                out.append(_finding("MESH.CONNECTIVITY", "violation", "$.mesh.elems", "Длина packed connectivity не соответствует сумме известных FEM арностей", len(mesh["elems"]), expected_total, 76))
            _plain_numbers(mesh["elems"], "$.mesh.elems", out, integers=True)
        for index, row in enumerate(mesh["elems"]):
            if not isinstance(row, list):
                break
            code = types_values[index] if index < len(types_values) else None
            expected_nodes = _NODE_COUNTS.get(int(code)) if isinstance(code, (int, float)) and is_integer(code) else None
            if expected_nodes is not None and (not isinstance(row, list) or len(row) != expected_nodes):
                out.append(_finding("MESH.CONNECTIVITY", "violation", "$.mesh.elems[%d]" % index, "Число узлов connectivity не соответствует типу элемента", len(row) if isinstance(row, list) else type(row).__name__, expected_nodes, 76))
    _audit_coords(data, out, binary, double_width)
    _audit_sets(data, out, binary, int_width)
    _audit_blocks(data, out, binary, int_width)
    # IDs are reference keys; repeated keys make the referenced record unclear.
    # The document does not explicitly specify their uniqueness, so report a
    # documentation ambiguity instead of inventing a strict prohibition.
    for section in ("materials", "property_tables", "coordinate_systems"):
        records = data.get(section)
        if isinstance(records, list):
            first = {}
            for index, record in enumerate(records):
                if isinstance(record, dict) and is_integer(record.get("id")):
                    identity = record["id"]
                    if identity in first:
                        out.append(_finding("REF.DUPLICATE_ID", "ambiguity", "$.%s[%d].id" % (section, index), "ID повторяется: выбор записи по ссылке неоднозначен, политика дубликатов не описана", {"id": identity, "first_index": first[identity]}, "Однозначный ID либо документированная политика дубликатов", 1012))
                    else:
                        first[identity] = index
    return out


def _audit_coords(data: dict, out: List[Finding], binary: bool, double_width: int) -> None:
    value = data.get("coordinate_systems")
    if value is None: return
    if not isinstance(value, list):
        out.append(_finding("CS.TYPE", "violation", "$.coordinate_systems", "coordinate_systems должна быть массивом", type(value).__name__, "array", 974)); return
    ids = []
    for i, item in enumerate(value):
        p = "$.coordinate_systems[%d]" % i
        if not isinstance(item, dict):
            out.append(_finding("CS.ITEM", "violation", p, "Элемент coordinate_systems должен быть объектом", type(item).__name__, "object", 978)); continue
        for key, typ in (("id", "int"), ("type", "string")):
            if key not in item: out.append(_finding("CS.FIELD", "ambiguity", p+"."+key, "Без поля невозможно однозначно интерпретировать систему координат", "missing", typ, 980)); continue
            _type(item[key], typ, p+"."+key, out, 980)
        if "name" in item:
            _type(item["name"], "string", p+".name", out, 980)
        if is_integer(item.get("id")): ids.append(item["id"])
        for key in ("origin", "dir1", "dir2"):
            if key in item: _array(item[key], p+"."+key, binary, double_width, 3, out, 982)
        if item.get("type") not in ("cartesian", "cylindrical", "spherical"):
            out.append(_finding("CS.TYPE_CODE", "ambiguity", p+".type", "Тип системы координат не перечислен в спецификации", item.get("type"), "cartesian|cylindrical|spherical", 980))
        for key in item:
            if key not in {"id", "type", "name", "origin", "dir1", "dir2"}:
                out.append(_finding("CS.UNKNOWN_FIELD", "ambiguity", p+"."+key, "Неизвестное поле coordinate_systems не описано спецификацией", key, "documented field", 974))
    if value and ids.count(1) != 1:
        out.append(_finding("CS.GLOBAL", "ambiguity", "$.coordinate_systems", "В непустой секции не найдена однозначная глобальная система с id=1", ids, "one id=1", 980))
    for i, item in enumerate(value):
        if isinstance(item, dict) and item.get("id") == 1 and item.get("type") != "cartesian":
            out.append(_finding("CS.GLOBAL_TYPE", "violation", "$.coordinate_systems[%d].type" % i, "Глобальная система id=1 должна быть cartesian", item.get("type"), "cartesian", 980))
        if isinstance(item, dict) and is_integer(item.get("id")) and item["id"] <= 0:
            out.append(_finding("CS.ID", "violation", "$.coordinate_systems[%d].id" % i, "Идентификатор системы координат должен быть > 0", item["id"], "> 0", 980))


def _audit_sets(data: dict, out: List[Finding], binary: bool, int_width: int) -> None:
    value = data.get("sets")
    if value is None: return
    if not isinstance(value, dict): out.append(_finding("SET.TYPE", "violation", "$.sets", "sets должна быть объектом", type(value).__name__, "object", 993)); return
    for kind, line in (("nodesets", 994), ("sidesets", 1002)):
        if kind not in value: continue
        records = value[kind]
        if not isinstance(records, list): out.append(_finding("SET.TYPE", "violation", "$.sets."+kind, "Набор должен быть массивом", type(records).__name__, "array", line)); continue
        for i, rec in enumerate(records):
            p = "$.sets.%s[%d]" % (kind, i)
            if not isinstance(rec, dict): out.append(_finding("SET.ITEM", "violation", p, "Запись set должна быть объектом", type(rec).__name__, "object", line)); continue
            for key, typ in (("id", "int"), ("apply_to_size", "int")):
                if key in rec: _type(rec[key], typ, p+"."+key, out, line)
                else: out.append(_finding("SET.FIELD", "violation", p+"."+key, "Отсутствует поле set", "missing", typ, line))
            if "name" in rec:
                _type(rec["name"], "string", p+".name", out, line)
            size = rec.get("apply_to_size")
            expected = size if is_integer(size) else None
            if kind == "sidesets" and expected is not None and binary: expected *= 2
            _array(rec.get("apply_to"), p+".apply_to", binary, int_width, expected, out, line)
            for key in rec:
                if key not in {"id", "name", "apply_to_size", "apply_to"}:
                    out.append(_finding("SET.UNKNOWN_FIELD", "ambiguity", p+"."+key, "Неизвестное поле set не описано спецификацией", key, "documented field", line))
    for key in value:
        if key not in {"nodesets", "sidesets"}:
            out.append(_finding("SET.UNKNOWN_FIELD", "ambiguity", "$.sets."+key, "Неизвестная подсекция sets не описана спецификацией", key, "nodesets|sidesets", 993))


def _audit_blocks(data: dict, out: List[Finding], binary: bool, int_width: int) -> None:
    value = data.get("blocks")
    if value is None: return
    if not isinstance(value, list): out.append(_finding("BLOCK.TYPE", "violation", "$.blocks", "blocks должна быть массивом", type(value).__name__, "array", 1014)); return
    cs_ids = _id_set(data.get("coordinate_systems") if isinstance(data.get("coordinate_systems"), list) else None)
    material_ids = _id_set(data.get("materials") if isinstance(data.get("materials"), list) else None)
    property_ids = _id_set(data.get("property_tables") if isinstance(data.get("property_tables"), list) else None)
    ids = set()
    for i, block in enumerate(value):
        p = "$.blocks[%d]" % i
        if not isinstance(block, dict): out.append(_finding("BLOCK.ITEM", "violation", p, "Запись block должна быть объектом", type(block).__name__, "object", 1016)); continue
        for key in ("id",):
            if key not in block: out.append(_finding("BLOCK.FIELD", "violation", p+"."+key, "Отсутствует идентификатор блока", "missing", "int", 1017)); continue
            _type(block[key], "int", p+"."+key, out, 1017)
        if is_integer(block.get("id")):
            if block["id"] in ids: out.append(_finding("BLOCK.ID", "violation", p+".id", "Идентификатор блока повторяется", block["id"], "unique", 1017))
            ids.add(block["id"])
        for key in ("material_id", "property_id", "cs_id", "orientation_id"):
            if key in block:
                _type(block[key], "int", p+"."+key, out, 1017)
        if block.get("material_id") == 0:
            if not isinstance(block.get("material"), dict):
                out.append(_finding("BLOCK.MATERIAL_ZERO", "violation", p+".material_id", "Нулевой material_id означает ошибку: материал блока не назначен", 0, "non-zero material id or material alternative", 2095))
        if is_integer(block.get("material_id")) and block["material_id"] != 0 and material_ids and block["material_id"] not in material_ids:
            out.append(_finding("BLOCK.MATERIAL_REF", "violation", p+".material_id", "material_id блока отсутствует среди материалов", block["material_id"], sorted(material_ids), 1018))
        # -1 denotes absence of special block properties, not a table reference.
        if is_integer(block.get("property_id")) and block["property_id"] != -1 and property_ids and block["property_id"] not in property_ids:
            if block["property_id"] == 0:
                out.append(_finding("BLOCK.PROPERTY_SENTINEL", "ambiguity", p+".property_id", "Значение property_id вне таблицы не имеет документированного универсального sentinel-смысла", block["property_id"], sorted(property_ids), 1021))
            else:
                out.append(_finding("BLOCK.PROPERTY_REF", "violation", p+".property_id", "property_id блока отсутствует среди property_tables", block["property_id"], sorted(property_ids), 1021))
        if "cs_id" in block and cs_ids and block["cs_id"] not in cs_ids:
            out.append(_finding("BLOCK.CS_REF", "violation", p+".cs_id", "cs_id блока не ссылается на coordinate_systems", block["cs_id"], sorted(cs_ids), 1024))
        if "steps" in block and (not isinstance(block.get("steps"), list) or any(not is_integer(x) for x in block["steps"])):
            out.append(_finding("BLOCK.STEPS", "violation", p+".steps", "steps блока должен быть массивом int", block["steps"], "[int]", 1026))
        material = block.get("material")
        if material is not None:
            if not isinstance(material, dict):
                out.append(_finding("BLOCK.MATERIAL", "violation", p+".material", "material блока должен быть объектом", type(material).__name__, "object", 1019))
            else:
                mids, msteps = material.get("ids"), material.get("steps")
                if not isinstance(mids, list) or any(not is_integer(x) for x in mids):
                    out.append(_finding("BLOCK.MATERIAL_IDS", "violation", p+".material.ids", "material.ids должен быть массивом int", mids, "[int]", 1019))
                if not isinstance(msteps, list) or any(not is_integer(x) for x in msteps):
                    out.append(_finding("BLOCK.MATERIAL_STEPS", "violation", p+".material.steps", "material.steps должен быть массивом int", msteps, "[int]", 1019))
                if isinstance(mids, list) and isinstance(msteps, list) and len(mids) != len(msteps):
                    out.append(_finding("BLOCK.MATERIAL_PAIRING", "violation", p+".material", "ids и steps должны иметь одинаковую длину", [len(mids), len(msteps)], "equal lengths", 1019))
        for key in block:
            if key not in {"id", "material_id", "material", "property_id", "cs_id", "orientation_id", "steps"}:
                out.append(_finding("BLOCK.UNKNOWN_FIELD", "ambiguity", p+"."+key, "Неизвестное поле block не описано спецификацией", key, "documented field", 1016))
