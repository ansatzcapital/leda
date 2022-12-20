from __future__ import annotations

import copy
from typing import Any, Optional, Sequence, Union

import numpy as np


def get_choice_value_str(val: Any) -> str:
    """Need to match javascript string rep."""
    if isinstance(val, str):
        return val
    elif isinstance(val, (int, float, bool)):
        return str(val)
    return str(hash(val))


class StaticWidget:
    """Base Class for Static Widgets."""

    def __init__(
        self, name: Optional[str] = None, divclass: Optional[str] = None
    ):
        self.name = name
        if divclass is None:
            self.divargs = ""
        else:
            self.divargs = f'class:"{divclass}"'

    def html(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.html()

    def _repr_html_(self) -> str:
        return self.html()

    def copy(self) -> StaticWidget:
        return copy.deepcopy(self)

    def renamed(self, name: str) -> StaticWidget:
        if (self.name is not None) and (self.name != name):
            obj = self.copy()
        else:
            obj = self
        obj.name = name
        return obj


class RangeWidget(StaticWidget):
    """Range (slider) widget."""

    slider_html = (
        '<b>{name}:</b> <input type="range" name="{name}" '
        'min="{range[0]}" max="{range[1]}" step="{range[2]}" '
        'value="{default}" style="{style}" '
        'oninput="interactUpdate(this.parentNode);">'
    )

    def __init__(
        self,
        min: int,
        max: int,
        step: int = 1,
        name: Optional[str] = None,
        default: Optional[int] = None,
        width: int = 350,
        divclass: Optional[str] = None,
        show_range: bool = False,
    ):
        StaticWidget.__init__(self, name, divclass)
        self.datarange = (min, max, step)
        self.width = width
        self.show_range = show_range
        if default is None:
            self.default = min
        else:
            self.default = default

    def values(self) -> Sequence[float]:
        min, max, step = self.datarange
        return list(np.arange(min, max + step, step))

    def html(self) -> str:
        style = ""

        if self.width is not None:
            style += f"width:{self.width}px"

        output = self.slider_html.format(
            name=self.name,
            range=self.datarange,
            default=self.default,
            style=style,
        )
        if self.show_range:
            output = " ".join(
                map(str, [self.datarange[0], output, self.datarange[1]])
            )
        return output


class DropDownWidget(StaticWidget):
    select_html = (
        '<b>{name}:</b> <select name="{name}" '
        'onchange="interactUpdate(this.parentNode);"> '
        "{options}"
        "</select>"
    )
    option_html = '<option value="{value}" ' "{selected}>{label}</option>"

    def __init__(
        self,
        values: Sequence[Union[str, int]],
        name: Optional[str] = None,
        labels=None,
        default=None,
        divclass=None,
        delimiter: str = "      ",
    ):
        super().__init__(name, divclass)
        self._values = values
        self.delimiter = delimiter
        if labels is None:
            labels = list(map(str, values))
        elif len(labels) != len(values):
            raise ValueError("length of labels must match length of values")
        self.labels = labels

        self.default = None
        if default is None:
            if values:
                self.default = values[0]
        elif default in values:
            self.default = default
        else:
            raise ValueError("if specified, default must be in values")

    def _single_option(self, label: str, value: Union[str, int]) -> str:
        if value == self.default:
            selected = " selected "
        else:
            selected = ""
        return self.option_html.format(
            label=label, value=get_choice_value_str(value), selected=selected
        )

    def values(self) -> Sequence[Union[str, int]]:
        return self._values

    def html(self) -> str:
        options = self.delimiter.join(
            [
                self._single_option(label, value)
                for (label, value) in zip(self.labels, self._values)
            ]
        )
        return self.select_html.format(name=self.name, options=options)


class RadioWidget(StaticWidget):
    radio_html = (
        '<input type="radio" name="{name}" value="{value}" '
        "{checked} "
        'onchange="interactUpdate(this.parentNode);">'
    )

    def __init__(
        self,
        values: Sequence[str],
        name: Optional[str] = None,
        labels: Optional[Sequence[str]] = None,
        default: Optional[str] = None,
        divclass: Optional[str] = None,
        delimiter: str = "      ",
    ):
        super().__init__(name, divclass)
        self._values = values
        self.delimiter = delimiter

        if labels is None:
            labels = list(map(str, values))
        elif len(labels) != len(values):
            raise ValueError("length of labels must match length of values")
        self.labels = labels

        self.default = None
        if default is None:
            if values:
                self.default = values[0]
        elif default in values:
            self.default = default
        else:
            raise ValueError("if specified, default must be in values")

    def _single_radio(self, value: str) -> str:
        if value == self.default:
            checked = 'checked="checked"'
        else:
            checked = ""
        return self.radio_html.format(
            name=self.name, value=value, checked=checked
        )

    def values(self) -> Sequence[str]:
        return self._values

    def html(self) -> str:
        preface = f"<b>{self.name}:</b> "
        return preface + self.delimiter.join(
            [
                f"{label}: {self._single_radio(value)}"
                for (label, value) in zip(self.labels, self._values)
            ]
        )
