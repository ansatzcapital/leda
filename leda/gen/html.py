"""HTML functions."""
from typing import List

import IPython.display


def show_toggle(
    name: str, selectors: List[str], desc: str
) -> IPython.display.HTML:
    """Show input toggle.

    Args:
        name
        selectors: JQuery selectors, like "div.input" or "#some-id"
        desc

    Returns:
        Toggle button in HTML.
    """
    assert " " not in name

    hide_lines = []
    show_lines = []
    for selector in selectors:
        hide_lines.append(f"$('{selector}').hide();")
        show_lines.append(f"$('{selector}').show();")

    hide_lines_str = "\n".join(hide_lines)
    show_lines_str = "\n".join(show_lines)

    body = f"""<script>
show_{name} = true;

function toggle_{name}() {{
  if (show_{name}) {{
    {hide_lines_str}
  }} else {{
    {show_lines_str}
  }}

  show_{name} = !show_{name};
}}
$(document).ready(toggle_{name});
</script>
<form action="javascript:toggle_{name}()">
<input type="submit" value="Toggle {desc}"></form>"""
    return IPython.display.HTML(body)


def show_input_toggle() -> IPython.display.HTML:
    """Show input toggle, which shows/hides input cells.

    See https://stackoverflow.com/a/28073228.
    """
    return show_toggle("input", ["div.input"], "input cells")


def show_std_output_toggle() -> IPython.display.HTML:
    """Show std output toggle, which shows/hides std output.

    See https://stackoverflow.com/a/28073228.
    """
    return show_toggle(
        "std_output",
        ["div.output_stderr", "div.output_stdout"],
        "std output",
    )
