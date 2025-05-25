"""Magics for IPython.

Note that this can only be imported in an IPython/Jupyter session.

See
https://ipython.readthedocs.io/en/stable/config/custommagics.html.
"""

from typing import Any, Callable, TypeVar

import IPython.core
import IPython.core.magic

import leda.interact.core
import leda.interact.func_gen

T = TypeVar("T")


def no_op(obj: T) -> T:
    return obj


try:
    get_ipython()  # type: ignore

    register_line_magic = IPython.core.magic.register_cell_magic
    register_line_cell_magic = IPython.core.magic.register_line_cell_magic
except NameError:
    register_line_magic = no_op
    register_line_cell_magic = no_op


def _interact(line: str, cell: str) -> Any:
    kwargs = leda.interact.func_gen.gen_kwargs(line)
    func_name, func_cell = leda.interact.func_gen.gen_func_cell(cell, kwargs)
    func = leda.interact.func_gen.gen_func(func_name, func_cell)
    return leda.interact.core.get_interact_mode().interact(func, **kwargs)


@register_line_cell_magic
def interact(line: str, cell: str) -> Any:
    return _interact(line, cell)


@register_line_magic
def toc(_: str) -> Any:
    return "Table of contents will be placed here in static mode."
