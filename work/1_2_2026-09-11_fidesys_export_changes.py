"""Read-only diagnosis of the 450 successful Fidesys exports.

Run from the repository root: PYTHONPATH=src python work/1_2_2026-09-11_fidesys_export_changes.py
Only the adjacent evidence JSON is written; Fidesys is not started.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
from numpy.typing import NDArray

from fc_model import FCValue, FC_ELEMENT_TYPES_KEYID

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "work/1_2_2026-09-11_fidesys_roundtrip"
Element = Tuple[int, Tuple[int, ...]]


def array(value: str, dtype: str) -> NDArray[np.generic]:
    decoded = FCValue.decode(value, np.dtype(dtype)).data
    assert isinstance(decoded, np.ndarray)
    return decoded


def elements(mesh: dict) -> Dict[int, Element]:
    ids = array(mesh["elemids"], "int32")
    types = array(mesh["elem_types"], "uint8")
    nodes = array(mesh["elems"], "int32")
    assert len(ids) == len(types) == mesh["elems_count"]
    result: Dict[int, Element] = {}
    offset = 0
    for elem_id, elem_type in zip(ids, types):
        size = FC_ELEMENT_TYPES_KEYID[int(elem_type)]["nodes_count"]
        result[int(elem_id)] = (int(elem_type), tuple(map(int, nodes[offset:offset + size])))
        offset += size
    assert offset == len(nodes) and len(result) == len(ids)
    return result


def strict_equal(a: object, b: object) -> bool:
    # Match the existing audit's distinction between JSON int and float.
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def main() -> None:
    records = json.loads((RUN / "results.json").read_text())["files"]
    totals: Counter[str] = Counter()
    sections: Counter[str] = Counter()
    files = []
    for record in records:
        if not record["alive"]:
            continue
        source = (ROOT / "data/fc_core_tests" / record["file"]).read_bytes()
        exported = (RUN / record["output"]).read_bytes()
        assert hashlib.sha256(source).hexdigest() == record["sha256"]
        assert hashlib.sha256(exported).hexdigest() == record["output_sha256"]
        a, b = json.loads(source), json.loads(exported)
        assert record["json_status"] == "different"
        am, bm = a["mesh"], b["mesh"]
        ai, bi = array(am["nids"], "int32"), array(bm["nids"], "int32")
        ax = array(am["nodes"], "float64").astype(np.float64, copy=False).reshape(-1, 3)
        bx = array(bm["nodes"], "float64").astype(np.float64, copy=False).reshape(-1, 3)
        assert len(ai) == len(ax) == am["nodes_count"]
        assert len(bi) == len(bx) == bm["nodes_count"]
        assert len(np.unique(ai)) == len(ai) == len(bi) == len(np.unique(bi))
        assert np.array_equal(np.sort(ai), np.sort(bi))
        ao, bo = np.argsort(ai), np.argsort(bi)
        aa, bb = ax[ao], bx[bo]
        changed = np.flatnonzero(np.any(aa != bb, axis=1))
        old_coordinates = set(map(tuple, ax.tolist()))
        node_changes = [
            {"id": int(ai[ao][i]), "before": aa[i].tolist(), "after": bb[i].tolist(),
             "after_existed_in_source": tuple(bb[i].tolist()) in old_coordinates}
            for i in changed
        ]
        ae, be = elements(am), elements(bm)
        assert ae.keys() == be.keys()
        unordered_a = Counter((t, tuple(sorted(ns))) for t, ns in ae.values())
        unordered_b = Counter((t, tuple(sorted(ns))) for t, ns in be.values())
        metrics = {
            "node_storage_order_changed": not np.array_equal(ai, bi),
            "coordinates_exact_by_id": len(changed) == 0,
            "elements_exact_by_id": ae == be,
            "element_signatures_equal_ignoring_ids": Counter(ae.values()) == Counter(be.values()),
            "element_node_sets_equal_ignoring_ids_and_local_order": unordered_a == unordered_b,
            "materials_section_unchanged": strict_equal(a.get("materials"), b.get("materials")),
            "legacy_material_assignments_replaced": "elem_materials" in am and "blocks" not in a,
            "legacy_contacts_disappeared": bool(a.get("contacts")) and not any(
                b.get(key) for key in ("contacts", "contact_constraints", "coupling_constraints", "periodic_constraints")
            ),
        }
        changed_sections = [key for key in sorted(a.keys() | b.keys())
                            if key not in a or key not in b or not strict_equal(a[key], b[key])]
        sections.update(changed_sections)
        for key, value in metrics.items():
            totals[key] += int(value)
        evidence = {
            "file": record["file"], "metrics": metrics, "changed_sections": changed_sections,
            "changed_nodes": node_changes,
            "max_coordinate_delta": float(np.max(np.abs(aa - bb))) if len(ai) else 0.0,
            "changed_element_ids": [key for key in ae if ae[key] != be[key]],
        }
        if metrics["legacy_material_assignments_replaced"]:
            old_materials = sorted(set(map(int, array(am["elem_materials"], "int32"))))
            new_materials = sorted({v["material_id"] for v in b["blocks"]})
            declared_materials = sorted(v["id"] for v in b.get("materials", []))
            assert new_materials == [0] and 0 not in declared_materials
            evidence["material_assignment"] = {
                "old_ids": old_materials, "new_ids": new_materials, "declared_ids": declared_materials,
            }
        files.append(evidence)
    assert len(files) == 450
    assert totals["element_node_sets_equal_ignoring_ids_and_local_order"] == 450
    result = {"files_checked": len(files), "hashes_checked": 900,
              "section_counts": dict(sections.most_common()), "metrics": dict(totals), "files": files}
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "files"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
