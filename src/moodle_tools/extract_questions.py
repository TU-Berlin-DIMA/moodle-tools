""".. include:: ../../docs/extract_questions.md"""

import argparse
import sys
import xml.etree.ElementTree as ET
from base64 import b64decode
from pathlib import Path
from typing import Any, Iterator

import pathvalidate
import yaml
from loguru import logger

from moodle_tools.questions import QuestionFactory
from moodle_tools.utils import iterate_inputs

ITEM_ORDER = {
    "type": 0,
    "category": 1,
    "title": 2,
    "question": 3,
    "answers": 20,
}


def load_moodle_xml(in_path: Path) -> Iterator[dict[str, str | Any | None]]:
    with open(in_path, encoding="utf-8") as file:
        document = ET.parse(file)
        quiz = document.getroot()

    # TODO: Define more than one category use case and implement logic
    category = ""
    for element in quiz.findall("question"):
        question_props = {}
        if element.attrib.get("type") == "category":
            category = (
                element.find("category").find("text").text.replace("//", "AND_OR")
            )  # fix for slashes in category names
        else:
            question_props.update({"category": category})
            question_type = element.attrib.get("type")
            question_props.update({"type": question_type})
            question = QuestionFactory.props_from_xml(question_type, element, **question_props)

            yield dict(sorted(question.items(), key=lambda item: ITEM_ORDER.get(item[0], 10)))


def extract_yaml_questions(in_paths: Iterator[Path], out_dir: Path | None) -> dict[str, str]:
    """Generate Moodle-Tools YAML from a Moodle-XML file.

    Args:
        path: Input XML file as path.

    Returns:
        str: Moodle-Tools YAML for all questions in the XML file.
    """
    questions: list[dict[str, str | Any | None]] = []
    for in_path in in_paths:
        for question in load_moodle_xml(in_path):
            questions.append(question)
            logger.debug(f"Question {question} loaded.")

    logger.info(f"Loaded {len(questions)} questions from YAML.")

    category_parts = [
        list(r) for r in zip(*[q["category"].split("/") for q in questions], strict=True)
    ]
    category_diff = [len(set(parts)) != 1 for parts in category_parts]

    min_category_diff = min(p for p in [i * int(c) for i, c in enumerate(category_diff)] if p > 0)

    grouped_questions: dict[str, list] = {}
    for question in questions:
        category = pathvalidate.sanitize_filename(
            "/".join(question["category"].split("/")[min_category_diff:]), platform="universal"
        )
        if category not in grouped_questions:
            grouped_questions[category] = []
        grouped_questions[category].append(question)

        if out_dir:
            for name, file in question.get("files", {}).items():
                if file["is_used"]:
                    match file["encoding"]:
                        case "base64":
                            img_dir = out_dir / category
                            img_dir.mkdir(parents=True, exist_ok=True)
                            filename = img_dir / name

                            content = b64decode(file["content"])

                            if filename.exists() and filename.read_bytes() != content:
                                filename = filename.with_suffix(
                                    filename.suffix + "." + question["title"]
                                )
                                logger.warning(
                                    f"File {filename} already exists, saving as {filename.name} ."
                                )
                            with filename.open("wb") as f:
                                f.write(content)
        else:
            logger.warning("No output path provided, additional files will not be saved.")

        del question["files"]

    class IndentDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False) -> None:
            super().increase_indent(flow, False)

    def str_presenter(dumper, data) -> Any:
        if len(data.splitlines()) > 1:  # check for multiline string
            data = "\n".join([line.rstrip() for line in data.strip().splitlines()])
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)  # to use with safe_dum
    IndentDumper.add_representer(str, str_presenter)

    questions_yaml_grouped = {
        k: yaml.dump_all(q, width=200, sort_keys=False, allow_unicode=True, Dumper=IndentDumper)
        for k, q in grouped_questions.items()
    }

    return questions_yaml_grouped


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

    output_dir = (
        None
        if args.output.name == "<stdout>"
        else (
            Path(args.output.name)
            if Path(args.output.name).is_dir()
            else Path(args.output.name).parent
        )
    )
    moodle_tools_yaml_grouped = extract_yaml_questions(inputs, output_dir)

    for category, moodle_tools_yaml in moodle_tools_yaml_grouped.items():
        if output_dir:
            output_path = output_dir / category / f"questions_{category}.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)
        print(
            moodle_tools_yaml,
            file=output_path.open("w") if output_dir else args.output,
        )


if __name__ == "__main__":
    main()
