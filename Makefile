.PHONY: install lint typecheck test run quality

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check backend
	ruff format --check backend

typecheck:
	mypy

test:
	pytest

quality: lint typecheck test

run:
	uvicorn evidencegraph.api.main:app --app-dir backend/src --reload
