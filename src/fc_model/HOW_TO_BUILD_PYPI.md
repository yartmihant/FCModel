python3 -m build
python3 -m twine check dist/*

export PYPI_TOKEN="pypi-*"
python3 -m twine upload -u __token__ -p "$PYPI_TOKEN" dist/*
