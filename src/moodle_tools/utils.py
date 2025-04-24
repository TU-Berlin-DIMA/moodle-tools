import base64
import re
from pathlib import Path

import markdown
from loguru import logger

try:
    import sqlparse  # type: ignore
except ImportError:
    sqlparse = None


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


def format_code(code: str, formatter: str | None = None) -> str:
    """Format code with a chosen formatter.

    Args:
        code: code to be parsed.
        formatter: formatter to be used.

    Returns:
        str: Code that has been parsed with the selected formatter.
    """
    match formatter:
        case None:
            return code
        case "sqlparse":
            if sqlparse is None:
                logger.error("sqlparse is not installed. Please install it to format code.")
                return code
            return sqlparse.format(code, reindent=True, keyword_case="upper")  # type: ignore
        case "sqlparse-no-indent":
            if sqlparse is None:
                logger.error("sqlparse is not installed. Please install it to format code.")
                return code
            return sqlparse.format(code, reindent=False, keyword_case="upper")  # type: ignore
        case _:
            raise ParsingError(f"Formatter not supported: {formatter}")


def parse_filesize(size: str | int) -> int:
    """Parse a human-readable filesize into bytes.

    Args:
        size: Human-readable filesize.

    Returns:
        int: Filesize in bytes.
    """
    if isinstance(size, int):
        return size

    if size.isdigit():
        return int(size)

    pattern = r"(^\d*[.]?\d+)\s*([KMGTP])*(i)*([Bb])"

    match = re.match(pattern, size)
    if not match:
        raise ValueError(f"Invalid filesize: {size}")

    num, exp, power, unit = match.groups()
    if not num or not unit:
        raise ValueError(f"Invalid filesize: {size}")

    exp = exp if exp else " "
    size_float = float(num) * (1024 if power == "i" else 1000) ** " KMGTPE".index(exp)
    return int(size_float) if unit == "B" else int(size_float / 8)


class ParsingError(Exception):
    """Exception raised when a YAML file fails to parse into its designated question type."""
