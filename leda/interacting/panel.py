import dataclasses
import sys
from typing import Any, Callable, Optional

from typing_extensions import override

import leda.interacting.base


@dataclasses.dataclass()
class StaticPanelInteractMode(leda.interacting.base.InteractMode):
    progress: bool = False

    _plot_lib: Optional[str] = dataclasses.field(default=None, init=False)

    @property
    @override
    def dynamic(self) -> bool:
        return False

    @override
    def init(self, plot_lib: str) -> None:
        self._plot_lib = plot_lib.lower()
        if self._plot_lib == "matplotlib":
            pn_extension = "ipywidgets"

            import matplotlib.pyplot as plt

            # Turn off interactive mode
            # (see https://stackoverflow.com/a/15713545).
            plt.ioff()
        elif self._plot_lib == "plotly":
            pn_extension = self._plot_lib

            import plotly.offline

            # Set online mode (i.e., load plotly.js from web).
            plotly.offline.init_notebook_mode(connected=True)
        else:
            raise ValueError(self._plot_lib)

        import panel as pn

        if sys.version_info >= (3, 10):
            set_pn_extension = pn.extension
        else:

            def set_pn_extension(value: str, safe_embed: bool) -> None:
                pn.extension(value, safe_embed=safe_embed)  # type: ignore[unused-ignore]

        set_pn_extension(pn_extension, safe_embed=True)

    @override
    def interact(self, func: Callable, **kwargs: Any) -> Any:
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
        return interact_view.embed(  # pyright: ignore
            max_states=500, max_opts=500, progress=self.progress
        )

    @override
    def process_result(self, obj: Any) -> Any:
        import panel as pn

        if leda.interacting.base.is_matplotlib(obj):
            # See https://panel.holoviz.org/reference/panes/Matplotlib.html.
            import matplotlib.pyplot as plt

            return pn.pane.Matplotlib(plt.gcf())
        elif leda.interacting.base.is_plotly(obj):
            # See https://panel.holoviz.org/reference/panes/Plotly.html.
            return pn.pane.Plotly(obj.to_dict())

        return super().process_result(obj)
