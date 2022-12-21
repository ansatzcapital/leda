# leda

Generate static reports with interactive widgets from Jupyter notebooks

[![PyPI version](https://badge.fury.io/py/leda.svg)](https://badge.fury.io/py/leda)
[![PyPI Supported Python Versions](https://img.shields.io/pypi/pyversions/leda.svg)](https://pypi.python.org/pypi/leda/)
[![GitHub Actions (Tests)](https://github.com/ansatzcapital/leda/workflows/Test/badge.svg)](https://github.com/ansatzcapital/leda)

## Quick Start

Generate a static HTML report from a Jupyter notebook:

```bash
python -m leda /path/to/nb.ipynb --output-dir ./outputs/

# Optional args:
python -m leda /path/to/nb.ipynb --output-dir ./outputs/ \
    -i "abc = 123" -k "other_kernel" --cell-timeout 100
```

This will automatically include formatting tweaks, including, e.g., hiding all input code.

See the [**static demos** being served by GitHub Pages](leda/tests/integration/refs).

Think of it like:
- [`voila`](https://voila.readthedocs.io/en/stable/using.html) but static, with no need for live kernels
- [nbconvert](https://github.com/jupyter/nbconvert)/[nbviewer](https://nbviewer.org/) but with interactive widgets
- [pretty-jupyter](https://github.com/JanPalasek/pretty-jupyter) but with interactive widgets

`-i` (`--inject`) arg is used to inject user code (and set report params) via a new cell prepended to the notebook during generation.
And `--template_name`/`--theme` args allow you to choose between `classic`, `lab` (`light`/`dark`), and `lab_narrow` (`light`/`dark`).

**Note**: `leda` assumes that all code is run in a trusted environment, so please be careful.

### Interaction/Widgets

`leda` provides an `%%interact` [magic](https://ipython.readthedocs.io/en/stable/interactive/magics.html)
that makes it easy to create outputs based on widgets, like:

```python
%%interact column=list("abcdefghij");mult=[1, 2, 3]
df = pd.DataFrame(np.random.RandomState(42).rand(100, 10), columns=list("abcdefghij"))
(df[[column]] * mult).plot(figsize=(15, 8), lw=2, title=f\"column={column!r}, mult={mult}\")
```

There are two types of interact modes: dynamic and static. Dynamic mode is when you're running the Jupyter notebook
live, in which case you will re-compute the cell output every time you select a different `mult`.

In a static mode (using whichever static widget backend is configured), the library will pre-compute
all possible combinations of widget states ([see Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product))
and then render a static HTML report that contains widgets that look and feel like the dynamic widgets
(despite being pre-rendered).

### Report Web UI Server

Unlike [`voila`](https://voila.readthedocs.io/en/stable/using.html), because all report output is **static HTML**,
you can stand up a report web UI server that suits your needs very easily. That means:
- It's trivial to set up in many cases.
- It's as scalable as your web server.
- It's more cost-efficient because there are no runtimes whatsoever.
- You don't have to worry about old versions no longer working due to code or data changes, so the historical
archive of old reports never expire or change or break.

For example, you can generate the report to a file, upload that file to a shared location, and then stand
up a bare-bones `nginx` server to serve the files. (Instead of having a two-step of generation + upload,
you could alternatively implement your own `leda.gen.base.ReportPublisher` and create a generation script of your own).

Another example is you can simply host a static S3 bucket, enable website hosting and then either use S3 as a web server publically or via locked down S3 endpoint.

You could also use [GitHub Pages](https://pages.github.com), much like the [static demos page](leda/tests/integration/refs).

### Params

Reports can be parametrized so that the user can set different values for each report run.

In the notebook, just use `leda.get_param()`:

```python
data_id = leda.get_param("data_id", dynamic_default=1, static_default=2)
```

And then change the injected code during each run:

```bash
python -m leda /path/to/nb.ipynb --output ./outputs/ -i "data_id = 100"
```

### Modular

`leda` is built to work with multiple visualization and widget libraries.

Works with these visualization libraries:
- [`matplotlib`](https://matplotlib.org/)
- [`plotly`](https://plotly.com/python/)

With the default dynamic widget library:
- [`ipywidgets`](https://ipywidgets.readthedocs.io/en/stable/)

And with these static widget libraries:
- [`static_ipywidgets`](https://github.com/jakevdp/ipywidgets-static) (vendored and modified)
- [`panel`](https://panel.holoviz.org/)

## Testing

See the `requirements-bundle*.txt` for version bundles that we currently test systematically.

## Known Issues

- There are multiple issues using `matplotlib` with `panel`, including:
  - The last widget output is not different from the penultimate one: https://github.com/holoviz/panel/issues/1222
  - All the widget outputs show up sequentially, instead of being hidden until chosen. This seems to be a known issue per the [`panel` FAQ](https://panel.holoviz.org/FAQ.html); however, using the example fix provided does not work.
