import dataclasses
from unittest import mock

from leda.vendor.static_ipywidgets.static_ipywidgets import interact, widgets


@dataclasses.dataclass(frozen=True)
class Obj:
    x: int

    def _repr_html_(self):
        return str(self.x)


def func(x):
    return Obj(2 * x)


def test_simple():
    with mock.patch("IPython.get_ipython"):
        static_interact = interact.StaticInteract(
            func, x=widgets.DropDownWidget([1, 2])
        )
        html = static_interact.html()
        assert (
            """
    <div name="subdiv-x1" style="display:block">
      2
    </div>
    # noqa: W293
    <div name="subdiv-x2" style="display:none">
      4
    </div>""".replace(
                "# noqa: W293", ""
            )
            in html
        )
