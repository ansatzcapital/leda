from typing import Any, cast

import IPython

import leda.interact.func_gen


class MockIPy:
    def __init__(self):
        self.space = {"foo_vals": ["a", "b"]}

    def ev(self, value: str) -> Any:
        return eval(value, self.space)


def test_gen_kwargs():
    mock_ipy = cast(IPython.InteractiveShell, MockIPy())
    assert leda.interact.func_gen.gen_kwargs("", ipy=mock_ipy) == {}
    assert leda.interact.func_gen.gen_kwargs(
        "foo_val=foo_vals", ipy=mock_ipy
    ) == {"foo_val": ["a", "b"]}
    assert leda.interact.func_gen.gen_kwargs("mult=(1, 2)", ipy=mock_ipy) == {
        "mult": (1, 2)
    }
    assert leda.interact.func_gen.gen_kwargs(
        "foo_val=foo_vals;mult=(1, 2)", ipy=mock_ipy
    ) == {"foo_val": ["a", "b"], "mult": (1, 2)}


def test_gen_func_cell():
    new_cell = leda.interact.func_gen.gen_func_cell(
        "fig", {"foo_val": ["a", "b"], "mult": (1, 2)}, func_name="foo"
    )[1]
    assert (
        new_cell
        == """
import leda.interact.func_gen


def foo(foo_val, mult):
    return leda.get_interact_mode().process_result(fig)
"""
    )


def test_gen_func_cell_indents():
    cell = """
fig = px.histogram(df,
                   nbins=100)
fig
"""
    new_cell = leda.interact.func_gen.gen_func_cell(
        cell, {"foo_val": ["a", "b"], "mult": (1, 2)}, func_name="foo"
    )[1]
    assert (
        new_cell
        == """
import leda.interact.func_gen


def foo(foo_val, mult):
    fig = px.histogram(df,
                       nbins=100)
    return leda.get_interact_mode().process_result(fig)
"""
    )
