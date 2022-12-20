import base64
import itertools
import os
from typing import Any, Union

import IPython
import markdown2
import plotly.graph_objects as go
import tqdm

from leda.vendor.static_ipywidgets.static_ipywidgets import (
    static_plotly_utils,
    widgets,
)

IMAGE_MANAGER = None


class ImageManager:
    def add_image(
        self, div_name: str, obj: Union[bytes, str], disp: bool = False
    ) -> str:
        """Adds image and returns source to include in HTML.

        Args:
            div_name
            obj: Image contents (either bytes or in base64 str).
            disp: Whether to display this image or not.

        Returns:
            Image tag.
        """
        raise NotImplementedError()


class InlineImageManager(ImageManager):
    def add_image(
        self, div_name: str, obj: Union[bytes, str], disp: bool = False
    ) -> str:
        if isinstance(obj, bytes):
            encoded = base64.standard_b64encode(obj).decode("ascii")
        else:
            encoded = obj

        return f'<img src="data:image/png;base64,{encoded}">'


class FileImageManager(ImageManager):
    def __init__(self, path: str):
        self.path = path

    def _get_bytes(self, obj: Union[bytes, str]) -> bytes:
        if isinstance(obj, bytes):
            return obj
        else:
            return base64.standard_b64decode(obj)

    def add_image(
        self, div_name: str, obj: Union[bytes, str], disp: bool = False
    ) -> str:
        # Get image bytes
        obj = self._get_bytes(obj)

        # Clean image filename for S3
        div_name = div_name.replace("<", "").replace(">", "").replace(":", "")
        img_filename = div_name + ".png"

        # Save to disk; to be uploaded somewhere else later
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        img_path = os.path.join(self.path, img_filename)
        with open(img_path, "wb") as fh:
            fh.write(obj)

        # Return tag with src-less image to enable downloading
        # images on demand. data_src tag will later be used to fill in src,
        # as needed by user.
        data_src = f"images/{img_filename}"
        img_src = data_src if disp else "#"
        return f'<img src="{img_src}" data_src="{data_src}">'


def _get_html(
    img_manager: ImageManager, div_name: str, obj: Any, disp: bool = False
) -> str:
    """Get the HTML representation of an object."""
    # Prevent trying to load Tkinter at import time
    import matplotlib.pyplot as plt

    # Note that figures in plotly>=4.8.0 do have _repr_html_()
    if isinstance(obj, go.Figure):
        return static_plotly_utils.figure_to_html(obj, display=disp)

    # TODO: use displaypub to make this more general
    # We want to short-circuit this function if we get e.g. a DataFrame
    # TODO: Note that the JS below isn't great because it hides all divs,
    #  so we just remove any divs in the obj's HTML, for now
    if hasattr(obj, "_repr_html_") and obj._repr_html_():
        return obj._repr_html_().replace("<div>", "").replace("</div>", "")
    elif hasattr(obj, "_repr_markdown_"):
        return markdown2.Markdown().convert(obj._repr_markdown_())

    ip = IPython.get_ipython()

    png_rep = ip.display_formatter.formatters["image/png"](obj)
    if png_rep is not None:
        if isinstance(obj, plt.Figure):
            plt.close(obj)  # Keep from displaying twice
        img_tag = img_manager.add_image(div_name, png_rep, disp=disp)
        return img_tag

    html_rep = ip.display_formatter.formatters["text/html"](obj)
    if html_rep is not None:
        return html_rep

    return f"<p> {str(obj)} </p>"


