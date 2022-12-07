"""Plotly tools to render static HTML.

Adapted from https://github.com/plotly/plotlyhtmlexporter, which can't be
used with the static widgets natively.

Template changes:
  - Include unique_div_id in figure id
"""
import os
import uuid
from typing import Tuple

import jinja2
import plotly.graph_objects as go

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "plotly_figure.tpl")


def get_figure_size(fig: go.Figure) -> Tuple[int, int]:
    """Get figure size based on traces.

    Args:
        fig

    Returns:
        Width, height.
    """
    total_str_len = sum(
        len(t.name) for t in fig.select_traces() if t.name is not None
    )
    if total_str_len > 250:
        height = 950
    else:
        height = 600

    # Seems to fit nicely in default jupyter template
    width = 850

    return width, height


def figure_to_html(fig: go.Figure, display: bool = False) -> str:
    """Convert figure to HTML.

    Args:
        fig
        display

    Returns:
        HTML that can be used in static widgets.
    """
    with open(TEMPLATE_PATH, "r") as fh:
        jinja_template = jinja2.Template(fh.read())

    width, height = get_figure_size(fig)

    return jinja_template.render(
        unique_div_id=uuid.uuid4(),
        figure=fig.to_json(),
        width=width,
        height=height,
        display=display,
    )
