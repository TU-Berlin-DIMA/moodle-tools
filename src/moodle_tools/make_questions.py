""".. include:: ../../docs/make_questions.md"""

import argparse
import sys

import moodle_tools.questions
from moodle_tools.utils import generate_moodle_questions


def parse_args() -> argparse.Namespace:
    """CLI Parser.

    This function serves as the entry point from the CLI. It contains
    the main flow of the program. It parses command-line
    arguments, call functions according to the subcommand,
    which is linked to a specific Question Type.

    Returns:
        argparse.Namespace

    Raises:
        Any exceptions raised during execution.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input file (default: %(default)s)",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: %(default)s)",
        type=argparse.FileType("w", encoding="utf-8"),
        default=sys.stdout,
    )
    parser.add_argument(
        "-t",
        "--title",
        help="Default question title (default: %(default)s)",
        type=str,
        default="Knowledge question",
    )
    parser.add_argument("-l", "--lenient", help="Skip strict validation.", action="store_true")
    parser.add_argument(
        "-m",
        "--markdown",
        help="Specify question and answer text in Markdown.",
        action="store_true",
    )
    parser.add_argument(
        "--table-border",
        help="Put a 1 Pixel solid black border around each table cell",
        action="store_true",
    )
    parser.add_argument(
        "--add-question-index",
        help="Extend each question title with an increasing number.",
        action="store_true",
    )
    parser.set_defaults(func=generate_moodle_questions)

    return parser.parse_args()


def main() -> None:
    """Entry point of the CLI Moodle Tools Generate Questions.

    This function serves as the entry point of the script or module.
    It calls and instantiates the CLI parser.

    Returns:
        None

    Raises:
        Any exceptions raised during execution.
    """
    args = parse_args()
    args.func(**vars(args))


if __name__ == "__main__":
    main()
