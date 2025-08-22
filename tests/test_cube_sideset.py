import json, sys
from pathlib import Path
from typing import Any, List

from fc_model import FCModel

def main() -> int:
    p = Path('tests/data/ultracube.fc')
    out = p.with_name(p.stem + '_roundtrip.fc')

    # Обновляем round-trip для актуальности
    fc_model = FCModel(str(p))
    fc_model.save(str(out))

    return 0


if __name__ == '__main__':
    sys.exit(main())
