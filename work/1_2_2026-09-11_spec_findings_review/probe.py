"""Reproduce frequent specification findings against the public FCModel API."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from typing import cast

import numpy as np
from fc_model import FCModel, FCValue, FCMaterial, FCPropertyTable, FCSrcMaterial, FCSrcPropertyTable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def signature(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def brief(value: object) -> object:
    if isinstance(value, str) and len(value) > 120:
        return {"type": "string", "chars": len(value), "sha256": hashlib.sha256(value.encode()).hexdigest()}
    if isinstance(value, list) and len(value) > 16:
        return {"type": "list", "items": len(value)}
    if isinstance(value, dict):
        return {k: brief(v) for k, v in value.items()}
    if isinstance(value, list):
        return [brief(v) for v in value]
    return value


def value_at(data: dict, path: str) -> object:
    value = data
    for key, index in re.findall(r"\.([^\.\[\]]+)|\[(\d+)\]", path[1:]):
        value = value[int(index)] if index else value[key]
    return brief(value)


def main() -> None:
    report = read("work/1_2_2026-09-11_spec_audit/results.json")
    records = {r["file"]: r for r in report["files"]}
    rt = {r["file"]: r for r in read("work/1_2_2026-09-11_json_cleanup/roundtrip_results.json")["files"]}
    fi = {}
    for p in ("work/1_2_2026-09-11_fidesys_import/results.json", "work/1_2_2026-09-11_json_cleanup/fidesys/results.json"):
        fi.update({r["file"]: r for r in read(p)["files"]})
    rules = ["MESH.ARRAY_SIZE", "MESH.BUFFER_SIZE", "SET.EXCLUSIVE", "DOC.FIELD_TYPE", "MAT.GROUP_CARDINALITY", "PT.UNKNOWN_FIELD", "DOC.UNKNOWN_FIELD", "MESH.UNKNOWN_FIELD", "CONTACT.PENALTY_DAMPING", "REF.DUPLICATE_ID", "PT.PROPERTY_FIELD", "BLOCK.PROPERTY_SENTINEL", "PT.TYPE", "SET.ENUM", "BLOCK.MATERIAL_ZERO", "MESH.NODE_LAYOUT", "MAT.GROUP_ARRAY", "PT.LAYERS_TYPE", "SET.SPECTRAL_ORDER", "DOC.DIMENSIONS_CONFLICT", "MESH.BINARY_SEMANTICS_UNCHECKED"]
    overrides = {
        "MESH.ARRAY_SIZE": ["Contact2dMixedHeattrannsRectangleSplit_Auto.fc"],
        "MESH.BUFFER_SIZE": ["13923_dynamic.fc", "Cube_static_direction_shell.fc"],
        "BLOCK.MATERIAL_ZERO": ["Cube_static_direction_shell.fc", "Cube_dyn_direction_shell.fc"],
        "PT.LAYERS_TYPE": ["Cube_static_direction_shell.fc", "Cube_dyn_direction_shell.fc"],
        "DOC.FIELD_TYPE": ["Contact2dMixedBriks_Homogeneous_Compression_ParantIdCheck.fc", "Contact3dHex20CylInCylAllRigidMove_Homogeneous.fc"],
        "DOC.UNKNOWN_FIELD": ["EfPrCond_CubeHooke_Hex20_nonper.fc", "Contact3dHex20CylInCylAllRigidMove_Homogeneous.fc"],
        "PT.UNKNOWN_FIELD": ["Contact3dHex8ShellEigenValues.fc", "Beam21_HookDamp_VM76.fc"],
    }
    groups = []
    for rule in rules:
        names = [name for name, r in records.items() if any(f["rule"] == rule for f in r["findings"])]
        names.sort(key=lambda n: (fi[n]["status"] != "loaded_without_errors", rt[n]["status"] != "equal", n))
        examples = list(overrides.get(rule, names[:2]))
        examples += [n for n in names if n not in examples][:2 - len(examples)]
        assert all(name in names for name in examples), (rule, examples)
        paths = Counter()
        for name in names:
            paths.update(set(re.sub(r"\[\d+\]", "[]", f["path"]) for f in records[name]["findings"] if f["rule"] == rule))
        groups.append({"rule": rule, "files": len(names), "fidesys_without_errors": sum(fi[n]["status"] == "loaded_without_errors" for n in names), "paths": dict(paths.most_common()), "examples": examples})
    selected = sorted(set(n for g in groups for n in g["examples"]))
    probes = []
    with tempfile.TemporaryDirectory(prefix="fc-spec-review-") as directory:
        for name in selected:
            path = ROOT / "data/fc_core_tests" / name
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == records[name]["sha256"] == rt[name]["sha256"] == fi[name]["sha256"]
            src = json.loads(path.read_text())
            result = {"file": name, "sha256": digest, "previous_roundtrip": rt[name]["status"], "fidesys_status": fi[name]["status"], "fidesys_errors": fi[name]["errors"], "fidesys_completion": fi[name]["completion"], "header": src["header"], "settings": src["settings"]}
            relevant = {g["rule"] for g in groups if name in g["examples"]}
            result["findings_reviewed"] = [{"rule": f["rule"], "path": f["path"], "original_actual": f["actual"], "value_in_file": value_at(src, f["path"])} for f in records[name]["findings"] if f["rule"] in relevant]
            mesh = src["mesh"]
            if src["header"]["binary"]:
                types = FCValue.decode(mesh["elem_types"], np.dtype(np.uint8)).data
                assert isinstance(types, np.ndarray)
                result["mesh_type_probe"] = {"elems_count": mesh["elems_count"], "decoded_uint8_count": int(types.size), "unique_codes": np.unique(types).tolist(), "bytes": int(types.nbytes), "declared_int_bytes": src["header"]["types"]["int"]}
            else:
                result["plain_mesh"] = {key: {"items": len(mesh[key]), "first": brief(mesh[key][0])} for key in ("nodes", "elems", "elem_types")}
            try:
                model = FCModel.load(str(path))
                target = Path(directory) / name
                model.save(str(target))
                out = json.loads(target.read_text())
                result["fresh_roundtrip"] = "equal" if signature(src) == signature(out) else "different"
                assert result["fresh_roundtrip"] == rt[name]["status"]
                result["preservation"] = {key: signature(src.get(key)) == signature(out.get(key)) for key in ("mesh", "settings", "materials", "property_tables", "blocks", "contact_constraints")}
                result["output_property_tables"] = brief(out.get("property_tables"))
                result["output_elem_types_base64_chars"] = len(out["mesh"]["elem_types"])
            except Exception as exc:
                result["fresh_roundtrip"] = "error"
                result["exception"] = {"type": type(exc).__name__, "message": str(exc)}
                assert rt[name]["status"] == "error", (name, exc)
            mats = []
            for raw in src["materials"]:
                multi = {k: [{"type": g.get("type"), "const_names": g.get("const_names")} for g in v] for k, v in raw.items() if isinstance(v, list) and len(v) > 1 and all(isinstance(g, dict) for g in v)}
                if multi:
                    try:
                        output = FCMaterial.decode(cast(FCSrcMaterial, raw)).encode()
                        mats.append({"id": raw["id"], "multi_groups": multi, "groups_preserved": {k: signature(raw[k]) == signature(output[k]) for k in multi}})
                    except Exception as exc:
                        mats.append({"id": raw["id"], "exception": str(exc)})
            result["material_probes"] = mats
            pts = []
            for raw in src.get("property_tables", []):
                output = FCPropertyTable.decode(cast(FCSrcPropertyTable, raw)).encode()
                pts.append({"input": brief(raw), "output": brief(output), "removed_fields": sorted(set(raw) - set(output)), "properties_preserved": signature(raw.get("properties")) == signature(output["properties"])})
            result["property_probes"] = pts
            result["blocks"] = src.get("blocks")
            result["contacts"] = brief(src.get("contact_constraints"))
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
            probes.append(result)
    # Distinguish observed per-type identifier reuse from arbitrary duplicated records.
    duplicate_files = same_type_duplicates = 0
    float_integer_findings = 0
    nonintegral_findings = []
    null_files = set()
    negative_property_files = 0
    for name, record in records.items():
        source = ROOT / "data/fc_core_tests" / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == record["sha256"]
        full = json.loads(source.read_text())
        negative_property_files += any(b.get("property_id") == -1 for b in full.get("blocks", []))
        for finding in record["findings"]:
            if finding["rule"] == "DOC.FIELD_TYPE" and finding["actual"] is None:
                null_files.add(name)
            if finding["rule"] == "PT.PROPERTY_FIELD":
                value = value_at(full, finding["path"])
                if isinstance(value, float) and value.is_integer():
                    float_integer_findings += 1
                else:
                    nonintegral_findings.append({"file": name, "path": finding["path"], "value": value})
        if not any(f["rule"] == "REF.DUPLICATE_ID" for f in record["findings"]):
            continue
        raw = full["property_tables"]
        duplicate_files += 1
        keys = [(x["type"], x["id"]) for x in raw]
        same_type_duplicates += len(keys) != len(set(keys))
    result = {"spec_sha256": report["spec_sha256"], "groups": groups, "selected_files": len(probes), "fresh_statuses": dict(Counter(p["fresh_roundtrip"] for p in probes)), "source_hashes_verified": len(records), "duplicate_files": duplicate_files, "files_with_duplicate_type_and_id": same_type_duplicates, "files_with_negative_property_id": negative_property_files, "files_with_null_type_findings": len(null_files), "integral_float_property_findings": float_integer_findings, "nonintegral_property_findings": nonintegral_findings, "probes": probes}
    (HERE / "evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("probes", "groups")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
