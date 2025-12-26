import json
from pathlib import Path
from typing import Any, List

from fc_model import FCModel

OPTIONAL_EMPTY_KEYS = {"data", "dep_var_num", "dep_var_size", "dependency_type"}

def _is_effectively_empty_optional(value: Any) -> bool:
    if value in ([], ""):
        return True
    if isinstance(value, list) and value:
        return all(v in ("", 0) for v in value)
    return False

def deep_diff(a: Any, b: Any, path: str = "$") -> List[str]:
    diffs: List[str] = []

    if type(a) != type(b):
        diffs.append(f"{path}: type mismatch {type(a).__name__} != {type(b).__name__}")
        return diffs

    if isinstance(a, dict):
        a_keys = set(a.keys())
        b_keys = set(b.keys())
        only_a = a_keys - b_keys
        only_b = b_keys - a_keys
        for k in sorted(only_a):
            # допустимо: ключ отсутствует во втором, если в первом он "пустой" и относится к опциональным
            if k in OPTIONAL_EMPTY_KEYS and _is_effectively_empty_optional(a.get(k)):
                continue
            diffs.append(f"{path}.{k}: missing in second")
        for k in sorted(only_b):
            # допустимо: ключ отсутствует в первом, если во втором он "пустой" и относится к опциональным
            if k in OPTIONAL_EMPTY_KEYS and _is_effectively_empty_optional(b.get(k)):
                continue
            diffs.append(f"{path}.{k}: missing in first")
        for k in sorted(a_keys & b_keys):
            diffs.extend(deep_diff(a[k], b[k], f"{path}.{k}"))
        return diffs

    if isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length {len(a)} != {len(b)}")
        min_len = min(len(a), len(b))
        for i in range(min_len):
            diffs.extend(deep_diff(a[i], b[i], f"{path}[{i}]"))
        if len(a) > len(b):
            for i in range(min_len, len(a)):
                diffs.append(f"{path}[{i}]: extra in first: {repr(a[i])}")
        elif len(b) > len(a):
            for i in range(min_len, len(b)):
                diffs.append(f"{path}[{i}]: extra in second: {repr(b[i])}")
        return diffs

    if a != b:
        diffs.append(f"{path}: {repr(a)} != {repr(b)}")
    
    return diffs


def test_ultracube_roundtrip(tmp_path: Path) -> None:
    p = Path("tests/data/ultracube.fc")
    out = tmp_path / "ultracube_roundtrip.fc"

    m = FCModel.load(str(p))
    m.save(str(out))

    # Проверяем, что файл корректный JSON
    with open(out, "r") as f:
        json.load(f)

    with open(p, "r") as f1, open(out, "r") as f2:
        src = json.load(f1)
        rtp = json.load(f2)

    diffs = deep_diff(src, rtp)
    assert diffs == []
