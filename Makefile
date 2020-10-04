all: test flake8 mypy lint

test:
	pytest

flake8:
	flake8 --max-line-length 80 --per-file-ignores='test/test_report.py:E501'

mypy:
	mypy -p did --ignore-missing-imports

lint:
	pylint --disable=R,C did
	pylint --disable='C0111' did
	pylint did

.PHONY: all test flake8 lint mypy
