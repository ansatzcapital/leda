"""Check PyPI package published on or after given asof datetime.

E.g.:

```bash
python ./check_pkgs.py ./packages.txt "2025-01-01"
```
"""

from __future__ import annotations

import argparse
import datetime
import functools
import logging
import pathlib
from typing import TypeVar, cast
import xml.etree.ElementTree as xml_etree  # noqa: N813

import pandas as pd
import requests

logger = logging.getLogger(__name__)

T = TypeVar("T")


def unwrap(value: T | None) -> T:
    assert value is not None
    return value


def fetch_package_rss(package_name: str) -> bytes:
    """Fetch the RSS feed for a given PyPI package."""
    url = f"https://pypi.org/rss/project/{package_name}/releases.xml"

    response = requests.get(url)
    response.raise_for_status()
    assert response.content is not None  # For typing
    return cast(bytes, response.content)


def parse_package_rss(
    rss_content: bytes, package_name: str, asof: datetime.datetime
) -> None:
    """Parse the RSS feed and extract releases asof given dt."""
    logger.debug("Checking %r", package_name)
    root = xml_etree.fromstring(rss_content)
    items = root.findall(".//item")
    for item in items:
        title = unwrap(item.find("title")).text
        pub_date = unwrap(item.find("pubDate")).text
        pub_ts = pd.to_datetime(pub_date, utc=True)  # pyright: ignore

        logger.debug("Published %s %s on %s", package_name, title, pub_ts)

        if pub_ts > asof:
            logger.info("Published %s %s on %s!", package_name, title, pub_ts)


def check_packages(
    package_constraints: list[str], asof: datetime.datetime
) -> None:
    for package_constraint in package_constraints:
        if (
            not package_constraint
            or "-e" in package_constraint
            or package_constraint.startswith("#")
        ):
            continue

        if "==" in package_constraint:
            package_name, _ = package_constraint.split("==")
        else:
            package_name = package_constraint

        package_rss_content = fetch_package_rss(package_name)
        parse_package_rss(package_rss_content, package_name, asof)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=pathlib.Path)
    parser.add_argument(
        "asof", type=functools.partial(pd.to_datetime, utc=True)
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    logger.info("Reading package file")
    package_constraints = (
        cast(pathlib.Path, args.path).read_text().splitlines()
    )
    asof = cast(pd.Timestamp, args.asof).to_pydatetime()

    logger.info("Checking packages")
    check_packages(package_constraints, asof)

    logger.info("Done")


if __name__ == "__main__":
    main()
