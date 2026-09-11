"""Audit every current corpus file; preserve provenance and structured evidence."""
from __future__ import annotations

import csv
import hashlib
import importlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPEC = ROOT / "docs/FC_INPUT_FORMAT.md"
CSV = ROOT / "work/1_2_2026-09-11_test_summary.csv"
DOMAINS = ("document", "mesh", "materials", "conditions")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reject_constant(value: str) -> object:
    raise ValueError("Недопустимая JSON-константа: " + value)


def no_duplicates(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Повтор JSON-ключа: " + key)
        result[key] = value
    return result


def main() -> None:
    modules = {name: importlib.import_module("audit_" + name) for name in DOMAINS}
    with CSV.open(encoding="utf-8-sig", newline="") as stream:
        previous = list(csv.DictReader(stream))
    previous_map = {row["Файл"]: row for row in previous}
    files = sorted((ROOT / "data/fc_core_tests").rglob("*.fc"))
    assert len(files) == len(previous_map) == 1130
    records: List[dict] = []
    severity_counts: Counter = Counter()
    rule_counts: Counter = Counter()
    statuses: Counter = Counter()
    started = datetime.now(timezone.utc).isoformat()
    for path in files:
        name = str(path.relative_to(ROOT / "data/fc_core_tests"))
        digest = sha(path)
        assert digest == previous_map[name]["SHA256"], "Stale previous results: " + name
        findings: List[dict] = []
        completed = []
        try:
            data = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant, object_pairs_hook=no_duplicates)
            if not isinstance(data, dict):
                raise ValueError("Корень JSON должен быть объектом")
        except (UnicodeError, ValueError) as exc:
            findings.append(dict(rule="JSON.INVALID", severity="violation", path="$", message=str(exc), actual="invalid JSON", expected="UTF-8 JSON object", spec="docs/FC_INPUT_FORMAT.md:11"))
        else:
            for domain, module in modules.items():
                try:
                    result = module.audit(data)
                    for f in result:
                        assert set(f) == {"rule", "severity", "path", "message", "actual", "expected", "spec"}, f
                        assert f["severity"] in {"violation", "legacy", "ambiguity"}, f
                        assert f["path"].startswith("$"), f
                        assert f["spec"].startswith("docs/FC_INPUT_FORMAT.md:"), f
                        if "UNKNOWN" in f["rule"] and isinstance(f["expected"], list):
                            f["expected"] = "Документированные поля/секции: см. указанный раздел спецификации"
                        json.dumps(f, ensure_ascii=False, allow_nan=False)
                        f["domain"] = domain
                    findings.extend(result)
                    completed.append(domain)
                except Exception as exc:
                    findings.append(dict(rule="AUDIT.INTERNAL", severity="check_error", path="$", message=type(exc).__name__ + ": " + str(exc), actual=domain, expected="Завершение проверки раздела", spec="docs/FC_INPUT_FORMAT.md:1", domain=domain))
        # Do not multiply identical findings from separate loops.
        unique = {json.dumps(f, sort_keys=True, ensure_ascii=False): f for f in findings}
        findings = sorted(unique.values(), key=lambda f: (f["severity"], f["path"], f["rule"]))
        counts = Counter(f["severity"] for f in findings)
        status = ("Проверка не завершена" if counts["check_error"] or len(completed) != 4 else
                  "Выявлены нарушения" if counts["violation"] else
                  "Нарушений не выявлено; есть legacy/неясности" if counts["legacy"] or counts["ambiguity"] else
                  "Нарушений не выявлено по выполненным правилам")
        statuses[status] += 1
        severity_counts.update(counts)
        rule_counts.update(set(f["rule"] for f in findings))
        records.append(dict(file=name, sha256=digest, status=status, completed_domains=completed,
                            counts={s: counts[s] for s in ("violation", "legacy", "ambiguity", "check_error")}, findings=findings))
        assert sha(path) == digest
    report = dict(started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                  spec="docs/FC_INPUT_FORMAT.md", spec_sha256=sha(SPEC),
                  previous_csv_sha256=sha(CSV), files_count=len(records), domains=list(DOMAINS),
                  checker_sha256={p.name: sha(p) for p in [HERE / "run_audit.py"] + [HERE / ("audit_" + x + ".py") for x in DOMAINS]},
                  statuses=dict(statuses), finding_counts=dict(severity_counts), files_per_rule=dict(rule_counts.most_common()), files=records)
    (HERE / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("files", "files_per_rule")}, ensure_ascii=False))
    if severity_counts["check_error"]:
        raise SystemExit("Есть внутренние ошибки аудита: исправить до публикации")


if __name__ == "__main__":
    main()
