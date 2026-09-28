from compare import normalize
from core_roundtrip import differences


def test_entire_settings_header_and_entity_names_are_ignored():
    a = {"header": {"version": 1}, "settings": {"solver": "one"},
         "restraints": [{"id": 1, "name": "old"}],
         "sets": {"nodesets": [{"id": 2, "name": "old"}]}}
    b = {"header": {"new": True}, "restraints": [{"id": 1}],
         "sets": {"nodesets": [{"id": 2, "name": "new"}]}}
    assert list(differences(normalize(a), normalize(b))) == []
    assert a["restraints"][0]["name"] == "old"  # No mutation of source.


def test_semantic_nested_name_and_ids_are_not_ignored():
    for a, b in [
        ({"materials": [{"law": {"name": "A"}}]}, {"materials": [{"law": {"name": "B"}}]}),
        ({"blocks": [{"id": 1}]}, {"blocks": [{"id": 2}]}),
        ({"mesh": {"nodes": "AAAA"}}, {"mesh": {"nodes": "BBBB"}}),
    ]:
        assert list(differences(normalize(a), normalize(b)))


def test_array_order_numeric_types_and_presence_remain_strict():
    for a, b in [({"x": [1, 2]}, {"x": [2, 1]}), ({"x": 1}, {"x": 1.0}),
                 ({"x": []}, {}), ({"loads": [{"name": "A"}]}, {"loads": []})]:
        assert list(differences(normalize(a), normalize(b)))
