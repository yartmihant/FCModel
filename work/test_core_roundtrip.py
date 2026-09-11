"""Checks for the diagnostic runner, separate from the package's unit suite."""
from pathlib import Path
from typing import List, Tuple

import pytest

from core_roundtrip import JSON, audit_file, differences, read_json


def test_object_order_is_ignored_recursively() -> None:
    assert not list(differences({"a": [{"x": 1, "y": 2}], "b": None},
                                {"b": None, "a": [{"y": 2, "x": 1}]}))


CASES: List[Tuple[JSON, JSON, str]] = [
    ({"data": []}, {}, "removed"),
    ({}, {"data": []}, "added"),
    ([1, 2], [2, 1], "value_changed"),
    ([1, 2], [1], "length_changed"),
    (True, 1, "type_changed"),
    (1, 1.0, "type_changed"),
    ("AQAAAA==", "AgAAAA==", "value_changed"),
]


@pytest.mark.parametrize("before,after,kind", CASES)
def test_strict_differences(before: JSON, after: JSON, kind: str) -> None:
    assert list(differences(before, after))[0]["kind"] == kind


def test_json_pointer_escapes_keys() -> None:
    assert list(differences({"a/b~": 1}, {}))[0]["path"] == "/a~1b~0"


@pytest.mark.parametrize("text", ['{"a": 1, "a": 2}', '{"x": NaN}', '{"x": Infinity}'])
def test_ambiguous_or_invalid_json_rejected(tmp_path: Path, text: str) -> None:
    source = tmp_path / "invalid.fc"
    source.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        read_json(source)


def test_audit_captures_error_and_continues(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.fc"
    invalid.write_text('{"header": {}}', encoding="utf-8")
    failed = audit_file(invalid, tmp_path / "bad-out.fc", "invalid.fc")
    assert failed["status"] == "error"
    assert failed["stage"] == "load"
    assert failed["source_unchanged"] is True
    # A checked-in real FC case exercises the public load/save and actual disk I/O.
    source = Path(__file__).resolve().parents[1] / "tests/data/ultracube.fc"
    output = tmp_path / "valid-out.fc"
    result = audit_file(source, output, source.name)
    assert result["status"] in ("equal", "different")
    assert result["source_unchanged"] is True
    assert output.is_file()
    assert result["differences"] == list(differences(read_json(source), read_json(output)))
