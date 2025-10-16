"""Run all integration tests for a particular version of Python."""

from __future__ import annotations

import argparse
import logging
import pathlib
import subprocess
import sys

import leda

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

logger = logging.getLogger(__name__)

# NB: This only works in editable install.
REPO_DIR = pathlib.Path(leda.__file__).parent.parent


def run_tests(python_version: str | None, extra_args: list[str]) -> None:
    pyproject_path = REPO_DIR / "pyproject.toml"
    with pyproject_path.open("rb") as fh:
        pyproject_config = tomllib.load(fh)

    count = 0
    features = pyproject_config["tool"]["pixi"]["feature"]
    for key, value in features.items():
        print(f"Key: {key}", file=sys.stderr)
        if not key.startswith("integration-test"):
            print("Skipping, not an integration test", file=sys.stderr)
            continue

        test_python_version = value["dependencies"]["python"]
        assert test_python_version.startswith("~=3.")
        assert test_python_version.endswith(".0")
        if (
            python_version is None
            or test_python_version == f"~={python_version}.0"
        ):
            command = " ".join(["just", key, " ".join(extra_args)])
            print(f"Running {key}: {command}", file=sys.stderr)
            count += 1
            subprocess.check_call(command, shell=True)
        else:
            print(f"Skipping {key}, {test_python_version}", file=sys.stderr)

    print(f"Running {count} tests", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-version")
    args, extra_args = parser.parse_known_args()

    run_tests(args.python_version, extra_args)


if __name__ == "__main__":
    main()
