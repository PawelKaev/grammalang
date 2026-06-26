.PHONY: lint typecheck test ci

lint:
	ruff check src/ tests/

typecheck:
	mypy src/

test:
	pytest -v

ci: lint typecheck test
	@echo "CI passed."
