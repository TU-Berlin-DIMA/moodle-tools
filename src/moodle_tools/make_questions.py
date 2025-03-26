""".. include:: ../../docs/make_questions.md"""

import argparse
import contextlib
import os
import sys
from collections.abc import Iterator
from importlib.util import find_spec
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger

from moodle_tools.eval import eval_context
from moodle_tools.questions import create_question
from moodle_tools.questions.question import Question
from moodle_tools.utils import ParsingError


def load_questions(
    documents: Iterator[dict[str, Any]],
    strict_validation: bool = True,
    parse_markdown: bool = True,
    table_styling: bool = True,
) -> Iterator[Question]:
    """Load questions from a collection of dictionaries.

    Args:
        documents: Collection of dictionaries.
        strict_validation: Validate each question strictly and raise errors for questions that miss
            optional information, such as feedback (default True).
        parse_markdown: Parse question and answer text as Markdown (default True).
        table_styling: Add Bootstrap style classes to table tags (default True).

    Yields:
        Iterator[Question]: The loaded questions.

    Raises:
        ParsingError: If question type or title are not provided.
    """
    for document in documents:
        if "table_styling" not in document:
            document.update({"table_styling": table_styling})
        if "markdown" not in document:
            document.update({"markdown": parse_markdown})
        if "skip_validation" in document:
            strict_validation = not document["skip_validation"]
        if "type" in document:
            question_type = document["type"]
        else:
            raise ParsingError(f"Question type not provided: {document}")
        if "title" not in document:
            raise ParsingError(f"Question title not provided: {document}")
        # TODO: Add further validation for required fields here

        if document.get("internal_copy"):
            internal_document = document.copy()
            internal_document["title"] += " (intern \U0001f92b)"
            document.pop("internal_copy")
            yield create_question(question_type, **internal_document)

        question = create_question(question_type, **document)
        logger.debug(f"Parsed `{type(question).__name__}` question.")
        if strict_validation:
            errors = question.validate()
            if errors:
                message = (
                    "The following question did not pass strict validation and has been ignored:\n"
                    f"{yaml.safe_dump(document)}\n" + "\n- ".join(errors)
                )
                logger.error(message)
                continue
        yield question


def generate_moodle_questions(
    *,
    paths: Iterator[Path],
    skip_validation: bool = False,
    parse_markdown: bool = True,
    add_question_index: bool = False,
    question_filter: list[str] | None = None,
    table_styling: bool = True,
    allow_eval: bool = False,
) -> str:
    """Generate Moodle XML from a list of paths to YAML documents.

    Args:
        paths: Input YAML files as paths.
        skip_validation: Skip strict validation (default False).
        parse_markdown: Parse question and answer text as Markdown (default True).
        add_question_index: Extend each question title with an increasing number (default False).
        question_filter: Filter questions to export by name.
        table_styling: Add Bootstrap style classes to table tags (default True).
        allow_eval: Allows to evaluate math expressions (default False).

    Returns:
        str: Moodle XML for all questions in the YAML file.
    """
    yaml.SafeLoader.add_constructor("!eval", eval_context(allow_eval))

    questions: list[Question] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as file, contextlib.chdir(path.parent):
            for i, question in enumerate(
                load_questions(
                    yaml.safe_load_all(file),
                    strict_validation=not skip_validation,
                    parse_markdown=parse_markdown,
                    table_styling=table_styling,
                ),
                start=1,
            ):
                if add_question_index:
                    question.title = f"{question.title} ({i})"
                questions.append(question)
    logger.debug(f"Loaded {len(questions)} questions from YAML.")

    if question_filter:
        questions = [question for question in questions if question.title in question_filter]
        logger.debug(f"{len(questions)} questions remained after running filter.")

        if not questions:
            logger.warning("Filter returned 0 questions. Exiting.")
            sys.exit(1)

        if len(questions) < len(question_filter):
            logger.warning("Filter returned fewer questions than expected. Exiting.")
            sys.exit(1)

    env = Environment(
        loader=PackageLoader("moodle_tools.questions"),
        lstrip_blocks=True,
        trim_blocks=True,
        autoescape=select_autoescape(),
    )
    template = env.get_template("quiz.xml.j2")
    xml = template.render(questions=[question.to_xml(env) for question in questions])
    logger.info(f"Generated {len(questions)} Moodle XML questions.")
    return xml


def iterate_inputs(
    files: Iterator[str | os.PathLike[Any]], strict: bool = False
) -> Iterator[Path]:
    """Iterate over a collection of input files or directories.

    Args:
        files: An iterator of file paths or directory paths.
        strict: If True, raise an OSError if a path is neither a file nor a directory.
                If False, ignore such paths.

    Yields:
        Iterator[Path]: A generator that yields Path objects representing input files.
    """
    for file in files:
        path = Path(file)
        # Ignore the extension if the file is explicitly specified on the command line.
        if path.is_file():
            yield path
        elif path.is_dir():
            # TODO: Refactor this to use path.walk() once we drop Python 3.11 support
            for dirpath, _, filenames in os.walk(path):
                for filename in filenames:
                    # Only process YAML files in folders, to exclude resources, like images.
                    if filename.endswith((".yml", ".yaml")):
                        yield Path(dirpath) / filename
        elif strict:
            raise OSError(f"Not a file or folder: {file}")
        else:
            logger.debug(f"{file} is neither a file nor a folder - ignoring.")


def parse_args() -> argparse.Namespace:
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
        "-s",
        "--skip-validation",
        action="store_true",
        help="Skip strict validation (default: %(default)s)",
    )
    parser.add_argument(
        "-q",
        "--add-question-index",
        action="store_true",
        help="Extend each question title with an increasing number (default: %(default)s)",
    )
    parser.add_argument(
        "-f",
        "--filter",
        action="extend",
        nargs="+",
        type=str,
        help="Filter questions to export by name",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        type=str,
        choices=["DEBUG", "INFO", "ERROR"],
        help="Set the log level (default: %(default)s)",
    )
    parser.add_argument(
        "--allow-eval",
        action="store_true",
        help="Allows to evaluate math expressions (default: %(default)s)",
    )

    return parser.parse_args()


@logger.catch(reraise=False, onerror=lambda _: sys.exit(1))
def main() -> None:
    """Run the question generator.

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

    if find_spec("isda_streaming") is None or find_spec("duckdb") is None:
        logger.debug(
            "ISDA questions are not available. If you need them, install the `isda` extra."
        )

    try:
        inputs = iterate_inputs(args.input, not args.skip_validation)
        question_xml = generate_moodle_questions(
            paths=inputs,
            skip_validation=args.skip_validation,
            add_question_index=args.add_question_index,
            question_filter=args.filter,
            allow_eval=args.allow_eval,
        )
        print(question_xml, file=args.output)
    except ParsingError as e:
        logger.error("Parsing failed because of the following error:")
        logger.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
