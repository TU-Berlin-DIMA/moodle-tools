import sys
import textwrap

import yaml

from moodle_tools.questions.factory import QuestionFactory


def load_questions(question_factory, strict_validation, yaml_files, **flags):
    """Iterate over the YAML files and generate a question for each YAML document.

    If `strict_validation` is set, filter those questions that contain missing optional
    information (e.g., feedback).
    """
    bullet = "\n- "

    question_type = None

    for properties in yaml_files:
        # TODO: List all the potential flags for preprocessing text or make a better logic to take them from the args
        if "table_border" in flags:
            properties.update({"table_border": flags["table_border"]})
        if "markdown" in flags:
            properties.update({"markdown": flags["markdown"]})
        if "type" in properties:
            question_type = properties["type"]
        # TODO: add exception to track the missing types, requires further refactoring, e.g. type is not passed to variants
        if "title" not in properties:
            properties.update({"title": flags["title"]})
        question = question_factory.create_question(question_type, **properties)
        if strict_validation:
            errors = question.validate()
            if errors:
                message = (
                    "---\nThe following question did not pass strict validation:\n"
                    f"{yaml.safe_dump(properties)}"
                    f"Errors:\n- {bullet.join(errors)}"
                )
                print(message, file=sys.stderr)
                continue
        yield question


def generate_moodle_questions(**kwargs):
    # TODO: Maybe a builder can help with this complexity of parameters
    """Generate an XML document containing Moodle questions.

    The type of Moodle question is defined by `question_type`.
    The actual question is defined by `question_class`.
    """
    # Create question instances from a list of YAML documents.
    questions = list(
        load_questions(QuestionFactory, not kwargs["lenient"], yaml.safe_load_all(kwargs["input"]), **kwargs)
    )

    # Add question index to title
    if kwargs["add_question_index"]:
        for index, question in enumerate(questions, 1):
            question.title = f"{question.title} ({index})"

    # Newline constant to make the "\n".join(...) work below.
    newline = "\n"
    # Generate Moodle XML
    xml = f"""\
    <?xml version="1.0" encoding="UTF-8"?>
    <quiz>
{newline.join([question.generate_xml() for question in questions])}
    </quiz>
    """
    xml = textwrap.dedent(xml)
    print(xml, file=kwargs["output"])