class StaticInteract:
    """Static Interact Object."""

    template = """
    <script type="text/javascript">
      var mergeNodes = function(a, b) {{
        return [].slice.call(a).concat([].slice.call(b));
      }}; // http://stackoverflow.com/questions/914783/javascript-nodelist/17262552#17262552
      function interactUpdate(div){{
         var outputs = div.getElementsByTagName("div");
         //var controls = div.getElementsByTagName("input");
         var controls = mergeNodes(div.getElementsByTagName("input"), div.getElementsByTagName("select"));
         function nameCompare(a,b) {{
            return a.getAttribute("name").localeCompare(b.getAttribute("name"));
         }}
         controls.sort(nameCompare);

         var value = "";
         for(i=0; i<controls.length; i++){{
           if((controls[i].type == "range") || controls[i].checked){{
             value = value + controls[i].getAttribute("name") + controls[i].value;
           }}
           if(controls[i].type == "select-one"){{
             value = value + controls[i].getAttribute("name") + controls[i][controls[i].selectedIndex].value;
           }}
         }}
         value = "subdiv-" + value;

         var oldDivs = [];
         var oldTraces = null;
         for(i=0; i<outputs.length; i++){{
           var name = outputs[i].getAttribute("name");
           if(!name || !name.startsWith("subdiv-")) {{
             continue;
           }}
           if(name == value){{
              newDiv = outputs[i];
           }} else if(name != "controls"){{
              oldDivs.push(outputs[i]);

              if (outputs[i].style.display == "block") {{
                oldChildDivs = outputs[i].getElementsByTagName("div");
                for (j = 0; j < oldChildDivs.length; j++) {{
                  if (oldChildDivs[j].hasAttribute("plotly_id")) {{
                    oldPlotlyId = oldChildDivs[j].getAttribute("plotly_id");
                    oldTraces = document.getElementById(oldPlotlyId).data;
                  }}
                }}
              }}
           }}
         }}

         // Load plotly figure
         // TODO: Support animating frames. See plotly_figure.tpl.
         childDivs = newDiv.getElementsByTagName("div");
         for (j = 0; j < childDivs.length; j++) {{
           if (childDivs[j].hasAttribute("plotly_id")) {{
             var plotlyId = childDivs[j].getAttribute("plotly_id");
             var figure = JSON.parse(document.getElementById('figure-' + plotlyId).innerText);
             Plotly.newPlot(plotlyId, figure.data, figure.layout);

             // This is to preserve plotly legend selections across
             // widgets.
             // Adapted from https://stackoverflow.com/a/59286599.
             var plotlyDiv = document.getElementById(plotlyId);
             var newTraces = document.getElementById(plotlyId).data;
             var restyleVisibles = [];
             var restyleIndices = [];
             if ((oldTraces != null) && (oldTraces.length == newTraces.length)) {{
               for (k = 0; k < oldTraces.length; k++) {{
                 if (oldTraces[k]["name"] == newTraces[k]["name"]) {{
                   if ("visible" in oldTraces[k]) {{
                     restyleVisibles.push(oldTraces[k]["visible"]);
                     restyleIndices.push(k);
                   }}
                 }}
               }}
             }}
             Plotly.restyle(plotlyDiv, {{"visible": restyleVisibles}}, restyleIndices);
           }}
         }}

         // Preload the image and show when it's ready
         // From https://stackoverflow.com/a/19396463
         imgs = newDiv.getElementsByTagName("img");
         if(imgs.length > 0){{
           for(j=0; j<imgs.length; j++){{
             // External images have data_src; inline images do not
             if(imgs[j].hasAttribute("data_src")) {{
               var newImgSrc = imgs[j].getAttribute("data_src");

               // For more on closures in loops and let keyword:
               // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures
               let newDivCapture = newDiv;
               let oldDivsCapture = oldDivs;
               let oldImg = imgs[j];
               let newImg = new Image;
               newImg.onload = function(){{
                 oldImg.src = newImgSrc;
                 newDivCapture.style.display = 'block';
                 for(k=0; k<oldDivsCapture.length; k++){{
                   oldDivsCapture[k].style.display = 'none';
                 }}
               }};
               newImg.src = newImgSrc;
             }} else {{
               newDiv.style.display = 'block';
               for(k=0; k<oldDivs.length; k++){{
                 oldDivs[k].style.display = 'none';
               }}
             }}
           }}
         }} else {{
           newDiv.style.display = 'block';
           for(k=0; k<oldDivs.length; k++){{
             oldDivs[k].style.display = 'none';
           }}
         }}
      }}
    </script>

    <div>
      {outputs}
      {widgets}
    </div>
    """

    subdiv_template = """
    <div name="subdiv-{name}" style="display:{display}">
      {content}
    </div>
    """

    def __init__(self, function, **kwargs):
        # TODO: implement *args (difficult because of the name thing)
        # update names
        for name in kwargs:
            kwargs[name] = kwargs[name].renamed(name)

        self.widgets = dict(kwargs)
        self.function = function
        self.img_manager = (
            IMAGE_MANAGER
            if IMAGE_MANAGER is not None
            else InlineImageManager()
        )

    def _output_html(self):
        names = [name for name in self.widgets]
        values = [list(widget.values()) for widget in self.widgets.values()]
        defaults = tuple([widget.default for widget in self.widgets.values()])

        # Now reorder alphabetically by names so divnames match javascript
        names, values, defaults = list(
            zip(*sorted(zip(names, values, defaults)))
        )

        all_values = list(itertools.product(*values))
        results = []
        for vals in tqdm.tqdm(
            all_values, total=len(all_values), desc="Generating results"
        ):
            results.append(self.function(**dict(list(zip(names, vals)))))

        divnames = [
            "".join(
                [
                    f"{n}{widgets.get_choice_value_str((v))}"
                    for n, v in zip(names, vals)
                ]
            )
            for vals in itertools.product(*values)
        ]
        display = [vals == defaults for vals in itertools.product(*values)]

        tmplt = self.subdiv_template
        result_parts = []
        for divname, result, disp in tqdm.tqdm(
            list(zip(divnames, results, display)),
            total=len(results),
            desc="Generating HTML",
        ):
            result_parts.append(
                tmplt.format(
                    name=divname,
                    display="block" if disp else "none",
                    content=_get_html(
                        self.img_manager,
                        f"{id(self)}-{divname}",
                        result,
                        disp=disp,
                    ),
                )
            )
        return "".join(result_parts)

    def _widget_html(self):
        return "\n<br>\n".join(
            [widget.html() for name, widget in sorted(self.widgets.items())]
        )

    def html(self):
        return self.template.format(
            outputs=self._output_html(), widgets=self._widget_html()
        )

    def _repr_html_(self):
        return self.html()
