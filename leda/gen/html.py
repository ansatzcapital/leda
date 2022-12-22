"""HTML functions."""
from typing import List, Tuple, Union

import IPython.display

Selector = Union[str, Tuple[str, str]]
Selectors = List[Selector]

# NB: These jQuery selectors are designed to work
# with both "classic" (old default) and "lab" (new default) templates.

INPUT_SELECTORS_CLASSIC: Selectors = ["div.input"]
# In 'lab' templates, the input cell and prompt are included in "jp-InputArea",
# but that would also include Markdown output, so we select the
# editor and prompt separately, to match the behavior of the "input"
# class in the 'classic" template.
INPUT_SELECTORS_LAB: Selectors = [
    "div.jp-InputArea-editor",
    "div.jp-InputArea-prompt",
]
INPUT_SELECTORS: Selectors = INPUT_SELECTORS_CLASSIC + INPUT_SELECTORS_LAB

# In 'classic' template, divs for stdout and stderr are clearly labeled
STD_OUTPUT_SELECTORS_CLASSIC: Selectors = [
    "div.output_stdout",
    "div.output_stderr",
]
# In 'lab' template:
#   - stdout has class="jp-OutputArea-output"
#   - stderr has class="jp-OutputArea-output" and
#     data-mime-type="application/vnd.jupyter.stderr"
#   - cell output has class="jp-OutputArea-output jp-OutputArea-executeResult"
STD_OUTPUT_SELECTORS_LAB: Selectors = [
    ("div.jp-RenderedText", ".not('.jp-OutputArea-executeResult')")
]
STD_OUTPUT_SELECTORS: Selectors = (
    STD_OUTPUT_SELECTORS_CLASSIC + STD_OUTPUT_SELECTORS_LAB
)


def show_toggle(
    name: str, selectors: Selectors, desc: str
) -> IPython.display.HTML:
    """Show input toggle.

    Adapted from https://stackoverflow.com/a/40106659.

    Args:
        name
        selectors: JQuery selectors, like "div.input" or "#some-id"
        desc

    Returns:
        Toggle button in HTML.
    """
    if " " in name:
        raise ValueError(name)

    hide_exprs = []
    show_exprs = []
    for selector in selectors:
        if isinstance(selector, str):
            selector = selector
            filterer = ""
        else:
            selector, filterer = selector

        hide_exprs.append(f"$('{selector}'){filterer}.hide();")
        show_exprs.append(f"$('{selector}'){filterer}.show();")

    hide_exprs_str = "\n".join(
        [
            f"            {line}"
            for expr in hide_exprs
            for line in expr.splitlines()
        ]
    )
    show_exprs_str = "\n".join(
        [
            f"            {line}"
            for expr in show_exprs
            for line in expr.splitlines()
        ]
    )

    # Load jQuery, since it's only automatically loaded in "classic" template
    return IPython.display.HTML(
        f"""
<script
  src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js">
</script>

<script>
    show_{name} = true;
    function toggle_{name}() {{
        if (show_{name}) {{
{hide_exprs_str}
        }} else {{
{show_exprs_str}
        }}
        show_{name} = !show_{name};
    }}

    $(document).ready(toggle_{name});
</script>

<form action="javascript:toggle_{name}()">
    <input type="submit" value="Toggle {desc}">
</form>
"""
    )


def show_input_toggle() -> IPython.display.HTML:
    """Show input toggle, which shows/hides input cells."""
    return show_toggle("code", INPUT_SELECTORS, "code")


def show_std_output_toggle() -> IPython.display.HTML:
    """Show std output toggle, which shows/hides std output."""
    return show_toggle("std_output", STD_OUTPUT_SELECTORS, "std output")
