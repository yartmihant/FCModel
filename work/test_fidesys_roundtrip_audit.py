"""Stage classification and real process/export lifecycle without Fidesys."""
import json
from pathlib import Path
import sys

import pytest

from core_roundtrip import sha256
from fidesys_roundtrip_audit import classify, parse_stages, run_case


def successful() -> dict:
    return dict(timeout=False, returncode=11, output_valid=True,
                import_stage={"completion": {"errors": 0}, "errors": []},
                export_stage={"errors": []}, export_completion={"errors": 0, "result": True})


@pytest.mark.parametrize("change,expected", [
    ({}, "roundtrip_passed"),
    ({"output_valid": False}, "invalid_output"),
    ({"export_completion": None}, "export_incomplete"),
    ({"export_completion": {"errors": 1, "result": True}}, "export_error"),
    ({"export_completion": {"errors": 0, "result": False}}, "export_error"),
    ({"export_stage": {"errors": ["Export failed"]}}, "export_error"),
    ({"import_stage": {"completion": {"errors": 1}, "errors": []}}, "import_error"),
    ({"import_stage": {"completion": None, "errors": []}}, "import_incomplete"),
    ({"returncode": -11}, "abnormal_exit"),
    ({"timeout": True}, "timeout"),
])
def test_success_requires_both_stages_and_valid_output(change: dict, expected: str) -> None:
    record = successful()
    record.update(change)
    assert classify(record) == expected


def test_stage_separation_ignores_echoes_and_only_the_authorized_warning() -> None:
    text = '''%>print("FCMODEL_IMPORT_DONE=" + value)
ERROR: Import failed.
WARNING: The distance between nodesets is not accurate.
FCMODEL_IMPORT_DONE={"errors":1,"nodes":2,"elements":1}
WARNING: Keep this warning.
ERROR: Export failed.
FCMODEL_EXPORT_DONE={"errors":2,"nodes":2,"elements":1,"result":true}
'''
    result = parse_stages(text)
    assert result["import_stage"]["errors"] == ["Import failed."]
    assert result["import_stage"]["warnings"] == []
    assert result["export_stage"]["errors"] == ["Export failed."]
    assert result["export_stage"]["warnings"] == ["Keep this warning."]
    assert result["export_completion"]["errors"] == 2
    with pytest.raises(ValueError):
        parse_stages('FCMODEL_EXPORT_DONE={"errors":0}')


def test_batch_export_is_fresh_and_original_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    original = source / "case.fc"
    original.write_text(json.dumps({"header": {}, "mesh": {"nodes_count": 1, "elems_count": 1}}))
    executable = tmp_path / "fake_fidesys"
    executable.write_text("#!" + sys.executable + "\n" + '''import json, sys
from pathlib import Path
probe = Path(sys.argv[sys.argv.index("-input") + 1]).read_text()
target = probe.split('export fidesyscase "')[1].split('"')[0]
print('FCMODEL_IMPORT_DONE={"errors":0,"nodes":1,"elements":1}')
Path(target).write_text(json.dumps({"header":{},"mesh":{"nodes_count":1,"elems_count":1},"added":True}))
print('FCMODEL_EXPORT_DONE={"errors":0,"nodes":1,"elements":1,"result":true}')
sys.exit(11)
''')
    executable.chmod(0o700)
    digest = sha256(original)
    entry = {"file": "case.fc", "sha256": digest, "status": "equal"}
    result = run_case(executable, source, entry, tmp_path / "results", 5)
    assert result["alive"] is True
    assert result["json_status"] == "different"
    assert result["differences"][0]["path"] == "/added"
    assert sha256(original) == digest
    with pytest.raises(FileExistsError):
        run_case(executable, source, entry, tmp_path / "results", 5)
