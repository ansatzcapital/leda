from unittest import mock

from leda.vendor.static_ipywidgets.static_ipywidgets import interact, widgets


def func(x):
    return 2 * x


def test_simple():
    with mock.patch(
        "leda.static_ipywidgets.static_ipywidgets.interact._get_png_rep",
        lambda obj: None,
    ):
        static_interact = interact.StaticInteract(
            func, x=widgets.DropDownWidget([1, 2])
        )
        assert (
            """
    <div name="x1" style="display:block">
      <p> 2 </p>
    </div>
    
    <div name="x2" style="display:none">
      <p> 4 </p>
    </div>"""  # noqa: W293
            in static_interact.html()
        )
