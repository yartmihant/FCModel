"""Recompare existing Fidesys exports using the owner's explicit exclusions."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "work"))
from core_roundtrip import JSON, differences, read_json, sha256
from fidesys_roundtrip_audit import classify

ENTITY_SECTIONS = {
    "blocks", "materials", "property_tables", "coordinate_systems", "loads",
    "restraints", "initial_sets", "contact_constraints", "coupling_constraints",
    "periodic_constraints", "receivers", "orientations", "imported_sections",
    "contacts", "bcs", "load_sets", "restraint_sets",
}


def normalize(value: JSON, path: tuple = ()) -> JSON:
    if isinstance(value, dict):
        entity = (len(path) == 2 and path[0] in ENTITY_SECTIONS and isinstance(path[1], int)) or (
            len(path) == 3 and path[0] == "sets" and path[1] in {"nodesets", "sidesets"}
            and isinstance(path[2], int)
        )
        return {k: normalize(v, path + (k,)) for k, v in value.items()
                if not (not path and k in {"settings", "header"}) and not (entity and k == "name")}
    if isinstance(value, list):
        return [normalize(v, path + (i,)) for i, v in enumerate(value)]
    return value


def analytical_diff(diff: dict) -> dict:
    # Hashes belong in provenance, not in analytical CSV cells.
    return {k: {x: y for x, y in v.items() if x != "sha256"} if isinstance(v, dict) else v
            for k, v in diff.items()}


def warnings(stage: dict) -> list:
    return [w for w in stage["warnings"]
            if w.strip().rstrip(".") != "The distance between nodesets is not accurate"]


def main() -> None:
    run = ROOT / "work/1_2_2026-09-11_fidesys_roundtrip"
    report = json.loads((run / "results.json").read_text())
    old_csv = ROOT / "work/1_2_2026-09-11_test_summary.csv"
    source = ROOT / "data/fc_core_tests"
    assert sorted(r["file"] for r in report["files"]) == sorted(p.relative_to(source).as_posix() for p in source.rglob("*.fc"))
    records = []
    hashes = {}
    for r in sorted(report["files"], key=lambda x: x["file"]):
        original = source / r["file"]
        assert sha256(original) == r["sha256"], "Stale original: " + r["file"]
        a = read_json(original)
        assert isinstance(a, dict) and isinstance(a["mesh"], dict)
        target = run / r["output"]
        assert target.exists() == r["output_exists"]
        if target.exists():
            assert sha256(target) == r["output_sha256"], "Stale export: " + r["file"]
        hashes[r["file"]] = {"source": r["sha256"], "export": r.get("output_sha256")}
        ds = None
        if r["output_valid"]:
            b = read_json(target)
            assert isinstance(b, dict) and isinstance(b["mesh"], dict)
            assert {k: b["mesh"][k] for k in ("nodes_count", "elems_count")} == r["output_mesh"]
            ds = [analytical_diff(d) for d in differences(normalize(a), normalize(b))]
        cycle = classify(r)
        assert cycle == r["status"]
        status = ("Пройден" if ds == [] else "Расхождения JSON") if cycle == "roundtrip_passed" else {
            "import_error": "Ошибка импорта", "import_incomplete": "Импорт не завершён",
            "export_error": "Ошибка экспорта", "export_incomplete": "Экспорт не завершён",
            "invalid_output": "Некорректный выходной FC", "abnormal_exit": "Аварийное завершение",
            "timeout": "Таймаут",
        }[cycle]
        imported, exported = r["import_stage"]["completion"], r["export_completion"]
        mesh_out = r.get("output_mesh")
        mesh_in = a["mesh"]
        counts = [mesh_in.get("nodes_count"), imported["nodes"] if imported else None,
                  mesh_out["nodes_count"] if mesh_out else None,
                  mesh_in.get("elems_count"), imported["elements"] if imported else None,
                  mesh_out["elems_count"] if mesh_out else None]
        known_mismatch = any(v is not None and v != counts[base] for base in (0, 3) for v in counts[base + 1:base + 3])
        count_status = "Нет" if known_mismatch else "Неизвестно" if None in counts else "Да"
        records.append(dict(
            file=r["file"], status=status,
            json_status=("Совпадает" if ds == [] else "Различается") if ds is not None else
                        "Некорректный выходной FC" if target.exists() else "Нет экспорта",
            differences=ds, import_done=imported is not None, export_done=exported is not None,
            import_errors=r["import_stage"]["errors"], export_errors=r["export_stage"]["errors"],
            import_warnings=warnings(r["import_stage"]), export_warnings=warnings(r["export_stage"]),
            output_error=r["output_error"], counts=counts, counts_equal=count_status,
        ))
    assert len(records) == 1130
    result = dict(source_run="2026-09-11", evaluated="2026-09-28", files=records,
                  counts=dict(Counter(r["status"] for r in records)),
                  json_counts=dict(Counter(r["json_status"] for r in records)),
                  old_summary_sha256=sha256(old_csv), hashes=hashes)
    (HERE / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("counts", "json_counts")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
