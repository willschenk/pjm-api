.PHONY: test test-live lint format install

install:
	pip install -e ".[dev,pfx]"

test:
	pytest tests/ -m "not live" --cov=pjm_api --cov-report=term-missing

test-live:
	PJM_LIVE_TEST=1 pytest tests/ -m live

lint:
	ruff check .
	mypy src/pjm_api

format:
	ruff format .
