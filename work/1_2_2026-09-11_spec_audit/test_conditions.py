import base64

from audit_conditions import audit


def _ints(values):
    raw = b"".join(int(v).to_bytes(4, "little", signed=True) for v in values)
    return base64.b64encode(raw).decode("ascii")


def test_valid_binary_load_and_restraint():
    data = {
        "header": {"binary": True, "types": {"int": 4, "double": 8}},
        "loads": [{"type": 5, "apply_to_size": 1, "apply_to": _ints([3]),
                    "data": ["", "", "", "", "", ""],
                    "dep_var_num": [""] * 6, "dep_var_size": [0] * 6,
                    "dependency_type": [0, 0, 0, 0, 0, 0]}],
        "restraints": [{"flag": [1, 0, 0, 0, 0, 0], "apply_to_size": 1,
                        "apply_to": _ints([3]), "data": [""],
                        "dep_var_num": [""], "dep_var_size": [0],
                        "dependency_type": [0]}],
    }
    assert audit(data) == []


def test_load_enum_and_component_errors():
    findings = audit({"header": {"binary": False}, "loads": [{"type": 999, "data": [1, 2]}]})
    assert any(f["rule"] == "LOAD.TYPE_CODE" and f["severity"] == "ambiguity" for f in findings)
    assert any(f["rule"] == "LOAD.COMPONENT_COUNT" for f in findings) is False


def test_contact_alias_and_constraints():
    findings = audit({"header": {"binary": False}, "contact_constraints": [{
        "type": "tied", "method": "auto", "ignoreoverlap": False,
        "master_size": 1, "master": [[1, 2]], "slave_size": 1, "slave": [[2, 3]],
        "search_radius": 0,
    }]})
    assert not any(f["rule"] == "CONTACT.ALIAS" for f in findings)
    assert any(f["rule"] == "CONTACT.VALUE" for f in findings)


def test_initial_flag_and_receiver_dofs():
    findings = audit({"header": {"binary": False},
                      "initial_sets": [{"type": 2, "flag": [1], "apply_to": [1]}],
                      "receivers": [{"type": 0, "apply_to": [1], "dofs": [1, 0]}]})
    assert any(f["rule"] == "INITIAL.FLAG_SIZE" for f in findings)
    assert any(f["rule"] == "RECEIVER.DOFS" for f in findings)


def test_table_layout_accepts_valid_columns_and_rejects_corrupt_base64():
    payload = base64.b64encode(bytes(16)).decode("ascii")
    load = {"type": 1, "data": [payload], "dependency_type": [[4]], "dep_var_size": [2], "dep_var_num": [[payload]]}
    data = {"header": {"binary": True, "types": {"int": 4, "double": 8}}, "loads": [load]}
    assert audit(data) == []
    load["dep_var_num"] = [["not base64!"]]
    assert any(f["rule"] == "COND.NUMERIC_PAYLOAD" for f in audit(data))


def test_nested_types_and_initial_all_are_checked():
    data = {"header": {"binary": True, "types": {"int": 4, "double": 8}}, "initial_sets": [{"type": 3, "flag": [1], "apply_to": "all"}], "contact_constraints": [{"type": "general", "method": "auto", "lagrange_settings": {"use_tangent": "yes"}}]}
    findings = audit(data)
    assert not any(f["rule"] == "COND.BASE64" for f in findings)
    assert any(f["path"] == "$.contact_constraints[0].lagrange_settings.use_tangent" for f in findings)


def test_missing_width_does_not_invent_a_payload_size():
    findings = audit({"header": {"binary": True}, "loads": [{"type": 1, "apply_to_size": 1, "apply_to": _ints([1, 0])}]})
    assert any(f["rule"] == "COND.WIDTH_CONTEXT" for f in findings)
    assert not any(f["rule"] == "COND.SIZE" for f in findings)


def test_face_target_requires_pairs_and_point_targets_use_double_triples():
    header = {"binary": True, "types": {"int": 4, "double": 8}}
    assert any(f["rule"] == "COND.SIZE" for f in audit({"header": header, "loads": [{"type": 1, "apply_to_size": 1, "apply_to": _ints([1])}]}))
    point = {"type": 47, "apply_to_size": 1, "apply_to": base64.b64encode(bytes(24)).decode("ascii")}
    assert not any(f["rule"] in ("COND.SIZE", "COND.BASE64") for f in audit({"header": header, "loads": [point]}))
