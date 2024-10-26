"""Nox setup.

To run all linters, checkers, and tests:
    nox

To run all fixers:
    nox -t fix

By default, nox will set up venvs for each session. To use your current
env instead, add `--no-venv` to any command:
    nox --no-venv

By default, nox will recreate venvs for each session. To reuse your existing
env instead, add `--reuse`/`-r` to any command:
    nox --reuse

To run all static linters and checkers:
    nox -t static

To pick a particular session, e.g.:
    nox --list
    nox -s fix_ruff
    nox -s pytest -- -k test_name

To run all integration tests:
    nox -t integration_test

To do an editable install into your current env:
    nox -s develop

See https://nox.thea.codes/en/stable/index.html for more.
"""

from __future__ import annotations

import pathlib
import sys

import nox
import nox.virtualenv

# Hack to fix tags for non-defaulted sessions (otherwise, running
# `nox -t fix` won't pick up any sessions)
if any(arg.startswith("fix") for arg in sys.argv):
    nox.options.sessions = ["fix_ruff"]
elif any(arg.startswith("integration_test") for arg in sys.argv):
    nox.options.sessions = [
        "integration_test_bundle0",
        "integration_test_bundle1",
        "integration_test_bundle2",
        "integration_test_bundle3",
        "integration_test_bundle4",
    ]
else:
    nox.options.sessions = ["ruff", "mypy", "pyright", "pytest"]


def is_isolated_venv(session: nox.Session) -> bool:
    """Indicates that the session is being run in an isolated env.

    I.e., the user has not set `--no-venv`.

    If the user uses their development (non-isolated) venv,
    then nox will (correctly) refuse to install packages, unless forced to.
    """
    return not isinstance(session.virtualenv, nox.virtualenv.PassthroughEnv)


@nox.session(tags=["static", "typecheck"])
def mypy(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")

    session.run("mypy", "leda")


@nox.session(tags=["static", "typecheck"])
def pyright(session: nox.Session) -> None:
    # TODO: Remove once pyright >= 1.1.387 is available. See:
    #   - https://github.com/microsoft/pyright/issues/9296
    #   - https://docs.python.org/3/library/sys.html#sys.platform
    if sys.platform == "win32":
        session.install("pyright <= 1.1.385")

    if is_isolated_venv(session):
        session.install("-e", ".[test]")

    env = {"PYRIGHT_PYTHON_VERBOSE": "1"}
    # Enable for debugging
    if False:
        env["PYRIGHT_PYTHON_DEBUG"] = "1"

    session.run("pyright", "leda", env=env)


@nox.session(tags=["test"])
def pytest(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
    session.run("pytest", "leda", *session.posargs)


@nox.session(tags=["lint", "static"])
def ruff(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")

    session.run("ruff", "format", "leda", "--check")
    session.run("ruff", "check", "leda")


@nox.session(tags=["fix"])
def fix_ruff(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")

    session.run("ruff", "format", "leda")
    session.run("ruff", "check", "leda", "--fix")


@nox.session(venv_backend="none")
def develop(session: nox.Session) -> None:
    # We install using compatibility mode for VS Code
    # to pick up the installation correctly.
    # See https://setuptools.pypa.io/en/latest/userguide/development_mode.html#legacy-behavior.
    session.run(
        "pip",
        "install",
        "-e",
        ".[demos,setup,test]",
        "--config-settings",
        "editable_mode=compat",
    )


def _get_requirements_versions(
    requirements_path: pathlib.Path,
) -> dict[str, str]:
    versions = {}
    for line in pathlib.Path(requirements_path).read_text().splitlines():
        if "==" not in line or line.startswith("#"):
            continue

        name, version = map(str.strip, line.split("=="))
        if "#" in version:
            version = version.split("#")[0].strip()

        versions[name] = version
    return versions


def _run_integration_test(session: nox.Session, bundle_name: str) -> None:
    if not is_isolated_venv(session):
        raise ValueError("Must be in isolated env mode")

    requirements_filename = f"requirements-{bundle_name}.txt"

    # In some cases, the cached versions of matplotlib and numpy are
    # incompatible, so we force them to rebuild in this specific order.
    requirements_versions = _get_requirements_versions(
        pathlib.Path(requirements_filename)
    )

    session.install(
        f"numpy=={requirements_versions['numpy']}",
        "--force",
        "--no-cache",
        "-c",
        requirements_filename,
    )
    session.install(
        f"matplotlib=={requirements_versions['matplotlib']}",
        "--force",
        "--no-cache",
        "-c",
        requirements_filename,
    )

    # Need to constrain extras per requirements file
    session.install("-r", requirements_filename, "-c", requirements_filename)
    session.install("-e", ".[demos,test]")

    args = []
    if "--gen-html-diffs" in session.posargs:
        args.append("--gen-html-diffs")

    session.run(
        "python",
        "-m",
        "leda.tests.integration.run_test",
        bundle_name,
        "--log",
        "INFO",
        *args,
    )


# Remember to update the python versions when we remove
# and update bundles. Note that the integration test will do a env
# check in the beginning if we have a mismatch between the nox
# config and the requirements bundles.
@nox.session(python="3.8", tags=["integration_test"])
def integration_test_bundle0(session: nox.Session) -> None:
    _run_integration_test(session, "bundle0")


@nox.session(python="3.8", tags=["integration_test"])
def integration_test_bundle1(session: nox.Session) -> None:
    _run_integration_test(session, "bundle1")


@nox.session(python="3.10", tags=["integration_test"])
def integration_test_bundle2(session: nox.Session) -> None:
    _run_integration_test(session, "bundle2")


@nox.session(python="3.11", tags=["integration_test"])
def integration_test_bundle3(session: nox.Session) -> None:
    _run_integration_test(session, "bundle3")


@nox.session(python="3.12", tags=["integration_test"])
def integration_test_bundle4(session: nox.Session) -> None:
    _run_integration_test(session, "bundle4")
