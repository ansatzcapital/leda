"""Generate static report from Jupyter notebook.

E.g.:
  python -m leda /path/to/notebook.ipynb
  python -m leda /path/to/notebook.ipynb -t $SOME_TAG -i "foo=123;bar='hi'"
"""
import argparse
import datetime
import logging
import pathlib

import leda.gen.base
import leda.gen.runners
import leda.interact.helpers

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

DEFAULT_CELL_TIMEOUT = datetime.timedelta(minutes=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "nb_path",
        type=pathlib.Path,
        help="Path to .ipynb file",
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        required=True,
        help="Path to output dir",
    )
    parser.add_argument(
        "-t",
        "--tag",
        type=str,
        default=None,
        help="Unique tag used in report publishing",
    )
    parser.add_argument(
        "-i",
        "--inject",
        type=str,
        default=None,
        help="Inject code at beginning of report; "
        "can use this to set report params",
    )
    parser.add_argument(
        "-k", "--kernel", type=str, default=None, help="Kernel name"
    )
    parser.add_argument(
        "--cell-timeout",
        type=int,
        default=DEFAULT_CELL_TIMEOUT.total_seconds(),
        help="Timeout for each cell in secs",
    )
    static_interact_mode_aliases_str = ",".join(
        leda.interact.helpers.STATIC_INTERACT_MODE_ALIASES
    )
    parser.add_argument(
        "--static-interact-mode",
        default="static_ipywidgets",
        choices=leda.interact.helpers.STATIC_INTERACT_MODE_ALIASES,
        help=f"Set static interact mode. "
        f"Choices: {static_interact_mode_aliases_str}",
    )
    parser.add_argument(
        "--template-name",
        type=str,
        choices=[None, "classic", "lab", "lab_narrow"],
        help="nbconvert template name",
    )
    parser.add_argument(
        "--theme",
        type=str,
        choices=[None, "light", "dark"],
        help="nbconvert template theme",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Suppress a log message that seems to have no effect
    logging.getLogger("traitlets").setLevel(logging.ERROR)

    report = leda.gen.base.FileReport(
        nb_path=args.nb_path,
        name=args.nb_path.stem,
        tag=args.tag,
        additional_inject_code=args.inject,
        cell_timeout=datetime.timedelta(seconds=args.cell_timeout),
    )
    runner = leda.gen.runners.MainReportRunner.get_default_runner(
        report,
        args.output_dir,
        static_interact_mode_alias=args.static_interact_mode,
        kernel_name=args.kernel,
        progress=True,
        template_name=args.template_name,
        theme=args.theme,
    )
    runner.run(report=report)

    logger.info("Done")


if __name__ == "__main__":
    main()
