"""Import and export every FC in isolated Fidesys batch processes.

Operational success and strict input/output JSON equality are independent.
Original files are never overwritten. Run with PYTHONPATH=src:work.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import time

from core_roundtrip import differences, read_json, sha256
from fidesys_import_audit import MARKER, PROBE, parse_output, stop_group

EXPORT_MARKER = "FCMODEL_EXPORT_DONE="


def export_probe(target: Path) -> str:
    command = 'export fidesyscase "' + str(target) + '" overwrite'
    return PROBE + "\n" + "result = cubit.cmd(" + repr(command) + ")\n" + (
        'print("FCMODEL_EXPORT_DONE=" + json.dumps({"errors": cubit.get_error_count(), '
        '"nodes": cubit.get_node_count(), "elements": cubit.get_element_count(), "result": result}))\n'
    )


def parse_stages(output: str) -> dict:
    lines = output.splitlines()
    boundary = next((i for i, line in enumerate(lines) if line.strip().startswith(MARKER)), None)
    imported = parse_output("\n".join(lines if boundary is None else lines[:boundary + 1]))
    exported = parse_output("\n".join([] if boundary is None else lines[boundary + 1:]))
    completion = None
    for line in lines:
        if line.strip().startswith(EXPORT_MARKER):
            value = json.loads(line.strip()[len(EXPORT_MARKER):])
            if not isinstance(value, dict) or not all(type(value.get(k)) is int for k in ("errors", "nodes", "elements")) or type(value.get("result")) is not bool:
                raise ValueError("Malformed export completion marker")
            completion = value
    return dict(import_stage=imported, export_stage=exported, export_completion=completion)


def classify(record: dict) -> str:
    if record["timeout"]:
        return "timeout"
    imported = record["import_stage"]
    done = imported["completion"]
    if done is None:
        return "import_incomplete"
    if imported["errors"] or done["errors"] > 0:
        return "import_error"
    exported = record["export_completion"]
    if exported is None:
        return "export_incomplete"
    if record["returncode"] not in (0, 11):
        return "abnormal_exit"
    if not exported["result"] or exported["errors"] > done["errors"] or record["export_stage"]["errors"]:
        return "export_error"
    if not record["output_valid"]:
        return "invalid_output"
    return "roundtrip_passed"


def run_case(executable: Path, source: Path, entry: dict, output: Path, timeout: float) -> dict:
    name = entry["file"]
    original = source / name
    digest = sha256(original)
    if digest != entry["sha256"]:
        raise ValueError("Stale source: " + name)
    target = output / "exported" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("Refusing to reuse a previous export: " + str(target))
    log = output / "logs" / (name + ".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timed_out = False
    with tempfile.TemporaryDirectory(prefix="fc-fidesys-roundtrip-") as cwd:
        probe = Path(cwd) / "export_fc.py"
        probe.write_text(export_probe(target), encoding="utf-8")
        command = [str(executable), "-nographics", "-batch", "-model", str(original), "-input", str(probe)]
        with log.open("wb") as stream:
            process = subprocess.Popen(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                       stdin=subprocess.DEVNULL, start_new_session=True)
            try:
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    timed_out = True
            finally:
                stop_group(process)
        returncode = process.returncode
    record: dict = dict(file=name, sha256=digest, roundtrip_status=entry["status"],
                  duration_seconds=round(time.monotonic() - started, 3), timeout=timed_out,
                  returncode=returncode, log=log.relative_to(output).as_posix(),
                  output=target.relative_to(output).as_posix(), output_exists=target.exists(),
                  output_valid=False, output_error="", json_status="not_available", differences=[],
                  command=command, **parse_stages(log.read_text(encoding="utf-8", errors="replace")))
    if target.exists():
        record["output_sha256"] = sha256(target)
        record["output_bytes"] = target.stat().st_size
        try:
            after = read_json(target)
            if not isinstance(after, dict) or not isinstance(after.get("header"), dict) or not isinstance(after.get("mesh"), dict):
                raise ValueError("Export lacks FC header/mesh objects")
            mesh = after["mesh"]
            assert isinstance(mesh, dict)
            if not all(type(v) is int and v >= 0 for v in (mesh.get("nodes_count"), mesh.get("elems_count"))):
                raise ValueError("Export lacks valid mesh counts")
            record["output_valid"] = True
            record["output_mesh"] = {k: mesh[k] for k in ("nodes_count", "elems_count")}
            ds = list(differences(read_json(original), after))
            record["differences"] = ds
            record["json_status"] = "different" if ds else "equal"
        except (ValueError, UnicodeError, OSError) as exc:
            record["output_error"] = type(exc).__name__ + ": " + str(exc)
            record["json_status"] = "invalid_output"
    else:
        record["output_error"] = "Exported FC file was not created"
    record["status"] = classify(record)
    record["alive"] = record["status"] == "roundtrip_passed"
    record["source_unchanged"] = sha256(original) == digest
    if not record["source_unchanged"]:
        raise RuntimeError("Source changed during roundtrip: " + name)
    return record


def summarize(records: list) -> dict:
    return dict(counts=dict(Counter(r["status"] for r in records)),
                json_counts=dict(Counter(r["json_status"] for r in records)),
                alive=sum(r["alive"] for r in records),
                exported=sum(r["output_exists"] for r in records),
                cross=dict(Counter(r["roundtrip_status"] + " / " + r["status"] for r in records)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", type=Path, default=Path("/home/antonov/.bin/CAE-Fidesys-8.1/cae-fidesys-8.1"))
    parser.add_argument("--baseline", type=Path, default=Path("work/1_2_2026-09-11_json_cleanup/roundtrip_results.json"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.workers < 1 or args.timeout <= 0:
        parser.error("workers and timeout must be positive")
    baseline_path = args.baseline.resolve()
    baseline = json.loads(baseline_path.read_text())
    source = Path(baseline["source"]).resolve()
    output = args.output.resolve()
    if source == output or source in output.parents:
        parser.error("Output must be outside the source corpus")
    if output.exists() and not args.resume:
        parser.error("Output exists; use a fresh directory or --resume")
    entries = baseline["files"]
    if args.only:
        entries = [e for e in entries if e["file"] in args.only]
        if len(entries) != len(set(args.only)):
            parser.error("Unknown --only filename")
    expected = {e["file"]: e for e in entries}
    executable = args.executable.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / "checkpoint.jsonl"
    metadata = dict(started_utc=datetime.now(timezone.utc).isoformat(), baseline=str(baseline_path),
                    baseline_sha256=sha256(baseline_path), source=str(source), selected_files=len(entries),
                    executable=str(executable), executable_sha256=sha256(executable),
                    importer_sha256=sha256(executable.parent / "preprocessor/bin/fidesysl"),
                    checker_sha256=sha256(Path(__file__)), workers=args.workers, timeout_seconds=args.timeout)
    records = []
    if args.resume:
        prior = json.loads((output / "metadata.json").read_text())
        for key in ("baseline_sha256", "executable_sha256", "importer_sha256", "checker_sha256", "selected_files"):
            if prior[key] != metadata[key]:
                parser.error("Resume metadata changed: " + key)
        metadata = prior
        if checkpoint.exists():
            records = [json.loads(line) for line in checkpoint.read_text().splitlines() if line]
        for r in records:
            if r["file"] not in expected or r["sha256"] != sha256(source / r["file"]):
                parser.error("Resume source changed")
            if r["output_exists"] and sha256(output / r["output"]) != r["output_sha256"]:
                parser.error("Resume export changed")
    else:
        (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    completed = {r["file"] for r in records}
    if len(completed) != len(records):
        parser.error("Duplicate checkpoint")
    with checkpoint.open("a", encoding="utf-8") as stream:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_case, executable, source, e, output, args.timeout) for e in entries if e["file"] not in completed]
            for future in as_completed(futures):
                record = future.result()
                records.append(record)
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                stream.flush()
                if len(records) % 25 == 0 or len(records) == len(entries):
                    print(str(len(records)) + "/" + str(len(entries)) + ": " + json.dumps(summarize(records)), flush=True)
    records.sort(key=lambda r: r["file"])
    result = dict(metadata, finished_utc=datetime.now(timezone.utc).isoformat(), **summarize(records), files=records)
    (output / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
