from __future__ import annotations

import textwrap
from typing import Any, Callable, Mapping
import uuid

import IPython


def gen_kwargs(
    line: str, ipy: IPython.InteractiveShell | None = None
) -> Mapping:
    """Evals line into kwargs."""
    if not line.strip():
        return {}

    ipy = IPython.get_ipython() if not ipy else ipy

    kwargs = {}
    parts = line.split(";")
    for part in parts:
        key, value = part.strip().split("=")
        kwargs[key] = ipy.ev(value)  # pyright: ignore

    return kwargs


def gen_func_cell(
    cell: str, kwargs: Mapping[str, Any], func_name: str | None = None
) -> tuple[str, str]:
    if not func_name:
        unique_id = uuid.uuid4().hex[:10]
        func_name = f"func_{unique_id}"

    arg_names = ", ".join(kwargs.keys())

    cell_lines = cell.strip().split("\n")

    # Add return line
    cell_lines[
        -1
    ] = f"return leda.get_interact_mode().process_result({cell_lines[-1]})"

    # Add indents
    func_body = textwrap.indent("\n".join(cell_lines), "    ")

    return (
        func_name,
        f"""
import leda.interact.func_gen


def {func_name}({arg_names}):
{func_body}
""",
    )


def gen_func(
    func_name: str,
    func_cell: str,
    ipy: IPython.InteractiveShell | None = None,
) -> Callable:
    ipy = IPython.get_ipython() if not ipy else ipy
    ipy.ex(func_cell)  # pyright: ignore
    return ipy.ev(func_name)  # pyright: ignore
