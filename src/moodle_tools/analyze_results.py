""".. include:: ../../docs/analyze_results.md"""

import argparse
import csv
import sys
from collections.abc import Sequence
from io import TextIOWrapper
from statistics import median, stdev
from typing import Literal

from loguru import logger

from moodle_tools.questions import (
    ClozeQuestionAnalysis,
    DropDownQuestionAnalysis,
    MissingWordsQuestionAnalysis,
    MultipleChoiceQuestionAnalysis,
    MultipleTrueFalseQuestionAnalysis,
    NumericalQuestionAnalysis,
    QuestionAnalysis,
    TrueFalseQuestionAnalysis,
)

__all__ = ["analyze_questions"]

TRANSLATIONS = {
    "question": {"de": "Frage", "en": "Question"},
    "response": {"de": "Antwort", "en": "Response"},
    "right_answer": {"de": "Richtige Antwort", "en": "Right answer"},
}


def detect_language(headers: Sequence[str] | None) -> Literal["en", "de"]:
    """Detect the language of the responses export by checking its headers.

    Args:
        headers: Headers of a CSV file.

    Returns:
        Literal["en", "de"]: The detected language.
    """
    if headers is None:
        logger.error("The input file does not contain any headers.")
        sys.exit(1)
    if "Nachname" in headers and "Vorname" in headers:
        return "de"
    if "Last name" in headers and "First name" in headers:
        return "en"

    logger.error(f"The input file language could not be detected via the CSV headers: {headers}")
    sys.exit(1)


def analyze_questions(
    infile: TextIOWrapper, outfile: TextIOWrapper, handlers: list[QuestionAnalysis]
) -> None:
    csv_reader = csv.DictReader(infile, delimiter=",", quotechar='"')
    lang = detect_language(csv_reader.fieldnames)

    # Process responses from input CSV file
    for row in csv_reader:
        for handler in handlers:
            question_id = handler.question_id
            try:
                handler.process_response(
                    row[f"{TRANSLATIONS['question'][lang]} {question_id}"],
                    row[f"{TRANSLATIONS['response'][lang]} {question_id}"],
                    row[f"{TRANSLATIONS['right_answer'][lang]} {question_id}"],
                )
            except KeyError as e:
                logger.error(
                    f"Could not find question with key {e} in CSV headers: {list(row.keys())}"
                )
                sys.exit(1)

    # Sort and flatten normalized questions and determine grades
    # TODO: Grade calculation is wrong for numerical and cloze questions
    questions = [
        (question, handler.grade(responses, question.correct_answer))
        for handler in sorted(handlers, key=lambda x: x.question_id)
        for question, responses in handler.questions.items()
    ]

    # Compute grade distribution statistics
    grades = [grade["grade"] for _, grade in questions]
    m = median(grades)
    stats = {
        "mean": sum(grades) / len(grades),
        "median": m,
        "mode": max(set(grades), key=grades.count),
        "stdev": stdev(grades),
        "mad": median([abs(grade - m) for grade in grades]),  # Median absolute deviation
    }
    logger.info(
        f"Grade stats (%): {{{', '.join(f'{key}: {value:1.2f}' for key, value in stats.items())}}}"
    )

    # Write normalized results as CSV file
    fieldnames = [
        "question_id",
        "variant_number",
        "question",
        "subquestion",
        "correct_answer",
        "grade",
        "outlier",
        "occurrence",
        "responses",
    ]
    writer = csv.DictWriter(outfile, fieldnames, dialect=csv.excel_tab)
    writer.writeheader()
    for question, grade in questions:
        row = question._asdict()
        grade["outlier"] = (
            not stats["median"] - 2 * stats["mad"]
            <= grade["grade"]
            <= stats["median"] + 2 * stats["mad"]
        )
        row.update(grade)
        writer.writerow(row)
    logger.debug(f"Wrote analysis report to {outfile.name}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input file (default: stdin)",
        type=argparse.FileType("r", encoding="utf-8-sig"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path, formatted as Excel-generated TAB-delimited file (default: stdout)",
        type=argparse.FileType("w", encoding="utf-8"),
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

    for handler in args.handlers:
        if isinstance(handler, ClozeQuestionAnalysis | NumericalQuestionAnalysis):
            logger.warning(
                "Grade calculation and outlier detection for numerical and cloze questions is "
                "bugged. You should not rely on it."
            )
            break

    # TODO: Refactor or remove
    custom_handlers: list[QuestionAnalysis] = []
    analyze_questions(args.input, args.output, args.handlers + custom_handlers)


if __name__ == "__main__":
    main()
