"""Run integration tests in either check or write mode.

See also `noxfile.py` integration test sessions.

E.g.:
```bash
# Check against reference output
python ./leda/tests/integration/run_test.py bundle0 --write --log INFO

# Write new references
python ./leda/tests/integration/run_test.py bundle4 --write --log INFO
```
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import difflib
import logging
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import ContextManager, Sequence

import nbconvert
import packaging.version

import leda

logger = logging.getLogger(__name__)

# NB: This only works in editable install
DEMO_DIR = pathlib.Path(leda.__file__).parent / "demos"
REF_DIR = pathlib.Path(__file__).parent / "refs"


def check_env(bundle_name: str) -> None:
    logger.info("Checking env against %r", bundle_name)
    req_text = (
        pathlib.Path(leda.__file__).parent.parent
        / f"requirements-{bundle_name}.txt"
    ).read_text()
    req_lines = req_text.splitlines()

    req_python_version = req_lines[0].split("python")[1].strip()
    installed_python_version = ".".join(
        map(str, [sys.version_info.major, sys.version_info.minor])
    )
    assert req_python_version == installed_python_version, (
        f"Python version mismatch: "
        f"{req_python_version} != {installed_python_version}"
    )

    installed_pkgs = {}
    pip_freeze_lines = (
        subprocess.check_output(["uv", "pip", "freeze"]).decode().splitlines()
    )
    for pip_freeze_line in pip_freeze_lines:
        # Skip editable and wheel installs
        if pip_freeze_line.startswith("-e") or "@" in pip_freeze_line:
            continue

        pkg_name, pkg_version = map(str.strip, pip_freeze_line.split("=="))
        installed_pkgs[pkg_name] = pkg_version

    for req_line in req_lines:
        req_line = req_line.split("#")[0].strip()
        if not req_line:
            continue

        req_name, req_version = map(str.strip, req_line.split("=="))

        installed_version = None
        for req_name_alias in [
            req_name,
            req_name.lower(),
            req_name.replace("-", "_"),
            req_name.replace("_", "-"),
        ]:
            try:
                installed_version = installed_pkgs[req_name_alias]
            except KeyError:
                pass
            else:
                break
        assert installed_version, f"Failed to find: {req_name!r}"

        logger.debug("Checking %r", req_name)
        assert installed_version == req_version, (
            f"Package version mismatch: {req_name!r}, "
            f"{installed_version} != {req_version}"
        )


def generate_test_report(
    nb_path: pathlib.Path,
    output_dir: pathlib.Path,
    static_interact_mode_alias: str,
    tag: str | None = None,
    template_name: str | None = None,
    theme: str | None = None,
) -> pathlib.Path:
    report = leda.FileReport(
        nb_path=nb_path,
        name=nb_path.stem,
        tag=tag,
        # Expanded cell timeout for slower CI workers
        cell_timeout=datetime.timedelta(minutes=5),
    )

    output_dir = output_dir / report.full_name

    modifier: leda.ReportModifier
    if static_interact_mode_alias == "static_ipywidgets":
        # Set to use inline images
        modifier = leda.StaticIpywidgetsReportModifier(local_dir_path=None)
    elif static_interact_mode_alias == "panel":
        modifier = leda.StaticPanelReportModifier()
    else:
        raise ValueError(
            f"Unknown static interact mode: {static_interact_mode_alias!r}"
        )

    generator = leda.MainStaticReportGenerator(
        cell_timeout=report.cell_timeout,
        progress=False,
        template_name=template_name,
        theme=theme,
    )

    publisher = leda.FileReportPublisher(output_dir=output_dir)

    runner = leda.MainReportRunner(
        modifier=modifier,
        generator=generator,
        publisher=publisher,
    )

    report_url = runner.run(report=report)
    assert report_url is not None
    return pathlib.Path(report_url.replace("file://", ""))


def clean_report_lines(lines: Sequence[str]) -> Sequence[str]:  # noqa: C901
    """Clean report of randomly-generated strs, e.g., tmp dir."""
    # Importing locally because this is only needed for testing
    import bs4

    text = "\n".join(lines)

    soup = bs4.BeautifulSoup(text, "html.parser")

    remove_divs: list[bs4.Tag] = []

    # Remove stderr output in 'classic' template
    remove_divs.extend(soup.find_all("div", {"class": "output_stderr"}))

    # Remove stderr output in 'lab'-based templates
    remove_divs.extend(
        soup.find_all(
            "div", {"data-mime-type": "application/vnd.jupyter.stderr"}
        )
    )

    # Remove Jupyter widget state
    remove_divs.extend(
        soup.find_all(
            "script", {"type": "application/vnd.jupyter.widget-state+json"}
        )
    )

    # Extract and dispose of them in soup
    for div in remove_divs:
        div.extract()

    text = str(soup)

    # Fix plotly ids, which are new at every report gen
    plotly_divs = soup.find_all("div", attrs={"plotly_id": True})
    if plotly_divs:
        plotly_ids = [
            plotly_div.attrs["plotly_id"] for plotly_div in plotly_divs
        ]

        # Replace random ids with deterministic ones (the order of the
        # figures should be the same each time)
        for idx, plotly_id in enumerate(plotly_ids):
            text = text.replace(plotly_id, f"plotly_fig{idx}")

    # Fx random cell ids (first appeared in py3.12 bundle 4)
    cell_divs = soup.find_all("div", attrs={"class": "cell"}) + soup.find_all(
        "div", attrs={"class": "jp-Cell"}
    )
    if cell_divs:
        cell_ids = [
            cell_div.attrs["id"].split("=")[1]
            for cell_div in cell_divs
            if "id" in cell_div.attrs
            and cell_div.attrs["id"].startswith("cell-id=")
        ]

        # Replace random ids with deterministic ones (the order of the
        # figures should be the same each time)
        for idx, cell_id in enumerate(cell_ids):
            text = text.replace(cell_id, str(idx))

    # Second pass
    remove_divs_second_pass = []

    soup = bs4.BeautifulSoup(text, "html.parser")

    # Remove seemingly random number of empty output divs, after first pass
    # cleaning (first appeared in py3.12 bundle 4)
    output_divs = soup.find_all("div", {"class": "jp-OutputArea-child"})
    for output_div in output_divs:
        if (
            len(output_div.attrs["class"]) == 1
            and len(list(output_div.children)) == 3
            and not output_div.text.strip()
            and str(list(output_div.children)[1])
            == '<div class="jp-OutputPrompt jp-OutputArea-prompt"></div>'
        ):
            remove_divs_second_pass.append(output_div)

    # Remove seemingly random number of empty prompt divs, after first pass
    # cleaning (first appeared in py3.12 bundle 4)
    prompt_divs = soup.find_all("div", {"class": "output_area"})
    for prompt_div in prompt_divs:
        if (
            len(prompt_div.attrs["class"]) == 1
            and len(list(prompt_div.children)) == 3
            and not prompt_div.text.strip()
            and str(list(prompt_div.children)[1])
            == '<div class="prompt"></div>'
        ):
            remove_divs_second_pass.append(prompt_div)

    # Extract and dispose of them in soup
    for div in remove_divs_second_pass:
        div.extract()

    text = str(soup)

    # Return stripped lines
    return [line for line in text.splitlines() if line.strip()]


def clean_report(text: str) -> str:
    return "\n".join(clean_report_lines(text.splitlines()))


def _handle_diffs(
    output_dir: pathlib.Path,
    tag: str,
    ref_result_lines: Sequence[str],
    test_result_lines: Sequence[str],
    context_diffs: Sequence[str],
    errors: list[str],
    generate_html_diffs: bool = False,
    verbose: bool = False,
) -> None:
    if not context_diffs:
        logger.info("Found no diffs")
        return

    logger.error(
        "❌ Found some diffs. Use --gen-html-diffs to "
        "generate an HTML report of these diffs."
    )
    errors.append(tag)
    if verbose:
        print("\n".join(context_diffs))

    if generate_html_diffs:
        logger.info("Generating HTML diff")
        html = difflib.HtmlDiff(wrapcolumn=79).make_file(
            ref_result_lines,
            test_result_lines,
            context=True,
            numlines=10,
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        diff_html_path = output_dir / f"{tag}-diff.html"
        diff_html_path.write_text(html, encoding="utf-8")

        logger.info(
            "Generated HTML diff: file://%s",
            diff_html_path,
        )
        print(f"file://{diff_html_path}")


def _run_test(
    output_dir: pathlib.Path,
    bundle_name: str,
    errors: list[str],
    nb_name: str,
    static_interact_mode_alias: str,
    template_name: str | None = None,
    theme: str | None = None,
    generate_html_diffs: bool = False,
    write_refs_mode: bool = False,
    verbose: bool = False,
) -> None:
    tag_parts = [nb_name, static_interact_mode_alias, bundle_name]
    if template_name or theme:
        tag_parts.extend(map(str, [template_name, theme]))
    tag = "-".join(tag_parts)
    logger.info("Running: %r", tag)

    nb_path = DEMO_DIR / f"{nb_name}.ipynb"

    test_result_path = generate_test_report(
        nb_path,
        output_dir,
        static_interact_mode_alias=static_interact_mode_alias,
        tag=tag,
        template_name=template_name,
        theme=theme,
    )

    possible_ref_result_filenames = [
        f"{tag}-{sys.platform}.html",
        f"{tag}.html",
    ]

    if write_refs_mode:
        write_ref_result_path = REF_DIR / possible_ref_result_filenames[-1]

        logger.info("Writing to %s", write_ref_result_path)
        # We don't clean the ref reports so that we get more natural-looking
        # code for the demo page
        write_ref_result_path.write_text(
            test_result_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        logger.info("Wrote: file://%s", write_ref_result_path.absolute())
        return

    ref_result_path = None
    for ref_result_filename in possible_ref_result_filenames:
        if (REF_DIR / ref_result_filename).exists():
            ref_result_path = REF_DIR / ref_result_filename
            break
    assert ref_result_path is not None

    ref_result_lines = clean_report_lines(
        ref_result_path.read_text(encoding="utf-8").splitlines()
    )
    test_result_lines = clean_report_lines(
        test_result_path.read_text(encoding="utf-8").splitlines()
    )

    logger.info(
        "Comparing %s vs. %s",
        ref_result_path.absolute(),
        test_result_path.absolute(),
    )
    context_diffs = list(
        difflib.context_diff(
            ref_result_lines,
            test_result_lines,
            fromfile=str(ref_result_path),
            tofile=str(test_result_path),
        )
    )
    _handle_diffs(
        output_dir=test_result_path.parent,
        tag=tag,
        ref_result_lines=ref_result_lines,
        test_result_lines=test_result_lines,
        context_diffs=context_diffs,
        errors=errors,
        generate_html_diffs=generate_html_diffs,
        verbose=verbose,
    )


def run_tests(
    output_dir: pathlib.Path,
    bundle_name: str,
    verbose: bool = False,
    generate_html_diffs: bool = False,
    write_refs_mode: bool = False,
) -> None:
    if generate_html_diffs and write_refs_mode:
        raise ValueError("Can't both compare and write")

    nb_names = ["basic_demo", "matplotlib_demo", "plotly_demo"]
    # TODO: Enable panel
    static_interact_mode_aliases = [
        alias
        for alias in leda.STATIC_INTERACT_MODE_ALIASES
        if alias != "panel"
    ]
    template_options: list[tuple[str | None, str | None]]
    if packaging.version.parse(nbconvert.__version__).major < 6:
        template_options = [(None, None)]
    else:
        template_options = [
            ("classic", "light"),
            ("lab", "light"),
            ("lab_narrow", "dark"),
        ]

    errors: list[str] = []
    for nb_name in nb_names:
        for static_interact_mode_alias in static_interact_mode_aliases:
            for template_name, theme in template_options:
                _run_test(
                    output_dir=output_dir,
                    bundle_name=bundle_name,
                    errors=errors,
                    nb_name=nb_name,
                    static_interact_mode_alias=static_interact_mode_alias,
                    template_name=template_name,
                    theme=theme,
                    generate_html_diffs=generate_html_diffs,
                    write_refs_mode=write_refs_mode,
                    verbose=verbose,
                )

    if errors:
        logger.info(
            "❌ Finished with %s errors:\n%s", len(errors), "\n".join(errors)
        )
        raise RuntimeError(f"{len(errors)} errors")
    else:
        logger.info("✅ Finished with no errors")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_name")
    parser.add_argument("--output-dir", default=None, type=pathlib.Path)
    parser.add_argument("--log-level", default=None, type=str)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--gen-html-diffs", action="store_true")
    parser.add_argument("--write-refs-mode", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    args = parser.parse_args()

    if args.log_level:
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        # Suppress a log message that seems to have no effect
        logging.getLogger("traitlets").setLevel(logging.ERROR)

    output_dir: str | pathlib.Path
    ctxt: ContextManager[str | pathlib.Path]
    if args.output_dir:
        if args.cleanup:
            raise ValueError("Can only clean up tmp dirs")

        output_dir = args.output_dir.expanduser()
        ctxt = contextlib.nullcontext(output_dir)
    elif os.environ.get("LEDA_TEST_OUTPUT_DIR", None):
        if args.cleanup:
            raise ValueError("Can only clean up tmp dirs")

        output_dir = os.path.expanduser(os.environ["LEDA_TEST_OUTPUT_DIR"])
        ctxt = contextlib.nullcontext(output_dir)
    elif args.cleanup:
        ctxt = tempfile.TemporaryDirectory(prefix="leda_integration_test_")
    else:
        ctxt = contextlib.nullcontext(
            tempfile.mkdtemp(prefix="leda_integration_test_")
        )

    check_env(args.bundle_name)

    with ctxt as output_dir:
        logger.info("Using output dir: %s", output_dir)
        run_tests(
            pathlib.Path(output_dir),
            args.bundle_name,
            verbose=args.verbose,
            generate_html_diffs=args.gen_html_diffs,
            write_refs_mode=args.write_refs_mode,
        )


if __name__ == "__main__":
    main()
