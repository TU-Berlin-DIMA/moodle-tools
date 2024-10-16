""".. include:: ../../docs/extract_questions.md"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator

from loguru import logger

from moodle_tools.questions import Question, QuestionFactory
from moodle_tools.utils import iterate_inputs


def load_moodle_xml(path: Path) -> Iterator[Question]:
    with open(path) as file:
        document = ET.parse(file)
        quiz = document.getroot()

    # Only one category allowed
    category = ""
    for element in quiz.findall("question"):
        question_props = dict()
        if element.attrib.get("type") == "category":
            category = element.find("category").find("text").text
        else:
            question_props.update({"category": category})
            question_props.update({"type": element.attrib.get("type")})
            question_props.update({"title": element.find("name").find("text").text})
            question_props.update({"question": element.find("questiontext").find("text").text})
            question_props.update(
                {"general_feedback": element.find("generalfeedback").find("text").text}
            )
            question_props.update({"markdown": False})
            question_props.update({"table_styling": False})
            question = QuestionFactory.create_question(
                question_props.get("type"), **question_props
            )
            yield question


def extract_yaml_questions(paths: Iterator[Path]) -> str:
    """Generate Moodle-Tools YAML from a Moodle-XML file.

    Args:
        path: Input XML file as path.

    Returns:
        str: Moodle-Tools YAML for all questions in the XML file.
    """
    questions: list[Question] = []
    for path in paths:
        for question in load_moodle_xml(path):
            questions.append(question)
            print(question.title)

    logger.info(f"Loaded {len(questions)} questions from YAML.")
    return "yaml"


def parse_args() -> argparse.Namespace:
    # pylint: disable=duplicate-code
    # TODO: refactor to comply with pylint and mypy.
    # Marked as duplicated with make_question:parse_args, main
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
