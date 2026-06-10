.PHONY: test test-live lint format install doctor-live

install:
	pip install -e ".[dev,pfx]"

test:
	pytest tests/ -m "not live" --cov=pjm_api --cov-report=term-missing

test-live:
	PJM_LIVE_TEST=1 pytest tests/ -m live

doctor-live:
	PJM_LIVE_TEST=1 pjm-api doctor --env TRAIN

lint:
	ruff check .
	mypy src/pjm_api

format:
	ruff format .
