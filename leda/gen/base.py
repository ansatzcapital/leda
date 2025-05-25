from __future__ import annotations

import abc
import dataclasses
import datetime
import functools
import logging
import pathlib
from typing import IO, Any, Mapping
import uuid

import nbformat
from typing_extensions import override

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclasses.dataclass(frozen=True)
class Report:
    name: str

    html_title: str | None = None
    tag: str | None = None

    params: Mapping[str, Any] | None = None
    additional_inject_code: str | None = None

    cell_timeout: datetime.timedelta | None = None

    @functools.cached_property
    def full_name(self) -> str:
        if self.tag:
            parts = [self.name, self.tag]
        else:
            parts = [self.name]

        parts.append(datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
        parts.append(str(uuid.uuid4())[-8:])

        return "-".join(parts)

    @property
    def handle(self) -> str | IO:
        raise NotImplementedError

    @functools.cached_property
    def inject_code(self) -> str | None:
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
    @override
    def handle(self) -> str | IO:
        logger.info("Reading %s", self.nb_path)
        return str(self.nb_path.expanduser())


@dataclasses.dataclass(frozen=True)
class ReportSet:
    reports: list[Report] = dataclasses.field(hash=False)


@dataclasses.dataclass()
class ReportModifier:
    def modify(self, nb_contents: nbformat.NotebookNode) -> None:
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class ReportArtifact:
    body: bytes
    images: Mapping[str, bytes] = dataclasses.field(
        default_factory=dict, hash=False
    )


@dataclasses.dataclass()
class ReportGenerator:
    @abc.abstractmethod
    def generate(
        self, nb_contents: nbformat.NotebookNode, html_title: str | None = None
    ) -> bytes: ...


@dataclasses.dataclass()
class ReportPublisher:
    @abc.abstractmethod
    def publish(
        self, report: Report, artifact: ReportArtifact
    ) -> str | None: ...


@dataclasses.dataclass()
class ReportRunner:
    @abc.abstractmethod
    def run(self, report: Report) -> str | None: ...


@dataclasses.dataclass()
class ReportSetRunner:
    @abc.abstractmethod
    def run(self, report_set: ReportSet) -> None: ...
