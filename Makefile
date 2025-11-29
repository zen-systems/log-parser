# Makefile
PYTHON ?= python3

.Phony: install test run lint docker-build docker-run


install:
	$(PYTHON) -m pip install -r requirements.txt


run: install
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) src/main.py "$(FILE)"; \

	else \
		$(PYTHON) src/main.py data/input..csv; \
	fi

test: install
	$(PYTHON) -m pytest

lint:
	@echo "No linter configured yet. Add ruff/flake8 here if desired."

docker-build:
	docker build -t trade-aggregator .

docker-run:
	docker run -rm -i trade-aggregator

