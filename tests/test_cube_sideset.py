from pathlib import Path

from fc_model import FCModel

def test_cube_sideset_roundtrip(tmp_path: Path) -> None:
    p = Path("tests/data/ultracube.fc")
    out = tmp_path / "ultracube_roundtrip.fc"

    fc_model = FCModel.load(str(p))
    fc_model.compress()
    fc_model.save(str(out))

if __name__ == '__main__':
    test_cube_sideset_roundtrip(Path('.'))