"""Parser, status and process-lifecycle tests; no Fidesys installation required."""
from pathlib import Path
import sys
import time
from typing import Dict

import pytest

from core_roundtrip import JSON, sha256
from fidesys_import_audit import classify, parse_output, run_import, summarize


def completed(errors: int = 0) -> Dict[str, JSON]:
    return {"completion": {"errors": errors, "nodes": 16, "elements": 9},
            "errors": []}


def test_collect_and_deduplicate_console_errors() -> None:
    parsed = parse_output('''[2026-09-11 15:00:00.000] [error] Master entity is empty.
ERROR: Master entity is empty.
[2026-09-11 15:00:00.001] [error] Command Failed.
ERROR: Command Failed.
WARNING: A model warning.
Fontconfig warning: example
FCMODEL_IMPORT_DONE={"errors":2,"nodes":0,"elements":0}
''')
    assert parsed["errors"] == ["Master entity is empty.", "Command Failed."]
    assert parsed["primary_errors"] == ["Master entity is empty."]
    assert parsed["warnings"] == ["A model warning.", "Fontconfig warning: example"]
    assert classify(parsed, False, 11) == "import_error"


def test_echoed_python_and_true_do_not_prove_success() -> None:
    parsed = parse_output('%>print("FCMODEL_IMPORT_DONE=" + json.dumps({}))\nTrue\n')
    assert parsed["completion"] is None
    assert classify(parsed, False, 11) == "incomplete"


@pytest.mark.parametrize("timeout,code,errors,expected", [
    (False, 11, 0, "loaded_without_errors"),
    (False, 0, 0, "loaded_without_errors"),
    (False, 11, 2, "import_error"),
    (True, 11, 0, "timeout"),
    (False, -11, 0, "abnormal_exit"),
])
def test_completion_is_required_with_clean_exit(timeout: bool, code: int,
                                                errors: int, expected: str) -> None:
    assert classify(completed(errors), timeout, code) == expected


def test_malformed_probe_rejected() -> None:
    with pytest.raises(ValueError):
        parse_output('FCMODEL_IMPORT_DONE={"errors": 0}')


def fake_executable(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "fake_fidesys"
    path.write_text("#!" + sys.executable + "\n" + body, encoding="utf-8")
    path.chmod(0o700)
    return path


@pytest.mark.parametrize("hang", [False, True])
def test_real_process_log_timeout_and_source_integrity(tmp_path: Path, hang: bool) -> None:
    source = tmp_path / "source"
    source.mkdir()
    model = source / "sample.fc"
    model.write_text("{}", encoding="utf-8")
    entry: Dict[str, JSON] = {"file": "sample.fc", "sha256": sha256(model), "status": "equal"}
    body = ('import time\ntime.sleep(20)\n' if hang else
            'print(\'FCMODEL_IMPORT_DONE={"errors":0,"nodes":16,"elements":9}\', flush=True)\n'
            'raise SystemExit(11)\n')
    result = run_import(fake_executable(tmp_path, body), source, entry,
                        tmp_path / "output", 0.2 if hang else 5)
    assert result["status"] == ("timeout" if hang else "loaded_without_errors")
    assert result["source_unchanged"] is True
    assert model.read_text() == "{}"
    assert (tmp_path / "output" / str(result["log"])).is_file()


def test_changed_source_not_correlated_with_stale_baseline(tmp_path: Path) -> None:
    model = tmp_path / "sample.fc"
    model.write_text("{}", encoding="utf-8")
    entry: Dict[str, JSON] = {"file": model.name, "sha256": "old", "status": "equal"}
    with pytest.raises(ValueError, match="differs from roundtrip"):
        run_import(tmp_path / "unused", tmp_path, entry, tmp_path / "output", 1)


def test_timeout_stops_spawned_descendant(tmp_path: Path) -> None:
    model = tmp_path / "sample.fc"
    model.write_text("{}", encoding="utf-8")
    late_file = tmp_path / "descendant_survived"
    child = "import time; from pathlib import Path; time.sleep(1); Path(" + repr(str(late_file)) + ").touch()"
    body = ("import subprocess, sys, time\nsubprocess.Popen([sys.executable, '-c', "
            + repr(child) + "])\ntime.sleep(20)\n")
    entry: Dict[str, JSON] = {"file": model.name, "sha256": sha256(model), "status": "equal"}
    result = run_import(fake_executable(tmp_path, body), tmp_path, entry,
                        tmp_path / "output", 0.3)
    assert result["status"] == "timeout"
    time.sleep(1.2)
    assert not late_file.exists()


def test_correlation_counts_files() -> None:
    records: list[Dict[str, JSON]] = [
        {"roundtrip_status": "equal", "status": "import_error",
         "primary_errors": ["bad"], "roundtrip_difference_patterns": []},
        {"roundtrip_status": "different", "status": "loaded_without_errors",
         "primary_errors": [], "roundtrip_difference_patterns": ["removed /layers"]},
    ]
    assert summarize(records)["roundtrip_by_import"] == {
        "equal": {"import_error": 1}, "different": {"loaded_without_errors": 1}}
