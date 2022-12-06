"""Generate static report from Jupyter notebook.

E.g.:
  python -m leda /path/to/notebook.ipynb
  python -m leda /path/to/notebook.ipynb -t $SOME_TAG -i "foo=123;bar='hi'"
"""
import argparse
import datetime
import logging
import pathlib

import leda

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
    parser.add_argument(
        "--static-interact-mode",
        default="static_ipywidgets",
        choices=["static_ipywidgets", "panel"],
        help="Set static interact mode. Choices: static_ipywidgets [default], panel",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    report = leda.FileReport(
        nb_path=args.nb_path,
        name=args.nb_path.stem,
        tag=args.tag,
        additional_inject_code=args.inject,
        cell_timeout=datetime.timedelta(seconds=args.cell_timeout),
    )
    leda.MainReportRunner.get_default_main_runner(
        report,
        args.output_dir,
        static_interact_mode_alias=args.static_interact_mode,
        kernel_name=args.kernel,
        progress=True,
    ).run(
        report=report,
    )

    logger.info("Done")


if __name__ == "__main__":
    main()
