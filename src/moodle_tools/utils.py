import base64
import re
from pathlib import Path
from typing import Any

import markdown
import sqlparse  # type: ignore
import yaml
from jinja2 import Environment
from loguru import logger


def format_tables(text: str) -> str:
    """Add bootstrap style classes to table tags."""
    return text.replace("<table>", '<table class="table table-sm w-auto">')


def parse_markdown(text: str) -> str:
    """Parse the question text as markdown."""
    return markdown.markdown(text, extensions=["tables", "attr_list", "md_in_html"])


def inline_images(text: str) -> str:
    """Detect SVG or PNG images in a question text and inline them with base64 encoding."""
    re_img = re.compile(
        r"""(?:<img alt="[^"]*" src="|"""  # opening tag for html img
        r"""background-image:\s*url\(')"""  # opening css background-image property
        r"""([^"']*)"""  # image path capture group
        r"""(?:'|"""  # closing quote for css background-image property
        r"""" (?:style="[^"]*" )?/>)"""  # closing tag for html img
    )
    for match in re_img.finditer(text):
        filename = Path(match.group(1))
        with filename.open("rb") as file:
            base64_str = base64.b64encode(file.read()).decode("utf-8")
            img_type = "svg+xml" if filename.suffix == ".svg" else filename.suffix.replace(".", "")
            text = text.replace(
                f'src="{filename}"', f'src="data:image/{img_type};base64,{base64_str}"'
            ).replace(f"url('{filename}')", f"url('data:image/{img_type};base64,{base64_str}')")

    return text


def preprocess_text(text: str | None, **flags: bool) -> str:
    """Function that preprocess the text depending on the flags.

    Flags:
    - markdown: Bool
    - table_styling: Bool
    """
    if not text:
        logger.debug("Received empty text, doing nothing.")
        return ""

    text = parse_markdown(text) if flags["markdown"] else text
    text = inline_images(text)
    return format_tables(text) if flags["table_styling"] else text


def parse_code(code: str, parser: str | None = None) -> str:
    """Parses code with a chosen parser.

    Args:
        code: code to be parsed.
        parser: parser to be used.

    Returns:
        str: Code that has been parsed with the selected parser.
    """
    match parser:
        case None:
            return code
        case "sqlparse":
            return sqlparse.format(code, reindent=True, keyword_case="upper")  # type: ignore
        case "sqlparse-no-indent":
            return sqlparse.format(code, reindent=False, keyword_case="upper")  # type: ignore
        case _:
            raise ParsingError(f"Parser not supported: {parser}")


def update_question_from_template(
    question: dict[str, Any], template: dict[str, Any], j2_env: Environment | None = None
) -> dict[str, Any]:
    """Update a question with templates values described in the template dictionary.

    Args:
        question: Question dictionary to be updated.
        template: Template dictionary with the values to update.
        j2_env: Jinja2 environment to use for rendering.

    Returns:
        dict: Updated question dictionary.
    """
    if not j2_env:
        j2_env = Environment(lstrip_blocks=True, trim_blocks=True)

    for key_outer, value_outer in template.items():
        if isinstance(value_outer, dict):
            template_keys = list(value_outer.keys())

            for key_inner in value_outer.keys():
                if key_inner in question.keys():
                    template_keys.remove(key_inner)
                    update_question_from_template(question[key_outer], template[key_outer], j2_env)

            if template_keys:
                applicable_keys = {
                    key: value for key, value in value_outer.items() if key in template_keys
                }
                template_str = yaml.safe_dump(question[key_outer])
                rendered = j2_env.from_string(template_str).render(applicable_keys)
                question[key_outer] = yaml.safe_load(rendered)

    return question


class ParsingError(Exception):
    """Exception raised when a YAML file fails to parse into its designated question type."""


class ValidationError(Exception):
    """Exception raised when a question does not pass strict validation."""
