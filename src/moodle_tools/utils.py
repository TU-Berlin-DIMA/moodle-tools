import base64
import os
import re
from pathlib import Path
from typing import Any, Iterator

import markdown
import sqlparse  # type: ignore
from loguru import logger
from markdownify import markdownify  # type: ignore


def format_tables(text: str) -> str:
    """Add bootstrap style classes to table tags."""
    return text.replace("<table>", '<table class="table table-sm w-auto">')


def parse_markdown(text: str) -> str:
    """Parse the question text as markdown."""
    return markdown.markdown(text, extensions=["tables", "attr_list", "md_in_html"])


def parse_html(text: str) -> str:
    """Parse the question text from HTML to markdown."""
    # TODO: Implement the function.
    md_text: str = markdownify(text).strip()
    return md_text


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


# def transpile_dict_to_yaml(properties: dict[str, str | Any | None]) -> str:
#    pass


def iterate_inputs(
    files: Iterator[str | os.PathLike[Any]], file_type: str, strict: bool = False
) -> Iterator[Path]:
    # pylint: disable=too-many-nested-blocks
    # TODO: Refactor and remove pylint disable nested blocks
    """Iterate over a collection of input files or directories.

    Args:
        files: An iterator of file paths or directory paths.
        strict: If True, raise an IOError if a path is neither a file nor a directory.
                If False, ignore such paths.

    Yields:
        Iterator[Path]: A generator that yields Path objects representing input files.
    """
    supported_file_types: dict[str, list[str]] = {"YAML": ["yml", "yaml"], "XML": ["xml"]}
    if file_type in supported_file_types:
        for file in files:
            path = Path(file)
            # Ignore the extension if the file is explicitly specified on the command line.
            if path.is_file():
                yield path
            elif path.is_dir():
                # TODO: Refactor this to use path.walk() once we drop Python 3.11 support
                for dirpath, _, filenames in os.walk(path):
                    for filename in filenames:
                        # Only process files in folders that match with supported types
                        # to exclude resources, like images.
                        for file_type_variant in supported_file_types[file_type]:
                            if filename.endswith(file_type_variant):
                                yield Path(dirpath) / filename
            elif strict:
                raise IOError(f"Not a file or folder: {file}")
            else:
                logger.debug(f"{file} is neither a file nor a folder - ignoring.")
    else:
        raise ParsingError(f"Unsupported File Type: {file_type}.")


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
