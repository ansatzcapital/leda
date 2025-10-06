from __future__ import annotations

import dataclasses
import logging
import pathlib

from typing_extensions import override

import leda.gen.base

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def log_loudly(report_url: str) -> None:
    logger.info("*****************************************************")
    logger.info("Report available at: %s", report_url)
    logger.info("*****************************************************")


@dataclasses.dataclass()
class InMemoryReportPublisher(leda.gen.base.ReportPublisher):
    artifact: leda.gen.base.ReportArtifact | None = None

    @override
    def publish(
        self,
        report: leda.gen.base.Report,
        artifact: leda.gen.base.ReportArtifact,
    ) -> None:
        self.artifact = artifact


@dataclasses.dataclass()
class FileReportPublisher(leda.gen.base.ReportPublisher):
    output_dir: pathlib.Path

    def _log_loudly(self, report_url: str) -> None:
        """Log final report URL loudly to user.

        Child classes may find it useful to override this method to,
        e.g., set a different default URL protocol and prefix.
        """
        log_loudly("file://" + report_url)

    @override
    def publish(
        self,
        report: leda.gen.base.Report,
        artifact: leda.gen.base.ReportArtifact,
    ) -> str | None:
        logger.info("Publishing %r to %s", report.name, self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        index_path = self.output_dir / "index.html"
        index_path.write_bytes(artifact.body)

        image_path = self.output_dir / "images"
        for image_filename, image_body in artifact.images.items():
            (image_path / image_filename).write_bytes(image_body)

        report_url = str(index_path)
        self._log_loudly(report_url)
        return report_url
