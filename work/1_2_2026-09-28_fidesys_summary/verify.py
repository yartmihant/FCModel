"""Verify CSV independently, including equality by canonical JSON serialization."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main() -> None:
    report = json.loads((HERE / "results.json").read_text())
    run = ROOT / "work/1_2_2026-09-11_fidesys_roundtrip"
    original_records = {r["file"]: r for r in json.loads((run / "results.json").read_text())["files"]}
    csv_path = HERE.parent / "1_2_2026-09-28_fidesys_roundtrip.csv"
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        headers = reader.fieldnames
    assert headers is not None and len(headers) == 22
    assert len(rows) == len(report["files"]) == len({r["Файл"] for r in rows}) == 1130
    statuses: Counter[str] = Counter()
    compared = 0
    for row, record in zip(rows, report["files"]):
        assert row["Файл"] == record["file"] and None not in row
        assert row["Roundtrip_статус"] == record["status"]
        assert row["JSON_статус"] == record["json_status"]
        ds = record["differences"]
        assert row["Число_различий"] == (str(len(ds)) if ds is not None else "")
        if ds is not None:
            assert json.loads(row["Различия_JSON"]) == ds
        else:
            assert row["Различия_JSON"] == ""
        r = original_records[record["file"]]
        if ds is not None:
            compared += 1
            pair = [json.loads((ROOT / "data/fc_core_tests" / record["file"]).read_text()),
                    json.loads((run / r["output"]).read_text())]
            for data in pair:
                data.pop("header", None)
                data.pop("settings", None)
                # Independent implementation: remove names from known entity arrays directly.
                for key in ("blocks", "materials", "property_tables", "coordinate_systems", "loads",
                            "restraints", "initial_sets", "contact_constraints", "coupling_constraints",
                            "periodic_constraints", "receivers", "orientations", "imported_sections",
                            "contacts", "bcs", "load_sets", "restraint_sets"):
                    collection = data.get(key)
                    if isinstance(collection, list):
                        for entity in collection:
                            if isinstance(entity, dict):
                                entity.pop("name", None)
                if isinstance(data.get("sets"), dict):
                    for key in ("nodesets", "sidesets"):
                        for entity in data["sets"].get(key, []):
                            if isinstance(entity, dict):
                                entity.pop("name", None)
            equal = json.dumps(pair[0], sort_keys=True) == json.dumps(pair[1], sort_keys=True)
            assert equal == (ds == []) == (row["JSON_статус"] == "Совпадает")
            assert (row["Roundtrip_статус"] == "Пройден") == (equal and r["alive"])
            assert all(not d["path"].startswith(("/header", "/settings")) for d in ds)
        for label, field in (("Ошибки", "errors"), ("Предупреждения", "warnings")):
            for stage, suffix in (("import", "импорта"), ("export", "экспорта")):
                assert row[label + "_" + suffix] == "\n".join(record[stage + "_" + field])
        for label, field in (("Импорт", "import"), ("Экспорт", "export")):
            assert row[label + "_завершён"] == ("Да" if record[field + "_done"] else "Нет")
        for col, value in zip(headers[15:21], record["counts"]):
            assert row[col] == (str(value) if value is not None else "")
        assert row["Счётчики_совпадают"] == record["counts_equal"]
        assert row["Ошибка_выходного_FC"] == record["output_error"]
        statuses[row["Roundtrip_статус"]] += 1
    previous = ROOT / "work/1_2_2026-09-11_test_summary.csv"
    assert hashlib.sha256(previous.read_bytes()).hexdigest() == report["old_summary_sha256"]
    assert dict(statuses) == report["counts"]
    result = dict(rows=len(rows), columns=len(headers), counts=dict(statuses),
                  old_summary_unchanged=True, independent_json_comparisons=compared,
                  csv_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest())
    (HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
