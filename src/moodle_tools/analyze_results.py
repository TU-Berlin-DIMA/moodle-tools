""".. include:: ../../docs/analyze_results.md"""

import argparse
import sys

from moodle_tools.questions.base import BaseQuestionAnalysis
from moodle_tools.questions.cloze import ClozeQuestionAnalysis
from moodle_tools.questions.coderunner_sql import CoderunnerQuestionSQLAnalysis
from moodle_tools.questions.drop_down import DropDownQuestionAnalysis
from moodle_tools.questions.missing_words import MissingWordsQuestionAnalysis
from moodle_tools.questions.multiple_choice import MultipleChoiceQuestionAnalysis
from moodle_tools.questions.multiple_true_false import MultipleTrueFalseQuestionAnalysis
from moodle_tools.questions.numerical import NumericalQuestionAnalysis
from moodle_tools.questions.true_false import TrueFalseQuestionAnalysis
from moodle_tools.utils import normalize_questions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input file (default: %(default)s)",
        type=argparse.FileType("r"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: %(default)s)",
        type=argparse.FileType("w"),
        default=sys.stdout,
    )
    parser.add_argument(
        "--n",
        "--numeric",
        help="List of numeric questions",
        action="extend",
        nargs="*",
        type=NumericalQuestionAnalysis,
        default=[],
    )
    parser.add_argument(
        "--tf",
        "--true-false",
        help="List of True/False questions",
        action="extend",
        nargs="*",
        type=TrueFalseQuestionAnalysis,
        default=[],
    )
    parser.add_argument(
        "--mc",
        "--multiple-choice",
        help="List of multiple choice questions",
        action="extend",
        nargs="*",
        type=MultipleChoiceQuestionAnalysis,
        default=[],
    )
    parser.add_argument(
        "--mtf",
        "--multiple-true-false",
        help="List of multiple choice questions",
        action="extend",
        nargs="*",
        type=MultipleTrueFalseQuestionAnalysis,
        default=[],
    )
    parser.add_argument(
        "--dd",
        "--drop-down",
        help="List of drop-down questions",
        action="extend",
        nargs="*",
        type=DropDownQuestionAnalysis,
        default=[],
    )
    parser.add_argument(
        "--mw",
        "--missing-words",
        help="List of missing words questions",
        action="extend",
        nargs="*",
        type=MissingWordsQuestionAnalysis,
        default=[],
    )
    parser.add_argument(
        "--cloze",
        help="List of cloze questions",
        action="extend",
        nargs="*",
        type=ClozeQuestionAnalysis,
        default=[],
    )
    parser.add_argument(
        "--cr",
        "--coderunner",
        help="List of coderunner questions",
        action="extend",
        nargs="*",
        type=CoderunnerQuestionSQLAnalysis,
        default=[],
    )
    args = parser.parse_args()
    args.handlers = args.n + args.tf + args.mc + args.mtf + args.dd + args.cloze + args.mw
    return args


def main() -> None:
    """Entry point of the CLI Moodle Tools Analyze Questions.

    This function serves as the entry point of the script or module.
    It calls and instantiates the CLI parser.

    Returns:
        None

    Raises:
        Any exceptions raised during execution.
    """
    args = parse_args()
    # TODO: Refactor or remove
    custom_handlers: list[BaseQuestionAnalysis] = []
    normalize_questions(args.input, args.output, args.handlers + custom_handlers)


if __name__ == "__main__":
    main()
