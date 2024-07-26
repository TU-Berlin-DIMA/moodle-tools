""".. include:: ../../docs/analyze_results.md"""

import argparse
import csv
import sys
from io import TextIOBase
from statistics import median

from loguru import logger

from moodle_tools.questions.cloze import ClozeQuestionAnalysis
from moodle_tools.questions.coderunner import CoderunnerQuestionAnalysis
from moodle_tools.questions.drop_down import DropDownQuestionAnalysis
from moodle_tools.questions.missing_words import MissingWordsQuestionAnalysis
from moodle_tools.questions.multiple_choice import MultipleChoiceQuestionAnalysis
from moodle_tools.questions.multiple_true_false import MultipleTrueFalseQuestionAnalysis
from moodle_tools.questions.numerical import NumericalQuestionAnalysis
from moodle_tools.questions.question import QuestionAnalysis
from moodle_tools.questions.true_false import TrueFalseQuestionAnalysis

__all__ = ["analyze_questions"]


def analyze_questions(
    infile: TextIOBase, outfile: TextIOBase, handlers: list[QuestionAnalysis]
) -> None:
    # Process responses from input CSV file
    for row in csv.DictReader(infile, delimiter=",", quotechar='"'):
        for handler in handlers:
            question_num = handler.question_number
            handler.process_response(
                row[f"Question {question_num}"],
                row[f"Response {question_num}"],
                row[f"Right answer {question_num}"],
            )
    # Sort and flatten normalized questions and determine grades
    questions = [
        (question, handler.grade(responses, question.correct_response))
        for handler in sorted(handlers, key=lambda x: int(x.question_number))
        for question, responses in handler.questions.items()
    ]
    # Determine median grade and MAD
    grades = [grade["grade"] for _, grade in questions]
    median_grade = median(grades)
    mad = median([abs(grade - median_grade) for grade in grades])
    logger.info(f"Median grade: {median_grade:1.1f}, MAD: {mad:1.1f}")
    # Write normalized results as CSV file
    fieldnames = [
        "question_number",
        "variant_number",
        "question",
        "subquestion",
        "correct_response",
        "grade",
        "outlier",
        "occurrence",
        "responses",
    ]
    writer = csv.DictWriter(outfile, fieldnames, dialect=csv.excel_tab)
    writer.writeheader()
    for question, grade in questions:
        row = question._asdict()
        grade["outlier"] = not median_grade - 2 * mad <= grade["grade"] <= median_grade + 2 * mad
        row.update(grade)
        writer.writerow(row)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
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
        type=CoderunnerQuestionAnalysis,
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
    logger.remove()
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | <level>{message}</level>")

    # TODO: Refactor or remove
    custom_handlers: list[QuestionAnalysis] = []
    analyze_questions(args.input, args.output, args.handlers + custom_handlers)


if __name__ == "__main__":
    main()
