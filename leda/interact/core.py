from __future__ import annotations

import IPython

import leda.interact.base
import leda.interact.dynamic

GLOBAL_INTERACT_MODE: leda.interact.base.InteractMode = (
    leda.interact.dynamic.DynamicIpywidgetsInteractMode()
)
GLOBAL_INTERACT_MODE.on_set()


def get_interact_mode() -> leda.interact.base.InteractMode:
    global GLOBAL_INTERACT_MODE
    return GLOBAL_INTERACT_MODE


def set_interact_mode(interact_mode: leda.interact.base.InteractMode):
    global GLOBAL_INTERACT_MODE
    GLOBAL_INTERACT_MODE = interact_mode
    GLOBAL_INTERACT_MODE.on_set()


def init(plot_lib: str):
    # Register cell magics (dynamically, because we need to check
    # that we're in a ipython session)
    if IPython.get_ipython():
        import leda.interact.magics  # noqa: F401

    get_interact_mode().init(plot_lib)
