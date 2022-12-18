import argparse
import contextlib
import difflib
import logging
import pathlib
import tempfile
from typing import Optional, Sequence

import leda

logger = logging.getLogger(__name__)

# NB: This only works in editable install
DEMO_DIR = pathlib.Path(leda.__file__) / "demos"
TEST_DIR = pathlib.Path(__file__).parent


def generate_test_report(
    nb_path: pathlib.Path,
    output_dir: pathlib.Path,
    static_interact_mode_alias: str,
    tag: Optional[str] = None,
) -> pathlib.Path:
    report = leda.FileReport(
        nb_path=nb_path,
        name=nb_path.stem,
        tag=tag,
    )

    output_dir = output_dir / report.full_name

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
    )

    publisher = leda.FileReportPublisher(output_dir=output_dir)

    runner = leda.MainReportRunner(
        modifier=modifier,
        generator=generator,
        publisher=publisher,
    )

    report_url = runner.run(report=report)
    return pathlib.Path(report_url.replace("file://", ""))


def clean_report_lines(lines: Sequence[str]) -> Sequence[str]:
    """Clean report of randomly-generated strs, e.g., tmp dir."""
    import bs4

    text = "\n".join(lines)

    soup = bs4.BeautifulSoup(text, "html.parser")

    remove_divs = []

    # Remove stderr output
    remove_divs.extend(soup.find_all("div", {"class": "output_stderr"}))

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

    return [line for line in text.splitlines() if line.strip()]


def clean_report(text: str) -> str:
    return "\n".join(clean_report_lines(text.splitlines()))


def run_tests(
    tmp_path: pathlib.Path,
    bundle_name: str,
    verbose: bool = False,
    generate_html_diffs: bool = False,
    write_refs_mode: bool = False,
):
    if generate_html_diffs and write_refs_mode:
        raise ValueError("Can't both compare and write")

    # TODO: Enable panel
    static_interact_mode_aliases = [
        alias
        for alias in leda.STATIC_INTERACT_MODE_ALIASES
        if alias != "panel"
    ]

    errors = []
    for nb_name in ["basic_demo", "matplotlib_demo", "plotly_demo"]:
        for static_interact_mode_alias in static_interact_mode_aliases:
            name_token = "-".join(
                [nb_name, static_interact_mode_alias, bundle_name]
            )
            logger.info("Running: %r", name_token)

            nb_path = DEMO_DIR / f"{nb_name}.ipynb"
            ref_result_path = TEST_DIR / f"{name_token}.html"

            test_result_path = generate_test_report(
                nb_path,
                tmp_path,
                static_interact_mode_alias=static_interact_mode_alias,
                tag=f"{static_interact_mode_alias}-{bundle_name}",
            )

            if write_refs_mode:
                logger.info("Writing to %s", ref_result_path)
                # Not necessary to clean when writing ref, but it's
                # a good way to sanity check the logic by hand
                ref_result_path.write_text(
                    clean_report(test_result_path.read_text())
                )
                logger.info("Wrote: file://%s", ref_result_path.absolute())
                continue

            ref_result_lines = clean_report_lines(
                ref_result_path.read_text().splitlines()
            )
            test_result_lines = clean_report_lines(
                test_result_path.read_text().splitlines()
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
            if context_diffs:
                logger.info("Found some diffs")
                errors.append(name_token)
                if verbose:
                    print("\n".join(context_diffs))

                if generate_html_diffs:
                    logger.info("Generating HTML diff")
                    with (
                        pathlib.Path.cwd() / f"{name_token}-diff.html"
                    ) as diff_html_path:
                        html = difflib.HtmlDiff(wrapcolumn=79).make_file(
                            ref_result_lines, test_result_lines, context=True
                        )
                        diff_html_path.write_text(html)
                        logger.info(
                            "Generated HTML diff: file://%s", diff_html_path
                        )
                        print(f"file://{diff_html_path}")

    if errors:
        raise RuntimeError(f"{len(errors)} errors")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle_name")
    parser.add_argument("--output-dir", default=None, type=pathlib.Path)
    parser.add_argument("--log-level", default=None, type=str)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--gen-html-diffs", action="store_true")
    parser.add_argument("--write-refs-mode", action="store_true")
    args = parser.parse_args()

    if args.log_level:
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        # Suppress a log message that seems to have no effect
        logging.getLogger("traitlets").setLevel(logging.ERROR)

    if args.output_dir:
        ctxt = contextlib.nullcontext(args.output_dir)
    else:
        ctxt = tempfile.TemporaryDirectory(prefix="leda_integration_test_")

    with ctxt as tmp_path:
        run_tests(
            pathlib.Path(tmp_path),
            args.bundle_name,
            verbose=args.verbose,
            generate_html_diffs=args.gen_html_diffs,
            write_refs_mode=args.write_refs_mode,
        )


if __name__ == "__main__":
    main()
