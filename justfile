#####################################################################
# Composite
#####################################################################

default: fix test

static: ruff mypy pyright

fix: fix-ruff

unit-test: pytest

test: static unit-test

build: build-python-dist

test-matrix:
    pixi run -e test-py38 --frozen --locked just test
    pixi run -e test-py39 --frozen --locked just test
    pixi run -e test-py310 --frozen --locked just test
    pixi run -e test-py311 --frozen --locked just test
    pixi run -e test-py312 --frozen --locked just test
    pixi run -e test-py313 --frozen --locked just test
    pixi run -e test-py314 --frozen --locked just test

integration-test-matrix: integration-test0 integration-test1 integration-test2 integration-test3

#####################################################################
# Common
#####################################################################

run-ci-tests:
    act -j test --container-architecture linux/amd64

#####################################################################
# Python
#####################################################################

ruff:
    ruff format . --check && ruff check .

fix-ruff:
    ruff format . && ruff check . --fix

mypy:
    mypy .

pyright:
    pyright .

pytest:
    pytest .

integration-test0:
    pixi run -e integration-test0 --frozen --locked python ./leda/tests/integration/run_test.py test0

gen-integration-test0:
    pixi run -e integration-test0 --frozen --locked python ./leda/tests/integration/run_test.py test0 --gen-refs

integration-test1:
    pixi run -e integration-test1 --frozen --locked python ./leda/tests/integration/run_test.py test1

gen-integration-test1:
    pixi run -e integration-test1 --frozen --locked python ./leda/tests/integration/run_test.py test1 --gen-refs

integration-test2:
    pixi run -e integration-test2 --frozen --locked python ./leda/tests/integration/run_test.py test1

gen-integration-test2:
    pixi run -e integration-test2 --frozen --locked python ./leda/tests/integration/run_test.py test2 --gen-refs

integration-test3:
    pixi run -e integration-test3 --frozen --locked python ./leda/tests/integration/run_test.py test3

gen-integration-test3:
    pixi run -e integration-test3 --frozen --locked python ./leda/tests/integration/run_test.py test3 --gen-refs

build-python-dist:
    uv build && twine check dist/*
