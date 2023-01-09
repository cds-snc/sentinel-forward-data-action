.PHONY: fmt install lint test fmt-ci lint-ci install-dev

fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

install-dev:
	pip3 install --user -r requirements_dev.txt

lint:
	flake8 .

test:
	pytest -s -vv tests

lint-ci:
	flake8 .

fmt-ci:
	black --check .
