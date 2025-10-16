## Summary

[GitHub](https://github.com/ansatzcapital/leda)

[Packaging](https://pypi.org/project/leda)

This pages demonstrates how `leda` can transform Jupyter notebooks into static reports. 

Note that this site is being served by [GitHub Pages](https://pages.github.com/), which only serves *static* content, yet you can interact with the pre-defined widgets as if a live kernel were running.

All reports were generated via:

```bash
python -m leda ./leda/demos/${NAME}.ipynb \
  --output /tmp/leda_outputs/ \
  --static-interact-mode static_ipywidgets \
  --template ${TEMPLATE} --theme ${THEME}
```

### basic_demo.ipynb

[Original Notebook](https://github.com/ansatzcapital/leda/tree/main/leda/demos/basic_demo.ipynb)

| Link                                                                       | Template   | Theme |
|----------------------------------------------------------------------------|------------|-------|
| [Static Report](basic_demo-static_ipywidgets-bundle4-classic-light.html)   | classic    | light |
| [Static Report](basic_demo-static_ipywidgets-bundle4-lab-light.html)       | lab        | light |
| [Static Report](basic_demo-static_ipywidgets-bundle4-lab_narrow-dark.html) | lab_narrow | dark  |

### matplotlib_demo.ipynb

[Original Notebook](https://github.com/ansatzcapital/leda/tree/main/leda/demos/matplotlib_demo.ipynb)

| Link                                                                            | Template   | Theme |
|---------------------------------------------------------------------------------|------------|-------|
| [Static Report](matplotlib_demo-static_ipywidgets-bundle4-classic-light.html)   | classic    | light |
| [Static Report](matplotlib_demo-static_ipywidgets-bundle4-lab-light.html)       | lab        | light |
| [Static Report](matplotlib_demo-static_ipywidgets-bundle4-lab_narrow-dark.html) | lab_narrow | dark  |

### plotly_demo.ipynb

[Original Notebook](https://github.com/ansatzcapital/leda/tree/main/leda/demos/plotly_demo.ipynb)

| Link                                                                        | Template   | Theme |
|-----------------------------------------------------------------------------|------------|-------|
| [Static Report](plotly_demo-static_ipywidgets-bundle4-classic-light.html)   | classic    | light |
| [Static Report](plotly_demo-static_ipywidgets-bundle4-lab-light.html)       | lab        | light |
| [Static Report](plotly_demo-static_ipywidgets-bundle4-lab_narrow-dark.html) | lab_narrow | dark  |
