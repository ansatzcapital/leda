"""Nox setup.

To run all linters, checkers, and tests:
    nox

To run all fixers:
    nox -t fix

By default, nox will set up venvs for each session. To use your current
env instead, add `--no-venv` to any command:
    nox --no-venv

To run all static linters and checkers:
    nox -t static

To pick a particular session, e.g.:
    nox --list
    nox -s fix_black
    nox -s pytest -- -k test_name

To run all integration tests:
    nox -t integration_test

To do an editable install into your current env:
    nox -s develop

See https://nox.thea.codes/en/stable/index.html for more.
"""
import sys

import nox
import nox.virtualenv

# Hack to fix tags for non-defaulted sessions (otherwise, running
# `nox -t fix` won't pick up any sessions)
if any(arg.startswith("fix") for arg in sys.argv):
    nox.options.sessions = ["fix_black", "fix_ruff"]
elif any(arg.startswith("integration_test") for arg in sys.argv):
    nox.options.sessions = [
        "integration_test_bundle0",
        "integration_test_bundle1",
        "integration_test_bundle2",
        "integration_test_bundle3",
        "integration_test_bundle4",
    ]
else:
    nox.options.sessions = ["black", "mypy", "pyright", "pytest", "ruff"]


def is_isolated_venv(session: nox.Session) -> bool:
    """Indicates that the session is being run in an isolated env.

    I.e., the user has not set `--no-venv`.

    If the user uses their development (non-isolated) venv,
    then nox will (correctly) refuse to install packages, unless forced to.
    """
    return not isinstance(session.virtualenv, nox.virtualenv.PassthroughEnv)


@nox.session(tags=["lint", "static"])
def black(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
    session.run("black", "--check", "leda")


@nox.session(tags=["fix"])
def fix_black(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
    session.run("black", "leda")


@nox.session(tags=["static", "typecheck"])
def mypy(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
    session.run("mypy", "leda")


@nox.session(tags=["static", "typecheck"])
def pyright(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
    session.run(
        "pyright",
        "leda",
        env={"PYRIGHT_PYTHON_DEBUG": "1", "PYRIGHT_PYTHON_VERBOSE": "1"},
    )


@nox.session(tags=["test"])
def pytest(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
    session.run("pytest", "leda", *session.posargs)


@nox.session(tags=["lint", "static"])
def ruff(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
    session.run("ruff", "check", "leda")


@nox.session(tags=["fix"])
def fix_ruff(session: nox.Session) -> None:
    if is_isolated_venv(session):
        session.install("-e", ".[test]")
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
        ".[setup,test]",
        "--config-settings",
        "editable_mode=compat",
    )


def _run_integration_test(
    session: nox.Session,
    bundle_name: str,
    numpy_version: str,
    matplotlib_version: str,
) -> None:
    if not is_isolated_venv(session):
        raise ValueError("Must be in isolated env mode")

    requirements_filename = f"requirements-{bundle_name}.txt"

    # In some cases, the cached versions of matplotlib and numpy are
    # incompatible, so we force them to rebuild in this order.
    session.install(
        f"numpy=={numpy_version}",
        "--force",
        "--no-cache",
        "-c",
        requirements_filename,
    )
    session.install(
        f"matplotlib=={matplotlib_version}",
        "--force",
        "--no-cache",
        "-c",
        requirements_filename,
    )

    # Need to constrain extras per requirements file
    session.install("-r", requirements_filename, "-c", requirements_filename)
    session.install("-e", ".[demos,test]")

    session.run(
        "python",
        "-m",
        "leda.tests.integration.run_test",
        bundle_name,
        "--log",
        "INFO",
    )


@nox.session(python="3.7", tags=["integration_test"])
def integration_test_bundle0(session: nox.Session) -> None:
    _run_integration_test(
        session, "bundle0", numpy_version="1.16.6", matplotlib_version="2.2.5"
    )


@nox.session(python="3.8", tags=["integration_test"])
def integration_test_bundle1(session: nox.Session) -> None:
    _run_integration_test(
        session, "bundle1", numpy_version="1.16.6", matplotlib_version="2.2.5"
    )


@nox.session(python="3.8", tags=["integration_test"])
def integration_test_bundle2(session: nox.Session) -> None:
    _run_integration_test(
        session, "bundle2", numpy_version="1.16.6", matplotlib_version="3.1.3"
    )


@nox.session(python="3.10", tags=["integration_test"])
def integration_test_bundle3(session: nox.Session) -> None:
    _run_integration_test(
        session, "bundle3", numpy_version="1.22.4", matplotlib_version="3.5.3"
    )


@nox.session(python="3.11", tags=["integration_test"])
def integration_test_bundle4(session: nox.Session) -> None:
    _run_integration_test(
        session, "bundle4", numpy_version="1.24.0", matplotlib_version="3.6.2"
    )
