""".. include:: ../../docs/extract_questions.md"""

import argparse
import sys
import xml.etree.ElementTree as ET
from base64 import b64decode
from pathlib import Path
from typing import Any, Iterator

import yaml
from loguru import logger
from moodle_tools.questions import QuestionFactory
from moodle_tools.utils import iterate_inputs


def load_moodle_xml(in_path: Path, out_path: Path | None) -> Iterator[dict[str, str | Any | None]]:
    with open(in_path) as file:
        document = ET.parse(file)
        quiz = document.getroot()

    # TODO: Define more than one category use case and implement logic
    category = ""
    for element in quiz.findall("question"):
        question_props = {}
        if element.attrib.get("type") == "category":
            category = element.find("category").find("text").text
        else:
            question_props.update({"category": category})
            question_type = element.attrib.get("type")
            question_props.update({"type": question_type})
            question = QuestionFactory.props_from_xml(question_type, element, **question_props)

            if out_path:
                for name, file in question.get("files", {}).items():
                    if file["is_used"]:
                        match file["encoding"]:
                            case "base64":
                                filename = out_path.parent / name
                                if filename.exists():
                                    filename = filename.with_suffix(filename.suffix + "." + question["title"])
                                    logger.warning(f"File {filename} already exists, saving as {filename.name} .")
                                with filename.open("wb") as f:
                                    f.write(b64decode(file["content"]))
            else:
                logger.warning("No output path provided, additional files will not be saved.")

            yield question


def extract_yaml_questions(in_paths: Iterator[Path], out_path: Path | None) -> str:
    """Generate Moodle-Tools YAML from a Moodle-XML file.

    Args:
        path: Input XML file as path.

    Returns:
        str: Moodle-Tools YAML for all questions in the XML file.
    """
    questions: list[dict[str, str | Any | None]] = []
    for in_path in in_paths:
        for question in load_moodle_xml(in_path, out_path):
            questions.append(question)
            logger.debug(f"Question {question} loaded.")

    logger.info(f"Loaded {len(questions)} questions from YAML.")

    questions_yaml = yaml.safe_dump_all(questions, width=1000)

    return questions_yaml


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
    output_dir = None if args.output.name == "<stdout>" else Path(args.output.name) if Path(args.output.name).parent.is_dir() else Path(args.output.name).parent
    moodle_tools_yaml = extract_yaml_questions(inputs, output_dir)
    print(moodle_tools_yaml, file=args.output)


if __name__ == "__main__":
    main()
