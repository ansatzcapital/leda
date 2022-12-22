from __future__ import annotations

import dataclasses
import datetime
import logging
import pathlib
from typing import IO, Any, List, Mapping, Optional, Union

import cached_property
import nbformat

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclasses.dataclass(frozen=True)
class Report:
    name: str

    tag: Optional[str] = None

    params: Optional[Mapping[str, Any]] = None
    additional_inject_code: Optional[str] = None

    cell_timeout: Optional[datetime.timedelta] = None

    @cached_property.cached_property
    def full_name(self) -> str:
        if self.tag:
            parts = [self.name, self.tag]
        else:
            parts = [self.name]

        parts.append(datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))

        return "-".join(parts)

    @property
    def handle(self) -> Union[str, IO]:
        raise NotImplementedError

    @cached_property.cached_property
    def inject_code(self) -> Optional[str]:
        if not self.params and not self.additional_inject_code:
            return None

        lines = []

        if self.params:
            for key, value in self.params.items():
                if isinstance(
                    value, (type(None), bool, int, float, str, list)
                ):
                    line = f"{key} = {value!r}"
                else:
                    raise TypeError(f"{key!r}: {type(value)}")

                lines.append(line)

        if self.additional_inject_code:
            lines += [self.additional_inject_code]

        return "\n".join(lines)


@dataclasses.dataclass(frozen=True)
class _FileReport:
    nb_path: pathlib.Path


@dataclasses.dataclass(frozen=True)
class FileReport(Report, _FileReport):
    @property
    def handle(self) -> Union[str, IO]:
        logger.info("Reading %s", self.nb_path)
        return str(self.nb_path.expanduser())


@dataclasses.dataclass(frozen=True)
class ReportSet:
    reports: List[Report] = dataclasses.field(hash=False)


@dataclasses.dataclass()
class ReportModifier:
    def modify(self, nb_contents: nbformat.NotebookNode):
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class ReportArtifact:
    body: bytes
    images: Mapping[str, bytes] = dataclasses.field(
        default_factory=dict, hash=False
    )


@dataclasses.dataclass()
class ReportGenerator:
    def generate(
        self, nb_contents: nbformat.NotebookNode, nb_name: Optional[str] = None
    ) -> bytes:
        raise NotImplementedError


@dataclasses.dataclass()
class ReportPublisher:
    def publish(
        self, report: Report, artifact: ReportArtifact
    ) -> Optional[str]:
        raise NotImplementedError


@dataclasses.dataclass()
class ReportRunner:
    def run(self, report: Report) -> Optional[str]:
        raise NotImplementedError


@dataclasses.dataclass()
class ReportSetRunner:
    def run(self, report_set: ReportSet):
        raise NotImplementedError
