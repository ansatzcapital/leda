from typing import Any, Callable


# noinspection PyProtectedMember
def is_matplotlib(obj: Any) -> bool:
    try:
        import matplotlib.axes._base
    except ImportError:
        return False

    try:
        import matplotlib.artist
    except ImportError:
        return False

    return isinstance(
        obj,
        (
            matplotlib.axes.SubplotBase,  # pyright: ignore
            matplotlib.artist.Artist,
        ),
    )


def is_plotly(obj: Any) -> bool:
    try:
        import plotly.graph_objs as go
    except ImportError:
        return False

    return isinstance(obj, go.Figure)


class InteractMode:
    @property
    def dynamic(self) -> bool:
        raise NotImplementedError

    def init(self, plot_lib: str):
        pass

    def on_set(self):
        pass

    def interact(self, func: Callable, **kwargs) -> Any:
        raise NotImplementedError

    def process_result(self, obj: Any) -> Any:
        return obj
