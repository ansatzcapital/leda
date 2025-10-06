# leda

Generate static HTML reports with interactive widgets from Jupyter notebooks

[![PyPI version](https://badge.fury.io/py/leda.svg)](https://badge.fury.io/py/leda)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/leda.svg)](https://pypi.python.org/pypi/leda/)
[![GitHub Actions (Tests)](https://github.com/ansatzcapital/leda/workflows/Test/badge.svg)](https://github.com/ansatzcapital/leda)

## Installation

`leda` is available on [PyPI](https://pypi.org/project/leda/):

```bash
pip install leda
```

## Quick Start

### Generation

To generate a static HTML report from a Jupyter notebook, run:

```bash
python -m leda /path/to/nb.ipynb --output-dir ./outputs/

# Optional args:
python -m leda /path/to/nb.ipynb --output-dir ./outputs/ \
    -i "abc = 123" -k "other_kernel" --cell-timeout 100
```

This generation automatically includes tweaks to the notebook to make
the output look more report-like (e.g., hiding all input code)

See the [**static demos**](https://ansatzcapital.github.io/leda/examples/output_refs/)
being served by GitHub Pages.

`leda` is like:
- [`voila`](https://voila.readthedocs.io/en/stable/using.html),
but static, with no need for live kernels
- [`quarto`](https://quarto.org/), but with static interactive widgets
- [`nbconvert`](https://github.com/jupyter/nbconvert)/
[`nbviewer`](https://nbviewer.org/), but self-hosted, designed for reports,
and with static interactive widgets
- [`papermill`](https://papermill.readthedocs.io/en/latest/),
but designed for reports and with static interactive widgets
- [`pretty-jupyter`](https://github.com/JanPalasek/pretty-jupyter),
but with static interactive widgets

The `-i` (`--inject`) arg is used to inject user code (and set report params)
via a new cell prepended to the notebook during generation.

And the `--template_name`/`--theme` args allow you to choose between
`classic`, `lab` (`light`/`dark`), and `lab_narrow` (`light`/`dark`).

**Note**: `leda` assumes that all code is run in a trusted environment,
so please be careful.

### Interaction/Widgets

`leda` also provides an `%%interact` [magic](https://ipython.readthedocs.io/en/stable/interactive/magics.html)
that makes it easy to create outputs based on widgets that work in both dynamic
and static modes, e.g.:

```python
# In[ ]:


import leda
import numpy as np
import pandas as pd


# In[ ]:


# Loads `interact` magic when running in Jupyter notebook.
leda.init("matplotlib")


# In[ ]:


%%interact column=list("abcdefghij");mult=[1, 2, 3]
df = pd.DataFrame(
  np.random.RandomState(42).rand(100, 10), columns=list("abcdefghij")
)
title = f"column={column!r}, mult={mult}"
(df[[column]] * mult).plot(figsize=(15, 8), lw=2, title=title)
```

There are two types of interact modes: dynamic and static.

**Dynamic mode** is when you're running the Jupyter notebook
live, in which case you will re-compute the cell output
every time you select a different `mult`. We always use
[`ipywidgets`](https://ipywidgets.readthedocs.io/en/stable/) as the
dynamic widget backend.

In **static mode** (using whichever static widget backend is configured),
the library will pre-compute all possible combinations of widget outputs
([see Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product))
and then render a static HTML report that contains widgets
that look and feel like the dynamic widgets (despite being pre-rendered).
See below for a list of supported static backends.

The non-magic equivalent of the last cell would be:

```python
def func(column: str, mult: int) -> object:
    df = pd.DataFrame(
        np.random.RandomState(42).rand(100, 10), columns=list("abcdefghij")
    )
    title = f"column={column!r}, mult={mult}"
    return (df[[column]] * mult).plot(figsize=(15, 8), lw=2, title=title)


leda.interact(func, column=list("abcdefghij"), mult=[1, 2, 3])
```

### Report Web UI Server

Unlike [`voila`](https://voila.readthedocs.io/en/stable/using.html),
because all report output is _static HTML_,
you can stand up a report web UI server that suits your needs very easily.
That means:
- It's trivial to set up in many cases.
- It's as scalable as your web server's ability to distribute static content.
- It's more cost-efficient because there are no runtimes whatsoever.
- You don't have to worry about old versions no longer working
due to code or data changes, so the historical
archive of old reports never expires or changes or breaks.

For example, you can generate the report to a file,
upload that file to a shared location, and then stand
up a bare-bones `nginx` server to serve the files.
Instead of having a two-step process of generation + upload,
you could alternatively implement your own `leda.ReportPublisher`
and create a generation script of your own--or use it as a library
in client script.

Another example is you can simply host a static S3 bucket,
enable website hosting and then either use S3 as a web server
publically or via locked down S3 endpoint.

You could also use [GitHub Pages](https://pages.github.com),
much like the [static demos page](https://ansatzcapital.github.io/leda/examples/output_refs/).

### Params

Reports can be parametrized so that the user can set
different values for each report run.

In the notebook, just use `leda.get_param()`:

```python
# In[ ]:


import leda


# In[ ]:


data_id = leda.get_param("data_id", dynamic_default=1, static_default=2)
```

And then change the injected code during each run:

```bash
python -m leda /path/to/nb.ipynb --output ./outputs/ -i "data_id = 100"
```

### Modular

`leda` is built to work with multiple visualization and widget libraries.

It works with these visualization libraries:
- [`matplotlib`](https://matplotlib.org/)
- [`plotly`](https://plotly.com/python/)

With the default dynamic widget library:
- [`ipywidgets`](https://ipywidgets.readthedocs.io/en/stable/)

And with these static widget libraries:
- [`static_ipywidgets`](https://github.com/jakevdp/ipywidgets-static)
(vendored and modified)
- [`panel`](https://panel.holoviz.org/)

## Testing

See the integration test environments in `pixi.toml` for version bundles
that we currently test systematically.

## Known Issues

- There are multiple issues using `matplotlib` with `panel`, including:
  - The last widget output is not different from the penultimate one: https://github.com/holoviz/panel/issues/1222
  - All the widget outputs show up sequentially,
    instead of being hidden until chosen.
    This seems to be a known issue per the [`panel` FAQ](https://panel.holoviz.org/FAQ.html);
    however, using the example fix provided does not work.
