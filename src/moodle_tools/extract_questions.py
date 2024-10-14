""".. include:: ../../docs/extract_questions.md"""

import argparse
import sys
from pathlib import Path
from typing import Iterator

from loguru import logger

from moodle_tools.utils import iterate_inputs


def extract_yaml_questions(paths: Iterator[Path]) -> str:
    """Generate Moodle-Tools YAML from a Moodle-XML file.

    Args:
        path: Input XML file as path.

    Returns:
        str: Moodle-Tools YAML for all questions in the XML file.
    """
    for path in paths:
        print(path)
    return "TODO: Implement function"


def parse_args() -> argparse.Namespace:
    # pylint: disable=duplicate-code
    """Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        action="extend",
        nargs="+",
        type=str,
        required=True,
        help="Input files or folder",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=sys.stdout,
        type=argparse.FileType("w", encoding="utf-8"),
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str,
        choices=["DEBUG", "INFO", "ERROR"],
        help="Set the log level (default: %(default)s)",
    )

    return parser.parse_args()


@logger.catch(reraise=False, onerror=lambda _: sys.exit(1))
def main() -> None:
    # pylint: disable=duplicate-code
    """Run the question extraction.

    This function serves as the entry point of the CLI.

    Raises:
        SystemExit: If the program is called with invalid arguments.
    """
    args = parse_args()
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | <level>{message}</level>",
        level=args.log_level,
        filter=lambda record: record["level"].no < 40,  # Don't log errors twice
    )
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | <level>{message}</level>",
        level="ERROR",
    )
    inputs = iterate_inputs(args.input, "XML")
    moodle_tools_yaml = extract_yaml_questions(inputs)
    print(moodle_tools_yaml, file=args.output)


if __name__ == "__main__":
    main()
