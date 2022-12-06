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

`-i` (`--inject`) is used to inject user code via a new cell prepended to the notebook during generation.

**Note**: `leda` assumes that all code is run in a trusted environment, so please be aware.

### Interaction/Widgets

`leda` provides an `%%interact` [magic](https://ipython.readthedocs.io/en/stable/interactive/magics.html)
that makes it easy to create outputs based on widgets, like:

```python
%%interact mult0=[1,2,3],mult1=[10,100,1000]
df = pd.DataFrame({"a": [1, 2, 3]}) * mult0 * mult1
df.plot(title=f"Foo: {mult0}, {mult1}")
```

There are two types of interact modes: dynamic and static. Dynamic mode is when you're running the Jupyter notebook
live, in which case you will re-compute the cell output every time you select a different `mult`.

In a static mode (using whichever static widget backend is configured), the library will pre-compute
all possible combinations of widget states ([see Cartesian product](https://en.wikipedia.org/wiki/Cartesian_product))
and then render a static HTML report that contains widgets that look and feel like the dynamic widgets
(despite being pre-rendered).

### Report Web UI Server

Unlike [`voila`](https://voila.readthedocs.io/en/stable/using.html), because all report output is **static HTML**,
you can stand up a report web UI server that suits your needs very easily.

For example, you can generate the report to a file, upload that file to a shared location, and then stand
up a bare-bones `nginx` server to serve the files. (Instead of having a two-step of generation + upload,
you could alternatively implement your own `leda.gen.base.ReportPublisher` and create a generation script of your own).

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

These are the version constraint bundles we're currently testing. The most important next task for leda
development would be to (1) automate testing generating reports (reports may contain many random
strs that don't affect the output but make it impossible to do a simple `diff`), and (2) expand
the number of bundles being tested (especially to the newer versions).

(All of these bundles are tested against Linux/macOS/Windows and various python versions.)

| Library          | Bundle 1: ✅ |
|------------------|-------------|
| `ipykernel`      | `== 5.1.*`  |
| `ipython`        | `== 7.16.*` |
| `ipywidgets`     | `== 7.5.*`  |
| `jupyter_client` | `== 6.0.*`  |
| `jupyter_core`   | `== 4.6.*`  |
| `matplotlib`     | `== 2.2.*`  |
| `nbclient`       | N/A         |
| `nbconvert`      | `== 5.6.*`  |
| `nbformat`       | `== 5.0.*`  |
| `notebook`       | `== 6.0.*`  |
| `plotly`         | `== 4.6.*`  |
