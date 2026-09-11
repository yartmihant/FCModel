"""Reconcile every original, export, stage log and published CSV row."""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "work"))
from core_roundtrip import read_json, sha256
from fidesys_import_audit import parse_output


def main() -> None:
    report = json.loads((HERE / "results.json").read_text())
    prior = json.loads((HERE / "previous_analysis_hashes.json").read_text())
    csv_path = ROOT / "work/1_2_2026-09-11_test_summary.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    matrix = {r["Файл"]: r for r in rows}
    assert len(rows) == len(matrix) == len(report["files"]) == 1130
    assert all(None not in r for r in rows)
    counts: Counter = Counter()
    live_json: Counter = Counter()
    live_spec: Counter = Counter()
    live = []
    exports = invalid = live_count_mismatch = 0
    old_import = {}
    for path in ["work/1_2_2026-09-11_fidesys_import/results.json", "work/1_2_2026-09-11_json_cleanup/fidesys/results.json"]:
        old_import.update({r["file"]: r for r in json.loads((ROOT / path).read_text())["files"]})
    newly_failed = []
    for r in report["files"]:
        name = r["file"]
        row = matrix[name]
        original = ROOT / "data/fc_core_tests" / name
        before = read_json(original)
        assert isinstance(before, dict) and isinstance(before["mesh"], dict)
        original_mesh = before["mesh"]
        assert sha256(original) == r["sha256"] == old_import[name]["sha256"]
        assert r["source_unchanged"]
        untouched = {k: row[k] for k in prior["columns"]}
        assert hashlib.sha256(json.dumps(untouched, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == prior["rows"][name]
        text = (HERE / r["log"]).read_text(errors="replace")
        import_lines = [line for line in text.splitlines() if line.startswith("FCMODEL_IMPORT_DONE=")]
        export_lines = [line for line in text.splitlines() if line.startswith("FCMODEL_EXPORT_DONE=")]
        imported = json.loads(import_lines[0].split("=", 1)[1]) if import_lines else None
        exported = json.loads(export_lines[0].split("=", 1)[1]) if export_lines else None
        assert len(import_lines) <= 1 and len(export_lines) <= 1
        assert imported == r["import_stage"]["completion"]
        assert exported == r["export_completion"]
        parsed = parse_output(text)
        errors = list(dict.fromkeys(r["import_stage"]["errors"] + r["export_stage"]["errors"]))
        warnings = list(dict.fromkeys(r["import_stage"]["warnings"] + r["export_stage"]["warnings"]))
        assert parsed["errors"] == errors and parsed["warnings"] == warnings
        assert row["Fidesys_ошибки"] == " | ".join(errors)
        assert row["Fidesys_предупреждения"] == " | ".join(warnings)
        assert int(row["Fidesys_уникальных_предупреждений"]) == len(warnings)
        assert int(row["Fidesys_уникальных_сообщений_ошибок"]) == len(errors)
        assert row["Fidesys_ошибки_импорта"] == " | ".join(r["import_stage"]["errors"])
        assert row["Fidesys_ошибки_экспорта"] == " | ".join(r["export_stage"]["errors"])
        assert row["Fidesys_импорт_завершён"] == ("Да" if imported else "Нет")
        assert row["Fidesys_экспорт_завершён"] == ("Да" if exported else "Нет")
        assert row["Fidesys_ошибок_по_API"] == (str(exported["errors"]) if exported else "")
        mismatches = []
        for key, counter, label, column in [
            ("nodes_count", "nodes", "узлы", "Fidesys_загружено_узлов"),
            ("elems_count", "elements", "элементы", "Fidesys_загружено_элементов"),
        ]:
            assert row[column] == (str(imported[counter]) if imported else "")
            if imported is not None and original_mesh[key] != imported[counter]:
                mismatches.append(f"{label}: JSON={original_mesh[key]}, Fidesys={imported[counter]}")
        if imported is None:
            assert row["Fidesys_разница_с_числами_JSON"].startswith("Неизвестно;")
        else:
            assert row["Fidesys_разница_с_числами_JSON"] == ("Да; " + "; ".join(mismatches) if mismatches else "Нет")
        valid = False
        target = HERE / r["output"]
        assert target.exists() == r["output_exists"]
        if target.exists():
            exports += 1
            assert sha256(target) == r["output_sha256"]
            try:
                output = read_json(target)
                valid = isinstance(output, dict) and isinstance(output.get("header"), dict) and isinstance(output.get("mesh"), dict)
                if valid:
                    assert isinstance(output, dict)
                    mesh = output["mesh"]
                    assert isinstance(mesh, dict)
                    valid = all(type(v) is int and v >= 0 for v in (mesh.get("nodes_count"), mesh.get("elems_count")))
                    if valid:
                        assert r["output_mesh"] == {k: mesh[k] for k in ("nodes_count", "elems_count")}
                if valid:
                    expected_json = "equal" if json.dumps(read_json(original), sort_keys=True) == json.dumps(output, sort_keys=True) else "different"
                    assert r["json_status"] == expected_json
            except (ValueError, UnicodeError):
                assert r["json_status"] == "invalid_output"
            invalid += not valid
        assert valid == r["output_valid"]
        assert row["Fidesys_выход_FC_валиден"] == ("Да" if valid else "Нет")
        if valid:
            if r["differences"]:
                assert json.loads(row["Fidesys_JSON_подробности"]) == r["differences"]
            else:
                assert row["Fidesys_JSON_подробности"] == ""
            assert int(row["Fidesys_JSON_число_расхождений"]) == len(r["differences"])
            assert row["Fidesys_экспорт_узлов"] == str(r["output_mesh"]["nodes_count"])
            assert row["Fidesys_экспорт_элементов"] == str(r["output_mesh"]["elems_count"])
        else:
            assert row["Fidesys_JSON_число_расхождений"] == ""
        alive = bool(imported is not None and exported is not None and not errors and imported["errors"] == 0
                     and exported["errors"] == 0 and exported["result"] and valid and not r["timeout"] and r["returncode"] in (0, 11))
        assert alive == r["alive"] == (r["status"] == "roundtrip_passed")
        assert row["Fidesys_живая_модель"] == ("Да" if alive else "Не подтверждено")
        counts[r["status"]] += 1
        if alive:
            live_json[r["json_status"]] += 1
            live_spec[row["Спецификация_статус"]] += 1
            live.append({"file": name, "source_sha256": r["sha256"], "export": r["output"], "export_sha256": r["output_sha256"]})
            assert imported is not None
            live_count_mismatch += (original_mesh["nodes_count"] != imported["nodes"] or original_mesh["elems_count"] != imported["elements"] or r["output_mesh"]["nodes_count"] != imported["nodes"] or r["output_mesh"]["elems_count"] != imported["elements"])
        elif old_import[name]["status"] == "loaded_without_errors":
            newly_failed.append({"file": name, "status": r["status"], "export_errors": r["export_stage"]["errors"], "output_error": r["output_error"]})
    assert dict(counts) == report["counts"]
    result = dict(rows=len(rows), columns=len(rows[0]), counts=dict(counts), alive=len(live),
                  alive_json=dict(live_json), alive_spec_statuses=dict(live_spec),
                  alive_mesh_count_mismatches=live_count_mismatch, exported=exports, invalid_exports=invalid,
                  previous_import_passed_now_failed=newly_failed, unchanged_analysis_columns=prior["columns"],
                  csv_sha256=sha256(csv_path), original_hashes_verified=1130, logs_verified=1130)
    (HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (HERE / "alive_manifest.json").write_text(json.dumps(live, ensure_ascii=False, indent=2) + "\n")
    (HERE / "alive_files.txt").write_text("".join(r["file"] + "\n" for r in live))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
