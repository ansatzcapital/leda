"""Magics for IPython.

Note that this can only be imported in an IPython/Jupyter session.

See https://ipython.readthedocs.io/en/stable/config/custommagics.html.
"""
from typing import Any

import IPython.core.magic

import leda.interact.core
import leda.interact.func_gen


def _interact(line: str, cell: str) -> Any:
    kwargs = leda.interact.func_gen.gen_kwargs(line)
    func_name, func_cell = leda.interact.func_gen.gen_func_cell(cell, kwargs)
    func = leda.interact.func_gen.gen_func(func_name, func_cell)
    return leda.interact.core.get_interact_mode().interact(func, **kwargs)


@IPython.core.magic.register_line_cell_magic
def interact(line: str, cell: str) -> Any:
    return _interact(line, cell)


@IPython.core.magic.register_line_magic
def toc(_) -> Any:
    return "Table of contents will be placed here in static mode."
