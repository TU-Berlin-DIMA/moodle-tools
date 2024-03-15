import base64
import csv
import re
import sys
import textwrap
from statistics import median

import markdown
import yaml


def optional_text(text: str | None) -> str:
    return f"<![CDATA[{text}]]>" if text else ""


def convert_markdown(text):
    return markdown.markdown(text, extensions=["tables", "attr_list"])


def table_borders(text):
    return text.replace("<table>", '<table border="1px solid black" style="margin-bottom: 2ex">')


# It is not possible to assign attribute lists to table elements.
# So we edit the HTML directly.


def inline_image(text: str) -> str:
    """This function detects SVG or PNG images and inlines them."""
    re_img = re.compile('<img alt="[^"]*" src="([^"]*).(png|svg)" (?:style="[^"]*" )?/>')
    for match in re_img.finditer(text):
        filename = f"{match.group(1)}.{match.group(2)}"
        with open(filename, "rb") as file:
            base64_str = base64.b64encode(file.read()).decode("utf-8")
            img_type = "svg+xml" if match.group(2) == "svg" else match.group(2)
            text = text.replace(filename, f"data:image/{img_type};base64,{base64_str}")

    return text


def preprocess_text(text, **flags):
    """Function that preprocess the text depending on the flags.

    Flags:
    - markdown: Bool
    - table_border: Bool
    """
    text = convert_markdown(text) if (flags["markdown"]) else text
    text = inline_image(text)
    text = table_borders(text) if (flags["table_border"]) else text
    return text


class FormatError(BaseException):
    pass


def load_questions(question_class, strict_validation, yaml_files, **flags):
    """Iterate over the YAML files and generate a question for each YAML document.

    If `strict_validation` is set, filter those questions that contain missing optional
    information (e.g., feedback).
    """
    bullet = "\n- "

    question_type = None

    for properties in yaml_files:
        # TODO: List all the potential flags for preprocessing text or make a better logic to take them from the args
        properties.update({"table_border": flags["table_border"]})
        properties.update({"markdown": flags["markdown"]})
        if 'type' in properties:
            question_type = properties['type']
            properties
        if "title" not in properties:
            properties.update({"title": flags["title"]})
        question = question_class(**properties)
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


def generate_moodle_questions(generate_question_xml, question_class, **kwargs):
    # TODO: Maybe a builder can help with this complexity of parameters
    """Generate an XML document containing Moodle questions.

    The type of Moodle question is defined by `question_type`.
    The actual question is defined by `question_class`.
    """
    # Create question instances from a list of YAML documents.
    questions = list(
        load_questions(question_class, not kwargs["lenient"], yaml.safe_load_all(kwargs["input"]), **kwargs)
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
{newline.join([generate_question_xml(question) for question in questions])}
    </quiz>
    """
    xml = textwrap.dedent(xml)
    print(xml, file=kwargs["output"])


def normalize_questions(infile, outfile, handlers):
    # Process responses from input CSV file
    for row in csv.DictReader(infile, delimiter=",", quotechar='"'):
        for handler in handlers:
            q_num = handler.question_number
            handler.process_response(
                row[f"Question {q_num}"],
                row[f"Response {q_num}"],
                row[f"Right answer {q_num}"],
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
    print(f"Median grade: {median_grade:1.1f}, MAD: {mad:1.1f}", file=sys.stderr)
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
