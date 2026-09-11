"""Strict diagnostic FCModel.load/save audit; run with PYTHONPATH=src.

Outputs must be outside the input corpus. Exit 1 means corpus failures;
exit 2 means missing input. No tolerances or legacy-field normalization.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import traceback
from typing import Dict, Iterator, List, Tuple, Union, cast

from fc_model import FCModel

JSON = Union[None, bool, int, float, str, List["JSON"], Dict[str, "JSON"]]


def unique_object(pairs: List[Tuple[str, JSON]]) -> Dict[str, JSON]:
    result: Dict[str, JSON] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("Invalid JSON number: " + value)


def read_json(path: Path) -> JSON:
    return cast(JSON, json.loads(path.read_text(encoding="utf-8"),
                                object_pairs_hook=unique_object,
                                parse_constant=reject_constant))


def preview(value: JSON) -> JSON:
    if isinstance(value, str) and len(value) > 160:
        return {"prefix": value[:120], "length": len(value),
                "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest()}
    if isinstance(value, (dict, list)):
        return {"type": type(value).__name__, "length": len(value)}
    return value


def differences(before: JSON, after: JSON, path: str = "") -> Iterator[Dict[str, JSON]]:
    if type(before) is not type(after):
        yield {"path": path, "kind": "type_changed", "before": preview(before),
               "after": preview(after), "before_type": type(before).__name__,
               "after_type": type(after).__name__}
    elif isinstance(before, dict):
        other = cast(Dict[str, JSON], after)
        for key in sorted(before.keys() | other.keys()):
            child = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in other:
                yield {"path": child, "kind": "removed", "before": preview(before[key])}
            elif key not in before:
                yield {"path": child, "kind": "added", "after": preview(other[key])}
            else:
                yield from differences(before[key], other[key], child)
    elif isinstance(before, list):
        other_list = cast(List[JSON], after)
        if len(before) != len(other_list):
            yield {"path": path, "kind": "length_changed",
                   "before": len(before), "after": len(other_list)}
        for index in range(min(len(before), len(other_list))):
            yield from differences(before[index], other_list[index], path + "/" + str(index))
    elif before != after:
        yield {"path": path, "kind": "value_changed",
               "before": preview(before), "after": preview(after)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_file(source: Path, output: Path, relative: str) -> Dict[str, JSON]:
    original_hash = sha256(source)
    result: Dict[str, JSON] = {"file": relative, "sha256": original_hash,
                               "bytes": source.stat().st_size}
    stage = "input_json"
    try:
        before = read_json(source)
        if isinstance(before, dict):
            result["header"] = before.get("header")
        stage = "load"
        model = FCModel.load(str(source))
        stage = "save"
        output.parent.mkdir(parents=True, exist_ok=True)
        model.save(str(output))
        stage = "output_json"
        after = read_json(output)
        stage = "compare"
        diffs = list(differences(before, after))
        result.update(status="different" if diffs else "equal",
                      differences=cast(List[JSON], diffs), output=str(output))
    except Exception as exc:
        frames = traceback.extract_tb(exc.__traceback__)
        last = frames[-1]
        result.update(status="error", stage=stage, error_type=type(exc).__name__,
                      error=str(exc), location=f"{Path(last.filename).name}:{last.lineno}",
                      traceback=traceback.format_exc())
    result["source_unchanged"] = original_hash == sha256(source)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("data/fc_core_tests"))
    parser.add_argument("--outputs", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    source = cast(Path, args.source).resolve()
    outputs = cast(Path, args.outputs).resolve()
    report = cast(Path, args.report).resolve()
    if outputs == source or source in outputs.parents:
        parser.error("--outputs must be outside --source")
    if report == source or source in report.parents:
        parser.error("--report must be outside --source")
    if outputs.exists():
        parser.error("--outputs must be a new directory (no overwrites)")
    files = sorted(p for p in source.rglob("*") if p.is_file() and p.suffix.lower() == ".fc")
    if not files:
        print("No .fc files found", file=sys.stderr)
        return 2
    started = datetime.now(timezone.utc).isoformat()
    results: List[JSON] = []
    counts: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    patterns: Counter[str] = Counter()
    for index, path in enumerate(files, 1):
        relative = path.relative_to(source)
        result = audit_file(path, outputs / relative, relative.as_posix())
        results.append(result)
        counts[str(result["status"])] += 1
        if result["status"] == "error":
            errors[f'{result["stage"]}: {result["error_type"]}: {result["error"]} @ {result["location"]}'] += 1
        else:
            # Count affected files, not occurrences of repeating array members.
            signatures = {str(d["kind"]) + " " + re.sub(r"/\d+(?=/|$)", "/*", str(d["path"]))
                          for d in cast(List[Dict[str, JSON]], result["differences"])}
            patterns.update(signatures)
        if index % 100 == 0 or index == len(files):
            print(f"{index}/{len(files)}: {dict(counts)}", flush=True)
    payload: Dict[str, JSON] = {
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "source": str(source), "outputs": str(outputs),
        "comparison": "Strict parsed JSON types/values; object key order ignored; array order preserved",
        "total": len(files), "counts": dict(counts),
        "error_groups": dict(errors.most_common()),
        "difference_patterns_files": dict(patterns.most_common()), "files": results,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if counts["different"] or counts["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
