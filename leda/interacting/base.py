import abc
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
        (matplotlib.axes.SubplotBase, matplotlib.artist.Artist),
    )


def is_plotly(obj: Any) -> bool:
    try:
        import plotly.graph_objs as go
    except ImportError:
        return False

    return isinstance(obj, go.Figure)


class InteractMode(abc.ABC):
    @property
    @abc.abstractmethod
    def dynamic(self) -> bool: ...

    def init(self, plot_lib: str) -> None:  # noqa: B027
        pass

    def on_set(self) -> None:  # noqa: B027
        pass

    @abc.abstractmethod
    def interact(self, func: Callable, **kwargs: Any) -> Any: ...

    def process_result(self, obj: Any) -> Any:
        return obj
