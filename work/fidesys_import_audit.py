"""Correlate original FC imports in Fidesys with the strict roundtrip baseline.

Uses the installed launcher's -model path in documented headless batch mode.
Each import has a separate process group, cwd, timeout, log, and completion probe.
Run with PYTHONPATH=src:work. The package and original models are never edited.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, cast

from core_roundtrip import JSON, sha256

MARKER = "FCMODEL_IMPORT_DONE="
PROBE = '''import cubit
import json
print("FCMODEL_IMPORT_DONE=" + json.dumps({"errors": cubit.get_error_count(), "nodes": cubit.get_node_count(), "elements": cubit.get_element_count(), "version": cubit.get_version()}))
'''
GENERIC_ERRORS = {"Command Failed.", "Errors found during session."}


def parse_output(output: str) -> Dict[str, JSON]:
    errors: List[str] = []
    warnings: List[str] = []
    completion: Optional[Dict[str, JSON]] = None
    for raw in output.splitlines():
        line = re.sub(r"\x1b\[[0-9;]*m", "", raw).strip()
        if line.startswith(MARKER):
            parsed = json.loads(line[len(MARKER):])
            if not isinstance(parsed, dict) or not all(
                isinstance(parsed.get(key), int) for key in ("errors", "nodes", "elements")
            ):
                raise ValueError("Malformed completion probe")
            completion = cast(Dict[str, JSON], parsed)
        match = re.match(r"^(?:\[[^\]]+\]\s*)?\[(error|warning|critical)\]\s*(.*)$", line, re.I)
        plain = re.match(r"^(ERROR|WARNING|FATAL):\s*(.*)$", line, re.I)
        if match or plain:
            found = match if match is not None else plain
            assert found is not None
            target = warnings if found.group(1).lower() == "warning" else errors
            message = found.group(2).strip()
            if message not in target:
                target.append(message)
        elif line.startswith("Fontconfig warning:") and line not in warnings:
            warnings.append(line)
    return {"errors": cast(List[JSON], errors), "warnings": cast(List[JSON], warnings),
            "primary_errors": cast(List[JSON], [e for e in errors if e not in GENERIC_ERRORS]),
            "completion": completion}


def classify(parsed: Dict[str, JSON], timed_out: bool, returncode: int) -> str:
    if timed_out:
        return "timeout"
    completion = parsed["completion"]
    if completion is None:
        return "incomplete"
    if returncode not in (0, 11):
        # Both positive and negative controls exit 11 with this installed launcher.
        return "abnormal_exit"
    assert isinstance(completion, dict)
    if parsed["errors"] or cast(int, completion["errors"]) > 0:
        return "import_error"
    return "loaded_without_errors"


def stop_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    # Also stop descendants if the launcher exited before them.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def run_import(executable: Path, source: Path, entry: Dict[str, JSON],
               output_dir: Path, timeout: float) -> Dict[str, JSON]:
    name = str(entry["file"])
    path = source / name
    checksum = sha256(path)
    if checksum != entry["sha256"]:
        raise ValueError("Source differs from roundtrip baseline: " + name)
    started = time.monotonic()
    log = output_dir / "logs" / (name + ".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    with tempfile.TemporaryDirectory(prefix="fc-fidesys-import-") as cwd:
        probe = Path(cwd) / "after_import.py"
        probe.write_text(PROBE, encoding="utf-8")
        command = [str(executable), "-nographics", "-batch", "-model", str(path),
                   "-input", str(probe)]
        with log.open("wb") as stream:
            process = subprocess.Popen(command, cwd=cwd, stdout=stream,
                                       stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                       start_new_session=True)
            try:
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
            finally:
                stop_group(process)
        returncode = process.returncode
    output = log.read_text(encoding="utf-8", errors="replace")
    parsed = parse_output(output)
    status = classify(parsed, timed_out, returncode)
    unchanged = checksum == sha256(path)
    if not unchanged:
        raise RuntimeError("Original model changed during import: " + name)
    result: Dict[str, JSON] = {
        "file": name, "sha256": checksum, "source_unchanged": unchanged,
        "roundtrip_status": entry["status"], "status": status,
        "duration_seconds": round(time.monotonic() - started, 3),
        "returncode": returncode, "timeout": timed_out,
        "log": log.relative_to(output_dir).as_posix(), "command": cast(List[JSON], command),
        **parsed,
    }
    for key in ("stage", "error_type", "error", "location"):
        if key in entry:
            result["roundtrip_" + key] = entry[key]
    signatures = sorted({str(d["kind"]) + " " + re.sub(r"/\d+(?=/|$)", "/*", str(d["path"]))
                         for d in cast(List[Dict[str, JSON]], entry.get("differences", []))})
    result["roundtrip_difference_patterns"] = cast(List[JSON], signatures)
    return result


def summarize(records: List[Dict[str, JSON]]) -> Dict[str, JSON]:
    counts: Counter[str] = Counter()
    cross: Dict[str, Counter[str]] = defaultdict(Counter)
    messages: Dict[str, Counter[str]] = defaultdict(Counter)
    patterns: Dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        status = str(record["status"])
        rt = str(record["roundtrip_status"])
        counts[status] += 1
        cross[rt][status] += 1
        for message in cast(List[str], record["primary_errors"]):
            messages[message][rt] += 1
        for pattern in cast(List[str], record["roundtrip_difference_patterns"]):
            patterns[pattern][status] += 1
    return {"counts": dict(counts),
            "roundtrip_by_import": {k: dict(v) for k, v in cross.items()},
            "primary_errors_by_roundtrip": {k: dict(v) for k, v in sorted(
                messages.items(), key=lambda item: (-sum(item[1].values()), item[0]))},
            "roundtrip_patterns_by_import": {k: dict(v) for k, v in sorted(patterns.items())}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, default=Path(
        "/home/antonov/.bin/CAE-Fidesys-8.1/cae-fidesys-8.1"))
    parser.add_argument("--baseline", type=Path, default=Path(
        "work/1_2_2026-09-11_core_roundtrip_results.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.timeout <= 0:
        parser.error("workers and timeout must be positive")
    baseline_path = cast(Path, args.baseline).resolve()
    baseline = cast(Dict[str, JSON], json.loads(baseline_path.read_text(encoding="utf-8")))
    source = Path(str(baseline["source"]))
    output_dir = cast(Path, args.output).resolve()
    if output_dir == source or source in output_dir.parents:
        parser.error("Output must be outside the source corpus")
    if output_dir.exists() and not args.resume:
        parser.error("Output exists; choose a new directory or use --resume")
    entries = cast(List[Dict[str, JSON]], baseline["files"])
    if args.only:
        selected = set(cast(List[str], args.only))
        entries = [entry for entry in entries if entry["file"] in selected]
        if len(entries) != len(selected):
            parser.error("Some --only names are absent from the baseline")
    expected = {str(e["file"]): e for e in entries}
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / "checkpoint.jsonl"
    records: List[Dict[str, JSON]] = []
    if args.resume and checkpoint.exists():
        records = [cast(Dict[str, JSON], json.loads(line))
                   for line in checkpoint.read_text(encoding="utf-8").splitlines() if line]
        for record in records:
            name = str(record["file"])
            if name not in expected or record["sha256"] != sha256(source / name):
                parser.error("Resume source or selection differs from checkpoint")
    completed = {str(r["file"]) for r in records}
    if len(completed) != len(records):
        parser.error("Duplicate checkpoint entries")
    executable = cast(Path, args.executable).resolve()
    metadata: Dict[str, JSON] = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "baseline": str(baseline_path), "baseline_sha256": sha256(baseline_path),
        "executable": str(executable), "executable_sha256": sha256(executable),
        "source": str(source), "workers": args.workers, "timeout_seconds": args.timeout,
        "probe": PROBE, "selected_files": len(entries),
    }
    if not args.resume:
        (output_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with checkpoint.open("a", encoding="utf-8") as journal:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_import, executable, source, entry, output_dir, args.timeout)
                       for entry in entries if str(entry["file"]) not in completed]
            for future in as_completed(futures):
                record = future.result()
                records.append(record)
                journal.write(json.dumps(record, ensure_ascii=False) + "\n")
                journal.flush()
                if len(records) % 25 == 0 or len(records) == len(entries):
                    print(f"{len(records)}/{len(entries)}: " + json.dumps(
                        summarize(records)["counts"], ensure_ascii=False), flush=True)
    records.sort(key=lambda r: str(r["file"]))
    result: Dict[str, JSON] = {
        **metadata, "finished_utc": datetime.now(timezone.utc).isoformat(),
        **summarize(records), "files": cast(List[JSON], records),
    }
    (output_dir / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["roundtrip_by_import"], ensure_ascii=False), flush=True)
    return int(any(r["status"] != "loaded_without_errors" for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
