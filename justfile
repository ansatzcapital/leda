#####################################################################
# Composite
#####################################################################

default: fix test

static: ruff mypy pyright

fix: fix-ruff

unit-test: pytest

build: build-python-dist

test: static unit-test

test-matrix:
    pixi run -e test-py38 --frozen --locked just test
    pixi run -e test-py39 --frozen --locked just test
    pixi run -e test-py310 --frozen --locked just test
    pixi run -e test-py311 --frozen --locked just test
    pixi run -e test-py312 --frozen --locked just test
    pixi run -e test-py313 --frozen --locked just test
    pixi run -e test-py314 --frozen --locked just test

integration-test-matrix: integration-test0 integration-test2 integration-test3

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

[positional-arguments]
@integration-test0 *args:
    pixi run -e integration-test0 --frozen --locked python ./leda/tests/integration/run_test.py test0 "$@"

[positional-arguments]
@gen-integration-test0 *args:
    pixi run -e integration-test0 --frozen --locked python ./leda/tests/integration/run_test.py test0 --gen-refs "$@"

[positional-arguments]
@integration-test2 *args:
    pixi run -e integration-test2 --frozen --locked python ./leda/tests/integration/run_test.py test2 "$@"

[positional-arguments]
@gen-integration-test2 *args:
    pixi run -e integration-test2 --frozen --locked python ./leda/tests/integration/run_test.py test2 --gen-refs "$@"

[positional-arguments]
@integration-test3 *args:
    pixi run -e integration-test3 --frozen --locked python ./leda/tests/integration/run_test.py test3 "$@"

[positional-arguments]
@gen-integration-test3 *args:
    pixi run -e integration-test3 --frozen --locked python ./leda/tests/integration/run_test.py test3 --gen-refs "$@"

[positional-arguments]
@integration-test4 *args:
    pixi run -e integration-test4 --frozen --locked python ./leda/tests/integration/run_test.py test4 "$@"

[positional-arguments]
@gen-integration-test4 *args:
    pixi run -e integration-test4 --frozen --locked python ./leda/tests/integration/run_test.py test4 --gen-refs "$@"

build-python-dist:
    uv build && twine check dist/*
