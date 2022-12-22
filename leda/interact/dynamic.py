from typing import Any, Callable, Dict

import ipywidgets

import leda.interact.base


def to_dynamic_ipywidgets(values: Dict[str, Any]) -> Dict[str, Any]:
    new_values = {}
    for key, value in values.items():
        widget = ipywidgets.widgets.interactive.widget_from_abbrev(value)

        if isinstance(widget, ipywidgets.IntSlider):
            # Set default value to min instead of midpoint
            widget.value = widget.min

            # Only update when user releases slider
            widget.continuous_update = False

        new_values[key] = widget
    return new_values


class DynamicIpywidgetsInteractMode(leda.interact.base.InteractMode):
    @property
    def dynamic(self) -> bool:
        return True

    def init(self, plot_lib: str):
        if plot_lib.lower() == "matplotlib":
            import matplotlib.pyplot as plt

            # Turn on interactive mode
            plt.ion()

    def interact(self, func: Callable, **kwargs) -> Any:
        kwargs = to_dynamic_ipywidgets(kwargs)

        return ipywidgets.interact(func, **kwargs)

    def process_result(self, obj: Any) -> Any:
        if leda.interact.base.is_plotly(obj):
            obj.show()

            return None

        return super().process_result(obj)
