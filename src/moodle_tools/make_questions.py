""".. include:: ../../docs/make_questions.md"""

import argparse
import sys
from io import TextIOBase
from typing import Any, Iterator

import yaml
from jinja2 import Environment, PackageLoader

from moodle_tools.questions.factory import QuestionFactory
from moodle_tools.questions.question import Question
from moodle_tools.utils import ParsingError


def load_questions(
    documents: Iterator[dict[str, Any]],
    strict_validation: bool = True,
    parse_markdown: bool = False,
    add_table_border: bool = False,
) -> Iterator[Question]:
    """Load questions from a collection of dictionaries.

    Args:
        documents: Collection of dictionaries.
        strict_validation: Validate each question strictly and raise errors for questions that miss
            optional information, such as feedback (default True).
        parse_markdown: Parse question and answer text as Markdown (default False).
        add_table_border: Put a 1 Pixel solid black border around each table cell (default False).

    Yields:
        Iterator[Question]: The loaded questions.

    Raises:
        ParsingError: If question type or title are not provided.
    """
    for document in documents:
        document.update({"table_border": add_table_border, "markdown": parse_markdown})
        if "type" in document:
            question_type = document["type"]
        else:
            raise ParsingError(f"Question type not provided: {document}")
        if "title" not in document:
            raise ParsingError(f"Question title not provided: {document}")
        # TODO: Add further validation for required fields here

        question = QuestionFactory.create_question(question_type, **document)
        if strict_validation:
            errors = question.validate()
            # TODO: Raise a ValidationError here instead of printing to stderr
            if errors:
                message = (
                    "---\nThe following question did not pass strict validation:\n"
                    + f"{yaml.safe_dump(document)}\n"
                    + "\n- ".join(errors)
                )
                print(message, file=sys.stderr)
                continue
        yield question


def generate_moodle_questions(
    file: TextIOBase,
    skip_validation: bool = False,
    parse_markdown: bool = False,
    add_question_index: bool = False,
    add_table_border: bool = False,
) -> str:
    """Generate Moodle XML from a file with a list of YAML documents.

    Args:
        file: Input YAML file.
        skip_validation: Skip strict validation (default False).
        parse_markdown: Parse question and answer text as Markdown (default False).
        add_question_index: Extend each question title with an increasing number (default False).
        add_table_border: Put a 1 Pixel solid black border around each table cell (default False).

    Returns:
        str: Moodle XML for all questions in the YAML file.
    """
    questions = list(
        load_questions(
            yaml.safe_load_all(file),
            strict_validation=not skip_validation,
            parse_markdown=parse_markdown,
            add_table_border=add_table_border,
        )
    )

    if add_question_index:
        for i, question in enumerate(questions, start=1):
            question.title = f"{question.title} ({i})"

    env = Environment(
        loader=PackageLoader("moodle_tools", "questions/templates"),
        lstrip_blocks=True,
        trim_blocks=True,
    )
    template = env.get_template("quiz.xml.j2")
    return template.render(questions=[question.to_xml(env) for question in questions])


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
        "-s", "--skip-validation", help="Skip strict validation", action="store_true"
    )
    parser.add_argument(
        "-m",
        "--parse-markdown",
        help="Parse question and answer text as Markdown",
        action="store_true",
    )
    parser.add_argument(
        "-q",
        "--add-question-index",
        help="Extend each question title with an increasing number",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--add-table-border",
        help="Put a 1 Pixel solid black border around each table cell",
        action="store_true",
    )

    return parser.parse_args()


def main() -> None:
    """Run the question generator.

    This function serves as the entry point of the CLI.

    Raises:
        SystemExit: If the program is called with invalid arguments.
    """
    args = parse_args()
    question_xml = generate_moodle_questions(
        file=args.input,
        skip_validation=args.skip_validation,
        parse_markdown=args.parse_markdown,
        add_question_index=args.add_question_index,
        add_table_border=args.add_table_border,
    )
    # TODO: Refactor this print statement
    print(question_xml, file=args.output)


if __name__ == "__main__":
    main()
