import base64
import re
from pathlib import Path

import markdown
import sqlparse  # type: ignore
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
        r"""<img alt="[^"]*" src="([^"]*).(png|svg)" (?:style="[^"]*" )?/>|"""
        r"""background-image:\s*url\('([^']*).(png|svg)'\)"""
    )  # TODO merge these regexes eventually
    for match in re_img.finditer(text):
        filename = Path(match.group(1) if match.group(1) else match.group(3)).with_suffix(
            f".{match.group(2) if match.group(2) else match.group(4)}"
        )
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
    text = format_tables(text) if flags["table_styling"] else text
    return text


def parse_code(code: str, parser: str | None = None) -> str:
    """Parses code with a chosen parser.

    Args:
        code: code to be parsed.
        parser: parser to be used.

    Returns:
        str: Code that has been parsed with the selected parser.
    """
    match (parser):
        case None:
            return code
        case "sqlparse":
            return sqlparse.format(code, reindent=True, keyword_case="upper")  # type: ignore
        case "sqlparse-no-indent":
            return sqlparse.format(code, reindent=False, keyword_case="upper")  # type: ignore
        case _:
            raise ParsingError(f"Parser not supported: {parser}")


class ParsingError(Exception):
    """Exception raised when a YAML file fails to parse into its designated question type."""


class ValidationError(Exception):
    """Exception raised when a question does not pass strict validation."""
