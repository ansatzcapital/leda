import dataclasses
import logging
import pathlib
from typing import Optional

import leda.gen.base

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def log_loudly(report_url: str):
    logger.info("*****************************************************")
    logger.info("Report available at: %s", report_url)
    logger.info("*****************************************************")


@dataclasses.dataclass()
class InMemoryReportPublisher(leda.gen.base.ReportPublisher):
    artifact: Optional[leda.gen.base.ReportArtifact] = None

    def publish(
        self,
        report: leda.gen.base.Report,
        artifact: leda.gen.base.ReportArtifact,
    ):
        self.artifact = artifact


@dataclasses.dataclass()
class FileReportPublisher(leda.gen.base.ReportPublisher):
    output_dir: pathlib.Path

    def publish(
        self,
        report: leda.gen.base.Report,
        artifact: leda.gen.base.ReportArtifact,
    ):
        logger.info("Publishing %r to %s", report.name, self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        index_path = self.output_dir / "index.html"
        index_path.write_bytes(artifact.body)

        image_path = self.output_dir / "images"
        for image_filename, image_body in artifact.images.items():
            (image_path / image_filename).write_bytes(image_body)

        report_url = str(index_path)
        log_loudly("file://" + report_url)
        return report_url
