import dataclasses
from typing import Any

import IPython

import leda.interact.core


def get_param(
    name: str,
    dynamic_default: Any = dataclasses.MISSING,
    static_default: Any = dataclasses.MISSING,
    default: Any = dataclasses.MISSING,
) -> Any:
    user_ns = IPython.get_ipython().user_ns
    if name in user_ns:
        return user_ns[name]

    dynamic_mode = leda.interact.core.get_interact_mode().dynamic

    if default is not dataclasses.MISSING:
        return default
    elif dynamic_default is not dataclasses.MISSING and dynamic_mode:
        return dynamic_default
    elif static_default is not dataclasses.MISSING and not dynamic_mode:
        return static_default

    raise NameError(name)
