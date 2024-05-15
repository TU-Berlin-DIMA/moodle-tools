import base64
import re

import markdown
import sqlglot
import sqlparse  # type: ignore


def add_table_borders(text: str) -> str:
    """Add a border to tables in the question text."""
    return text.replace("<table>", '<table border="1px solid black" style="margin-bottom: 2ex">')


def parse_markdown(text: str) -> str:
    """Parse the question text as markdown."""
    return markdown.markdown(text, extensions=["tables", "attr_list"])


def inline_images(text: str) -> str:
    """Detect SVG or PNG images in a question text and inline them with base64 encoding."""
    re_img = re.compile('<img alt="[^"]*" src="([^"]*).(png|svg)" (?:style="[^"]*" )?/>')
    for match in re_img.finditer(text):
        filename = f"{match.group(1)}.{match.group(2)}"
        with open(filename, "rb") as file:
            base64_str = base64.b64encode(file.read()).decode("utf-8")
            img_type = "svg+xml" if match.group(2) == "svg" else match.group(2)
            text = text.replace(filename, f"data:image/{img_type};base64,{base64_str}")

    return text


def preprocess_text(text: str, **flags: bool) -> str:
    """Function that preprocess the text depending on the flags.

    Flags:
    - markdown: Bool
    - table_border: Bool
    """
    text = parse_markdown(text) if flags["markdown"] else text
    text = inline_images(text)
    text = add_table_borders(text) if flags["table_border"] else text
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
        case "sqlglot":
            return ";\n\n".join(
                sqlglot.transpile(
                    code,
                    read="duckdb",
                    write="duckdb",
                    pretty=True,
                    normalize_functions="upper",
                )
            )
        case _:
            raise ParsingError(f"Parser not supported: {parser}")


class ParsingError(Exception):
    """Exception raised when a YAML file fails to parse into its designated question type."""


class ValidationError(Exception):
    """Exception raised when a question does not pass strict validation."""
