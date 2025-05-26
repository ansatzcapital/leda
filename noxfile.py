"""Nox setup.

To run all linters, checkers, and tests:

```bash
nox
```

To run all fixers:

```bash
nox -t fix
```

By default, nox will set up venvs for each session. To use your current
env instead, add `--no-venv` to any command:

```bash
nox --no-venv
```

By default, nox will recreate venvs for each session. To reuse your existing
env instead, add `--reuse`/`-r` to any command:

```bash
nox --reuse
```

To run all static linters and checkers:

```
nox -t static
```

To pick a particular session, e.g.:

```bash
nox --list
nox -s fix_ruff
nox -s pytest -- -k test_name
```

To run all integration tests:

```bash
nox -t integration_test
```

To do an editable install into your current env:

```bash
nox -s develop
```

See https://nox.thea.codes/en/stable/index.html for more.
"""

from __future__ import annotations

import pathlib
import sys

import nox
import nox.virtualenv

# TODO: Remove pip support when we remove support for python3.8
if sys.version_info >= (3, 9):
    nox.options.default_venv_backend = "uv"

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


def prepare(session: nox.Session, extras: str = "all") -> None:
    """Help debugging in CI context."""
    if is_isolated_venv(session):
        session.install("-e", f".[{extras}]")


@nox.session()
def print_env(session: nox.Session) -> None:
    """Print env info for debugging."""
    prepare(session)

    session.run("python", "--version")
    session.run("uv", "pip", "list")


@nox.session(tags=["static", "typecheck"])
def mypy(session: nox.Session) -> None:
    """Run mypy type checker."""
    prepare(session)

    session.run("mypy", ".")


@nox.session(tags=["static", "typecheck"])
def pyright(session: nox.Session) -> None:
    """Run pyright type checker."""
    prepare(session)

    env = {"PYRIGHT_PYTHON_VERBOSE": "1"}
    # Enable for debugging
    if False:
        env["PYRIGHT_PYTHON_DEBUG"] = "1"

    session.run("pyright", ".", env=env)


@nox.session(tags=["test"])
def pytest(session: nox.Session) -> None:
    """Run pytest."""
    prepare(session)

    session.run("pytest", ".", *session.posargs)


@nox.session(tags=["lint", "static"])
def ruff(session: nox.Session) -> None:
    """Run ruff formatter and linter checks."""
    prepare(session)

    session.run("ruff", "format", ".", "--check")
    session.run("ruff", "check", ".")


@nox.session(tags=["fix"])
def fix_ruff(session: nox.Session) -> None:
    """Fix some ruff formatter and linter issues."""
    prepare(session)

    session.run("ruff", "format", ".")
    session.run("ruff", "check", ".", "--fix")


@nox.session()
def build(session: nox.Session) -> None:
    """Build Python wheel."""
    prepare(session)

    session.run("python", "-m", "build", "--wheel")
    session.run("twine", "check", "dist/*")


@nox.session(venv_backend="none")
def develop(session: nox.Session) -> None:
    """Install local dir into activated env using editable installs."""
    # We install using compatibility mode for VS Code
    # to pick up the installation correctly.
    # See https://setuptools.pypa.io/en/latest/userguide/development_mode.html#legacy-behavior.
    session.run(
        "uv",
        "pip",
        "install",
        "-e",
        ".[all]",
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
        "--force-reinstall",
        "--no-cache",
        "-c",
        requirements_filename,
    )
    session.install(
        f"matplotlib=={requirements_versions['matplotlib']}",
        "--force-reinstall",
        "--no-cache",
        "-c",
        requirements_filename,
    )

    # Need to constrain extras per requirements file
    session.install("-r", requirements_filename, "-c", requirements_filename)
    session.install("-e", ".[demos,test]")

    # To help debugging
    # TODO: Remove pip support when we remove support for python3.8
    args = ["pip"] if "--use-pip" in session.posargs else ["uv", "pip"]
    session.run(*args, "freeze")

    # Run test
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
