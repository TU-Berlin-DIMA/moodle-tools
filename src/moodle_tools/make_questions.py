""".. include:: ../../docs/make_questions.md"""

import argparse
import sys
from io import TextIOBase
from pathlib import Path
from typing import Any, Iterator

import yaml
from jinja2 import Environment, PackageLoader
from jsonschema import Draft202012Validator, ValidationError

from moodle_tools.questions.factory import QuestionFactory
from moodle_tools.questions.question import Question
from moodle_tools.utils import ParsingError


def load_questions(
    documents: Iterator[dict[str, Any]],
    strict_validation: bool = True,
    parse_markdown: bool = True,
    add_table_border: bool = True,
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
    schema_path = Path(__file__).parent / "questions/schemas/"
    question_schema = "question.yaml"

    report_errors = []

    for document in documents:
        if "table_border" not in document:
            document.update({"table_border": add_table_border})
        if "markdown" not in document:
            document.update({"markdown": parse_markdown})
        if "skip_validation" in document:
            strict_validation = not document["skip_validation"]
            document.update({"strict_validation": strict_validation})
        else:
            document.update({"strict_validation": strict_validation})
        if "type" in document:
            question_type = document["type"]

        # Validation of mandatory basic attributes
        with open(schema_path / question_schema, "r", encoding="utf8") as stream:
            schema_base = yaml.safe_load(stream.read())

        validator = Draft202012Validator(schema_base)

        try:
            validator.validate(document)
        except ValidationError as e:
            if "title" in document:
                current_document = (document["title"], [e.message])
            else:
                current_document = ("No Reference", [e.message])
            report_errors.append(current_document)
        else:
            # if "type" in document:
            #     question_type = document["type"]
            # else:
            #     raise ParsingError(f"Question type not provided: {document}")
            # if "title" not in document:
            #     raise ParsingError(f"Question title not provided: {document}")
            # # TODO: Add further validation for required fields here
            if "internal_copy" in document and document["internal_copy"]:
                internal_document = document.copy()
                internal_document["title"] += " (intern \U0001f92b)"
                document.pop("internal_copy")
                yield QuestionFactory.create_question(question_type, **internal_document)

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
    # Reports all errors
    if report_errors:
        raise ParsingError(report_errors)


def generate_moodle_questions(
    file: TextIOBase,
    skip_validation: bool = False,
    parse_markdown: bool = True,
    add_question_index: bool = False,
    add_table_border: bool = True,
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
        loader=PackageLoader("moodle_tools.questions"), lstrip_blocks=True, trim_blocks=True
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
        "-q",
        "--add-question-index",
        help="Extend each question title with an increasing number",
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
        add_question_index=args.add_question_index,
    )
    # TODO: Refactor this print statement
    print(question_xml, file=args.output)


if __name__ == "__main__":
    main()
