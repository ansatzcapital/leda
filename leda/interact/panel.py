import dataclasses
from typing import Any, Callable, Optional

import leda.interact.base
import leda.interact.core


@dataclasses.dataclass()
class StaticPanelInteractMode(leda.interact.base.InteractMode):
    progress: bool = False

    _plot_lib: Optional[str] = dataclasses.field(default=None, init=False)

    @property
    def dynamic(self) -> bool:
        return False

    def init(self, plot_lib: str):
        self._plot_lib = plot_lib.lower()
        if self._plot_lib == "matplotlib":
            pn_extension = "ipywidgets"

            import matplotlib.pyplot as plt

            # Turn off interactive mode
            # (see https://stackoverflow.com/a/15713545)
            plt.ioff()
        else:
            pn_extension = self._plot_lib

        import panel as pn

        pn.extension(pn_extension)

    def interact(self, func: Callable, **kwargs) -> Any:
        import panel as pn

        if self._plot_lib == "matplotlib":
            import matplotlib.pyplot as plt

            if plt.isinteractive():
                raise RuntimeError(
                    "Please ensure matplotlib interactive mode is off "
                    "(e.g., call %matplotlib inline "
                    "*before* calling leda.init())"
                )

        interact_view = pn.interact(func, **kwargs)
        return interact_view.embed(
            max_states=500, max_opts=500, progress=self.progress
        )

    def process_result(self, obj: Any) -> Any:
        import panel as pn

        if leda.interact.base.is_matplotlib(obj):
            # See https://panel.holoviz.org/reference/panes/Matplotlib.html
            import matplotlib.pyplot as plt

            return pn.pane.Matplotlib(plt.gcf())
        elif leda.interact.base.is_plotly(obj):
            # See https://panel.holoviz.org/reference/panes/Plotly.html
            return pn.pane.Plotly(obj.to_dict())

        return super().process_result(obj)
