import base64
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))
from audit_materials import audit


def _material(value: object = "AAAAAAAASUA="):
    return {
        "id": 1,
        "name": "Steel",
        "elasticity": [{
            "type": 0,
            "const_names": [0, 1],
            "const_types": [0, 0],
            "const_dep_size": [0, 0],
            "constants": [value, "MzMzMzMz0z8="],
            "const_dep": ["", ""],
        }],
    }


def test_valid_material_and_property_table_have_no_findings():
    data = {
        "header": {"binary": True, "types": {"double": 8}},
        "materials": [_material()],
        "property_tables": [{
            "id": 1,
            "type": 1,
            "properties": {"section_type": 0, "geometry": {"B": 1.0, "H": 2.0}},
            "layers": [],
        }],
    }
    assert audit(data) == []


def test_rejects_bad_enum_and_component_lengths():
    material = _material()
    material["elasticity"][0]["type"] = 999
    material["elasticity"][0]["const_types"] = [0]
    findings = audit({"materials": [material]})
    rules = {item["rule"] for item in findings}
    assert "MAT.GROUP_TYPE" in rules
    assert "MAT.COMPONENT_LENGTH" in rules


def test_checks_tabular_payload_lengths_and_formula_shape():
    material = _material()
    component = material["elasticity"][0]
    component["const_types"] = [[5], 6]
    component["const_dep_size"] = [2, 0]
    component["constants"] = [base64.b64encode(b"\x00" * 8).decode(), 3.0]
    component["const_dep"] = [[base64.b64encode(b"\x00" * 8).decode()], ""]
    findings = audit({"header": {"types": {"double": 8}}, "materials": [material]})
    rules = {item["rule"] for item in findings}
    assert "MAT.DEP_LENGTH" in rules
    assert "MAT.VALUE_ENCODING" in rules


def test_plain_json_numeric_arrays_are_accepted():
    material = _material([1.0])
    material["elasticity"][0]["constants"][1] = [0.3]
    assert audit({"header": {"binary": False, "types": {"double": 8}}, "materials": [material]}) == []


def test_binary_mode_rejects_plain_numeric_payloads():
    material = _material([1.0])
    findings = audit({"header": {"binary": True, "types": {"double": 8}}, "materials": [material]})
    assert any(item["rule"] == "MAT.VALUE_ENCODING" for item in findings)


def test_checks_cardinality_unknown_fields_and_table_value_length():
    material = _material()
    component = material["elasticity"][0]
    component["constants"][0] = base64.b64encode(b"\x00" * 8).decode()
    component["const_types"][0] = [5]
    component["const_dep_size"][0] = 2
    component["const_dep"][0] = [base64.b64encode(b"\x00" * 16).decode()]
    material["elasticity"].append(dict(component))
    material["elasticity"][0]["extra"] = 1
    findings = audit({"header": {"binary": True, "types": {"double": 8}}, "materials": [material],
                      "property_tables": [{"id": 1, "type": 5, "properties": {
                          "mass": 1.0, "mass_x": 2.0, "mass_distribution": 2}}]})
    rules = {item["rule"] for item in findings}
    assert "MAT.GROUP_CARDINALITY" in rules
    assert "MAT.UNKNOWN_FIELD" in rules
    assert "MAT.VALUE_LENGTH" in rules
    assert "PT.MASS_EXCLUSIVE" in rules
    assert "PT.MASS_DISTRIBUTION" in rules


def test_missing_width_scalar_table_code_and_unknown_group_schema():
    material = _material()
    material["elasticity"][0]["constants"][0] = "AAAAAAAASUA="
    material["elasticity"][0]["const_types"][0] = 1
    material["hsdf"] = [{"type": 0, "const_names": [], "const_types": [],
                          "const_dep_size": [], "constants": [], "const_dep": []}]
    findings = audit({"materials": [material]})
    rules = {item["rule"] for item in findings}
    assert "MAT.TYPE_SIZE" in rules
    assert "MAT.DEP_TYPE" in rules
    assert "MAT.GROUP_SCHEMA" in rules
