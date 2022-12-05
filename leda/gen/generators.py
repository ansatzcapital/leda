from __future__ import annotations

import dataclasses
import datetime
import logging
import os
from typing import Mapping, Optional, Tuple

import jupyter_client.kernelspec
import nbconvert
import nbformat
import termcolor
import tqdm
import traitlets

import leda.gen.base

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ExecutePreprocessorWithProgressBar(
    nbconvert.preprocessors.ExecutePreprocessor
):
    """Small extension to provide progress bar."""

    progress = traitlets.Bool(default_value=False).tag(config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Progress bar state
        self._num_cells: Optional[int] = None
        self._pbar: Optional[tqdm.tqdm] = None

    def preprocess(
        self,
        nb: nbformat.NotebookNode,
        resources: Optional[Mapping] = None,
        km: Optional[jupyter_client.KernelManager] = None,
    ) -> Tuple[nbformat.NotebookNode, Mapping]:
        self._num_cells = len(nb["cells"])

        result = super(ExecutePreprocessorWithProgressBar, self).preprocess(
            nb, resources, km=km
        )
        if self._pbar is not None:
            self._pbar.close()

        return result

    def preprocess_cell(
        self,
        cell: nbformat.NotebookNode,
        resources: Mapping,
        cell_index: int,
        store_history: bool = True,
    ) -> Tuple[nbformat.NotebookNode, Mapping]:
        if self._pbar is None:
            self._pbar = tqdm.tqdm(
                desc="Executing notebook",
                total=self._num_cells,
                disable=not self.progress,
            )

        cell_lines = cell.source.splitlines()
        if cell_lines:
            first_line = termcolor.colored(cell_lines[0], color="green")
        else:
            first_line = ""
        self._pbar.set_postfix_str(first_line)

        # Note that preprocess_cell() will actually run the cell
        result = super(
            ExecutePreprocessorWithProgressBar, self
        ).preprocess_cell(cell, resources, cell_index)
        self._pbar.update(1)

        return result


@dataclasses.dataclass()
class MainStaticReportGenerator(leda.gen.base.ReportGenerator):
    cell_timeout: Optional[datetime.timedelta] = None
    kernel_name: Optional[str] = None
    progress: bool = False

    def _get_preprocessor(self) -> nbconvert.preprocessors.ExecutePreprocessor:
        kwargs = {}

        if self.cell_timeout:
            kwargs["timeout"] = int(self.cell_timeout.total_seconds())

        if self.kernel_name:
            kernel_specs = jupyter_client.kernelspec.find_kernel_specs()
            if self.kernel_name in kernel_specs:
                kwargs["kernel_name"] = self.kernel_name
            else:
                raise ValueError(
                    f"The kernel {self.kernel_name!r} could not be found. "
                    f"Kernel choices: {kernel_specs.keys()}"
                )

        return ExecutePreprocessorWithProgressBar(
            progress=self.progress, **kwargs
        )

    def generate(
        self,
        nb_contents: Mapping,
        nb_name: Optional[str] = None,
    ) -> bytes:
        logger.info("Generating notebook")
        preprocessor = self._get_preprocessor()
        preprocessor.preprocess(
            nb_contents, resources={"metadata": {"path": os.getcwd()}}
        )

        logger.info("Generating HTML")
        exporter = nbconvert.HTMLExporter()
        body, _ = exporter.from_notebook_node(nb_contents)

        logger.info("Modifying HTML")
        if nb_name:
            body = body.replace(
                "<title>Notebook</title>", f"<title>{nb_name}</title>"
            )

        return body.encode(errors="ignore")
