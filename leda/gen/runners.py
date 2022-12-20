from __future__ import annotations

import dataclasses
import logging
import pathlib
from typing import Optional, Union, cast

import nbformat

import leda.gen.base
import leda.gen.generators
import leda.gen.modifiers
import leda.gen.publishers

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclasses.dataclass()
class MainReportRunner(leda.gen.base.ReportRunner):
    modifier: leda.gen.base.ReportModifier
    generator: leda.gen.base.ReportGenerator
    publisher: leda.gen.base.ReportPublisher

    def run(self, report: leda.gen.base.Report) -> Optional[str]:
        nb_contents = nbformat.read(report.handle, as_version=4)

        self.modifier.modify(nb_contents)

        body = self.generator.generate(nb_contents, nb_name=report.name)
        artifact = leda.gen.base.ReportArtifact(body)

        return self.publisher.publish(report, artifact)

    @classmethod
    def get_default_runner(
        cls,
        report: Union[pathlib.Path, leda.gen.base.Report],
        local_dir_path: pathlib.Path,
        static_interact_mode_alias: str,
        kernel_name: Optional[str] = None,
        progress: bool = False,
        template_name: Optional[str] = None,
        theme: Optional[str] = None,
    ) -> MainReportRunner:
        if isinstance(report, pathlib.Path):
            report = leda.gen.base.FileReport(name=report.stem, nb_path=report)

        output_dir_path = local_dir_path / cast(str, report.full_name)

        modifier: leda.gen.base.ReportModifier
        if static_interact_mode_alias == "static_ipywidgets":
            modifier = leda.gen.modifiers.StaticIpywidgetsReportModifier(
                output_dir_path
            )
        elif static_interact_mode_alias == "panel":
            modifier = leda.gen.modifiers.StaticPanelReportModifier()
        else:
            raise ValueError(
                f"Unknown static interact mode: {static_interact_mode_alias!r}"
            )

        generator = leda.gen.generators.MainStaticReportGenerator(
            cell_timeout=report.cell_timeout,
            kernel_name=kernel_name,
            progress=progress,
            template_name=template_name,
            theme=theme,
        )

        publisher = leda.gen.publishers.FileReportPublisher(
            output_dir=output_dir_path
        )

        return MainReportRunner(
            modifier=modifier,
            generator=generator,
            publisher=publisher,
        )
