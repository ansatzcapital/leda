from __future__ import annotations

from typing import Any, Callable

import IPython

import leda.interacting.base
import leda.interacting.dynamic

GLOBAL_INTERACT_MODE: leda.interacting.base.InteractMode = (
    leda.interacting.dynamic.DynamicIpywidgetsInteractMode()
)
GLOBAL_INTERACT_MODE.on_set()


def get_interact_mode() -> leda.interacting.base.InteractMode:
    global GLOBAL_INTERACT_MODE
    return GLOBAL_INTERACT_MODE


def set_interact_mode(
    interact_mode: leda.interacting.base.InteractMode,
) -> None:
    global GLOBAL_INTERACT_MODE
    GLOBAL_INTERACT_MODE = interact_mode
    GLOBAL_INTERACT_MODE.on_set()


def init(plot_lib: str) -> None:
    # Register cell magics (dynamically, because we need to check
    # that we're in an ipython session)
    if IPython.get_ipython():
        import leda.interacting.magics  # noqa: F401

    get_interact_mode().init(plot_lib)


def interact(func: Callable, **kwargs: Any) -> Any:
    """Return object that displays Cartesian product of kwarg inputs.

    E.g.:

    >>> import pandas as pd  # doctest: +SKIP
    >>> def foo(x: int, y: float) -> object:  # doctest: +SKIP
    ...     df = pd.DataFrame({"a": [x * y]})
    ...     return df.plot()
    >>> interact(foo, x=[1, 2, 3], y=(1.0, 2.0))  # doctest: +SKIP
    interactive(...)

    Equivalent to the `%%interact` magic.
    """
    return get_interact_mode().interact(func, **kwargs)
