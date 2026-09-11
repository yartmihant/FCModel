"""Independently reconcile the revised CSV and permitted finding removals."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASELINE = "4bd5f2284613be67284c238e595ea37b66db3ee6"
SPEC_REPORT = "work/1_2_2026-09-11_spec_audit/results.json"
CSV_PATH = "work/1_2_2026-09-11_test_summary.csv"
sys.path.insert(0, str(ROOT / "work"))
from fidesys_import_audit import parse_output


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def previous(path: str) -> str:
    return subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT).decode("utf-8-sig")


def signature(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def value_at(data: dict, path: str) -> object:
    value = data
    for key, index in re.findall(r"\.([^\.\[\]]+)|\[(\d+)\]", path[1:]):
        value = value[int(index)] if index else value[key]
    return value


def main() -> None:
    old = {r["file"]: r for r in json.loads(previous(SPEC_REPORT))["files"]}
    spec = read(SPEC_REPORT)
    new = {r["file"]: r for r in spec["files"]}
    old_csv = {r["Файл"]: r for r in csv.DictReader(io.StringIO(previous(CSV_PATH)))}
    with (ROOT / CSV_PATH).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len({r["Файл"] for r in rows}) == 1130
    assert all(len(row) == 33 and None not in row for row in rows)
    assert set(old) == set(new) == set(old_csv) == {r["Файл"] for r in rows}
    assert (ROOT / "docs/FC_INPUT_FORMAT.md").read_text() == (ROOT / "src/fc_model/FC_INPUT_FORMAT.md").read_text()
    assert hashlib.sha256((ROOT / spec["spec"]).read_bytes()).hexdigest() == spec["spec_sha256"]
    for name, digest in spec["checker_sha256"].items():
        assert hashlib.sha256((ROOT / "work/1_2_2026-09-11_spec_audit" / name).read_bytes()).hexdigest() == digest
    fi = {}
    for path in ["work/1_2_2026-09-11_fidesys_import/results.json", "work/1_2_2026-09-11_json_cleanup/fidesys/results.json"]:
        fi.update({r["file"]: dict(r, report_path=path) for r in read(path)["files"]})
    removed: Counter = Counter()
    retained = 0
    sizes: Counter = Counter()
    warning_files: Counter = Counter()
    mismatch_files = []
    columns = list(rows[0])
    assert columns[columns.index("Fidesys_загружено_элементов") + 1] == "Fidesys_разница_с_числами_JSON"
    assert not any(len({row[k] for row in rows}) == 1 for k in columns)
    for row in rows:
        name = row["Файл"]
        source = ROOT / "data/fc_core_tests" / name
        data = json.loads(source.read_text())
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest == old[name]["sha256"] == new[name]["sha256"] == fi[name]["sha256"]
        before = {signature(f): f for f in old[name]["findings"]}
        after = {signature(f): f for f in new[name]["findings"]}
        assert after.keys() <= before.keys(), (name, "Unexpected new/modified finding")
        retained += len(after)
        for key in before.keys() - after.keys():
            finding = before[key]
            rule, path = finding["rule"], finding["path"]
            allowed = rule in {"DOC.DIMENSIONS_CONFLICT", "MESH.BINARY_SEMANTICS_UNCHECKED", "MAT.GROUP_CARDINALITY"}
            if rule in {"MESH.ARRAY_SIZE", "MESH.BUFFER_SIZE"}:
                allowed = path == "$.mesh.elem_types"
            elif rule == "SET.EXCLUSIVE":
                allowed = path in {"$.settings.statics", "$.settings.dynamics"} and finding["actual"] == []
            elif rule == "SET.ENUM":
                allowed = path == "$.settings.eigen_solver.solver" and value_at(data, path) == "auto"
            elif rule in {"PT.PROPERTY_FIELD", "DOC.FIELD_TYPE"}:
                value = value_at(data, path)
                allowed = isinstance(value, float) and value.is_integer() and (finding["expected"] == "int" or "int" in str(finding["expected"]))
            assert allowed, (name, finding)
            removed[rule] += 1
        record = new[name]
        assert json.loads(row["Спецификация_подробности_JSON"]) == record["findings"]
        for severity, column in [("violation", "нарушений"), ("legacy", "legacy"), ("ambiguity", "неясностей")]:
            assert int(row["Спецификация_" + column]) == record["counts"][severity]
        assert row["Спецификация_статус"] == record["status"]
        for column in columns:
            if column in old_csv[name] and not column.startswith("Спецификация_") and column not in {
                "Fidesys_статус", "Fidesys_предупреждения", "Fidesys_уникальных_предупреждений", "Fidesys_пояснение"
            }:
                assert row[column] == old_csv[name][column], (name, column)
        f = fi[name]
        warnings = [w for w in f["warnings"] if w not in {
            "The distance between nodesets is not accurate", "The distance between nodesets is not accurate."
        }]
        assert row["Fidesys_предупреждения"] == " | ".join(warnings)
        assert int(row["Fidesys_уникальных_предупреждений"]) == len(warnings)
        warning_files["ignored_in_files"] += len(warnings) != len(f["warnings"])
        warning_files["remaining_warning_files"] += bool(warnings)
        if f["status"] == "loaded_without_errors":
            expected_status = "Без ошибок, с предупреждениями" if warnings else "Без ошибок и предупреждений"
            assert row["Fidesys_статус"] == expected_status
            warning_files["loaded_with_remaining_warnings"] += bool(warnings)
            warning_files["loaded_without_remaining_warnings"] += not warnings
        log = ROOT / Path(f["report_path"]).parent / f["log"]
        parsed = parse_output(log.read_text(errors="replace"))
        assert parsed["warnings"] == warnings, name
        assert parsed["errors"] == f["errors"], name
        assert parsed["completion"] == f["completion"], name
        completion = f["completion"]
        mismatch = []
        if completion is None:
            assert row["Fidesys_разница_с_числами_JSON"].startswith("Неизвестно;")
            sizes["unknown"] += 1
        else:
            for key, counter, label in [("nodes_count", "nodes", "узлы"), ("elems_count", "elements", "элементы")]:
                expected, actual = data["mesh"][key], completion[counter]
                if expected != actual:
                    mismatch.append(f"{label}: JSON={expected}, Fidesys={actual}")
            expected_comparison = "Да; " + "; ".join(mismatch) if mismatch else "Нет"
            assert row["Fidesys_разница_с_числами_JSON"] == expected_comparison
            sizes["different" if mismatch else "equal"] += 1
            if mismatch:
                mismatch_files.append({"file": name, "comparison": expected_comparison, "fidesys_status": f["status"]})
    report = dict(rows=len(rows), columns=len(columns), baseline_commit=BASELINE,
                  removed_findings=dict(removed), retained_findings_unchanged=retained,
                  spec_statuses=spec["statuses"], mesh_comparisons=dict(sizes),
                  warning_files=dict(warning_files), mismatch_files=mismatch_files,
                  source_hashes_verified=1130, original_logs_reparsed=1130,
                  removed_columns=sorted(set(next(iter(old_csv.values()))) - set(columns)),
                  csv_sha256=hashlib.sha256((ROOT / CSV_PATH).read_bytes()).hexdigest())
    (HERE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "mismatch_files"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
