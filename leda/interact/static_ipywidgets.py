import dataclasses
import html
from typing import Any, Callable, Optional

import ipywidgets

import leda.interact.base
import leda.interact.core
import leda.interact.dynamic
from leda.vendor.static_ipywidgets import static_ipywidgets


class StaticIpywidgetsInteractMode(leda.interact.base.InteractMode):
    _plot_lib: Optional[str] = dataclasses.field(default=None, init=False)

    @property
    def dynamic(self) -> bool:
        return False

    def init(self, plot_lib: str):
        self._plot_lib = plot_lib.lower()
        if self._plot_lib == "matplotlib":
            pass
        elif self._plot_lib == "plotly":
            import plotly.offline

            # Set online mode (i.e., load plotly.js from web)
            plotly.offline.init_notebook_mode(connected=True)
        else:
            raise ValueError(self._plot_lib)

    # noinspection PyProtectedMember
    def interact(self, func: Callable, **kwargs) -> Any:
        new_value: static_ipywidgets.widgets.StaticWidget

        kwargs = dict(leda.interact.dynamic.to_dynamic_ipywidgets(kwargs))

        for key, value in kwargs.items():
            if isinstance(value, ipywidgets.widgets.IntSlider):
                new_value = static_ipywidgets.widgets.RangeWidget(
                    min=value.min,
                    max=value.max,
                    step=value.step,
                )
            elif isinstance(value, ipywidgets.widgets.Dropdown):
                labels = [html.escape(v[0]) for v in value._options_full]
                values = [v[1] for v in value._options_full]
                new_value = static_ipywidgets.widgets.DropDownWidget(
                    values=values,
                    labels=labels,
                )
            else:
                raise ValueError(f"Unknown type: {type(value)}")

            kwargs[key] = new_value

        return static_ipywidgets.interact.StaticInteract(func, **kwargs)

    def process_result(self, obj: Any) -> Any:
        if leda.interact.base.is_matplotlib(obj):
            import matplotlib.pyplot as plt

            return plt.gcf()

        return super().process_result(obj)
