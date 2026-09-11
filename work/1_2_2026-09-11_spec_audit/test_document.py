"""Boundary checks for literal specification rules, including permitted modes."""
from audit_document import SCHEMAS, audit, matches


def test_schema_extraction_covers_nested_settings_and_authorized_fields():
    assert len(SCHEMAS["settings"]) == 39
    assert SCHEMAS["settings.output"]["full_periodic"][0] == "bool"
    assert SCHEMAS["settings.output"]["model_properties"][0] == "bool"
    assert SCHEMAS["settings.eigen_solver.linear_solver.iter_opts"]["linear_max_iterations"][0] == "int"


def test_json_scalar_and_fixed_array_types():
    assert matches(1, "double")
    assert not matches(True, "int")
    assert not matches(True, "double")
    assert matches([0, 1], "double | [double, double]")
    assert not matches([0], "double | [double, double]")


def test_valid_minimal_context_and_plain_array_mode():
    result = audit({"header": {"version": 3, "binary": False, "types": {"int": 4}}, "settings": {"type": "static", "statics": {"result_number": 1}}})
    assert result == []


def test_incomplete_enum_and_unknown_section_are_not_false_errors():
    result = audit({"header": {}, "settings": {"type": "new_analysis"}, "extension": {}})
    assert any(f["rule"] == "SET.UNLISTED_MODE" and f["severity"] == "ambiguity" for f in result)
    assert any(f["rule"] == "DOC.UNKNOWN_SECTION" and f["severity"] == "ambiguity" for f in result)


def test_conditional_required_fields_and_exclusivity():
    result = audit({"settings": {"type": "dynamic", "finite_deformations": True, "dynamics": {"scheme": "implicit", "time_step": .01, "steps_count": 10, "result_number": 1}}})
    assert any(f["rule"] == "SET.REQUIRED" and f["path"] == "$.settings.nonlinear_solver.tolerance" for f in result)
    assert any(f["rule"] == "SET.EXCLUSIVE" and f["path"] == "$.settings.dynamics" for f in result)


def test_contradictions_and_legacy_do_not_become_violations():
    result = audit({"header": {"version": 2}, "settings": {"dimensions": "3D"}, "contacts": [], "load_sets": []})
    assert any(f["rule"] == "DOC.DIMENSIONS_CONFLICT" and f["severity"] == "ambiguity" for f in result)
    assert any(f["rule"] == "DOC.LEGACY_SECTION" and f["severity"] == "legacy" for f in result)
    assert not any(f["severity"] == "violation" for f in result)
