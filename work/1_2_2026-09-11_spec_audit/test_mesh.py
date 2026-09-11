import base64
import json

from audit_mesh import audit


def _b64(values: bytes) -> str:
    return base64.b64encode(values).decode("ascii")


def _plain_model():
    return {
        "header": {"version": 3, "binary": False},
        "mesh": {
            "nodes_count": 4, "nids": [1, 2, 3, 4],
            "nodes": [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
            "elems_count": 1, "elemids": [1], "elem_types": [1],
            "elem_blocks": [1], "elem_orders": [1], "elem_parent_ids": [0],
            "elems": [1, 2, 3, 4],
        },
        "coordinate_systems": [{"id": 1, "type": "cartesian", "name": "global",
                                "origin": [0, 0, 0], "dir1": [1, 0, 0], "dir2": [0, 1, 0]}],
        "sets": {"nodesets": [{"id": 1, "name": "N", "apply_to_size": 2, "apply_to": [1, 2]}]},
        "blocks": [{"id": 1, "material_id": 1, "cs_id": 1, "steps": []}],
    }


def test_valid_plain_mesh_has_no_mesh_findings():
    assert audit(_plain_model()) == []
    assert audit(json.loads(json.dumps(_plain_model()), parse_int=float)) == []


def test_no_special_properties_is_not_a_missing_table_reference():
    model = _plain_model()
    model["property_tables"] = [{"id": 7}]
    for value in (-1, -1.0, 7):
        model["blocks"][0]["property_id"] = value
        assert not any(f["path"] == "$.blocks[0].property_id" for f in audit(model))
    model["blocks"][0]["property_id"] = 0
    assert any(f["rule"] == "BLOCK.PROPERTY_SENTINEL" for f in audit(model))
    model["blocks"][0]["property_id"] = 8
    assert any(f["rule"] == "BLOCK.PROPERTY_REF" for f in audit(model))
    model["blocks"][0]["property_id"] = -1
    model.pop("property_tables")
    assert not any(f["path"] == "$.blocks[0].property_id" for f in audit(model))


def test_connectivity_and_global_cs_are_checked():
    model = _plain_model()
    model["mesh"]["elems"] = [[1, 2, 3]]
    model["coordinate_systems"][0]["id"] = 2
    rules = {item["rule"] for item in audit(model)}
    assert "MESH.CONNECTIVITY" in rules
    assert "CS.GLOBAL" in rules


def test_binary_invalid_payload_and_set_size():
    model = _plain_model()
    model["header"] = {"version": 3, "binary": True, "types": {"int": 4, "double": 8}}
    for key in ("nids", "elemids", "elem_types", "elem_blocks", "elem_orders", "elem_parent_ids", "elems"):
        model["mesh"][key] = _b64(b"\0\0\0\0")
    model["mesh"]["nodes"] = _b64(b"\0" * 96)
    model["sets"]["nodesets"][0]["apply_to"] = "%%%"
    rules = {item["rule"] for item in audit(model)}
    assert "MESH.ARRAY_SIZE" in rules
    assert "MESH.BASE64" in rules


def test_elem_types_uses_one_byte_and_unknown_fields_are_reported():
    model = _plain_model()
    model["header"] = {"version": 3, "binary": True, "types": {"int": 4, "double": 8, "char": 1}}
    for key in ("nids", "elemids", "elem_blocks", "elem_orders", "elem_parent_ids", "elems"):
        model["mesh"][key] = _b64(b"\0\0\0\0")
    model["mesh"]["elem_types"] = _b64(b"\1")
    model["mesh"]["nodes"] = _b64(b"\0" * 96)
    model["mesh"]["future_field"] = 1
    rules = {item["rule"] for item in audit(model)}
    assert not any(f["path"] == "$.mesh.elem_types" for f in audit(model))
    assert "MESH.BINARY_SEMANTICS_UNCHECKED" not in rules
    assert "MESH.UNKNOWN_FIELD" in rules
    model["mesh"]["elem_types"] = _b64(b"\1\0\0\0")
    assert any(f["rule"] == "MESH.ARRAY_SIZE" and f["path"] == "$.mesh.elem_types" for f in audit(model))
