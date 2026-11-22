.PHONY: setup download-model samples test build-frontend dev

PYTHON := backend/.venv/bin/python
PYTEST := backend/.venv/bin/pytest

setup:
	/opt/homebrew/bin/python3.12 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements.txt
	npm --prefix frontend install

download-model:
	$(PYTHON) backend/scripts/download_model.py

samples:
	$(PYTHON) backend/scripts/generate_demo_samples.py

test:
	$(PYTEST) -v backend/tests/test_forensics.py

build-frontend:
	npm --prefix frontend run build

dev:
	./start_dev.sh
