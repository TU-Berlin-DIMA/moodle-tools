import base64
import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import dacite
import markdown
from loguru import logger
from lxml import etree
from lxml.etree import ElementBase

try:
    import sqlparse  # type: ignore
except ImportError:
    sqlparse = None


class TextAnchor(IntEnum):
    START = 0
    MIDDLE = 50
    END = 100

    @classmethod
    def from_str(cls, value: str) -> "TextAnchor":
        return cls[value.upper()] if value else cls.MIDDLE


@dataclass
class OverlayItem:
    """Dataclass to hold overlay item information."""

    value: str
    x: float
    y: float
    text_anchor: TextAnchor
    xml: ElementBase
    matches_extract: bool = False

    def as_div(self, indent: int, vertical_offset: float) -> str:
        """Return the overlay item as a div element."""
        return f'{" " * indent}<div style="position: absolute; left: {self.x}px; top: {self.y}px; transform: translate({-self.text_anchor}%, -{vertical_offset}%);">{self.value}</div> <!--  -->'  # TODO what is a good identifying comment?


@dataclass
class ImageOverlay:
    """Dataclass to hold image overlay information."""

    image: str
    gap_image: str
    debug_image: str | None = None
    scale_coords: float = 1.0
    scale_image: float = 1.0
    vertical_offset: float = 0.5
    overlay_items: dict[str, OverlayItem] = None


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


def overlay_image(
    question: str,
    image_overlay: dict[str, dict[str, str | float]],
    extract_regex: list[str],
    **flags: bool,
) -> str:
    RE_IMAGEBOX = r"\[\[IMAGEBOX=(\w+)\]\]"

    if not extract_regex:
        return question

    if not image_overlay:
        return question

    for image, overlay_data in image_overlay.items():
        overlay: ImageOverlay = dacite.from_dict(data_class=ImageOverlay, data=overlay_data)

        if not overlay.gap_image:
            raise ValueError("gap_image must be provided for Image Overlays.")

        with open(overlay.image, "rb") as img_file:
            image_data = etree.fromstring(img_file.read())

        min_x, min_y, width, height = [int(val) for val in image_data.get("viewBox").split(" ")]
        width *= overlay.scale_coords
        height *= overlay.scale_coords

        doc_width = int(re.search(r"(\d+)", image_data.get("width", width)).group(1))
        doc_height = int(re.search(r"(\d+)", image_data.get("height", height)).group(1))

        def get_text_anchor(elem: ElementBase) -> TextAnchor:
            style = elem.get("style", "")
            re_text_anchor = re.compile(r"text-anchor:\s*(\w+)")
            match = re_text_anchor.search(style)
            if not match:
                parent = elem.getparent().get("style", "")
                match = re_text_anchor.search(parent)

            return TextAnchor.from_str(match.group(1) if match else "middle")

        overlay_items = [
            OverlayItem(
                value=elem.text.strip(),
                x=(float(elem.get("x")) - min_x) * overlay.scale_coords,
                y=(float(elem.get("y")) - min_y) * overlay.scale_coords,
                text_anchor=get_text_anchor(elem),
                xml=elem,
            )
            for elem in image_data.iter()
            if elem.text and elem.text.strip()
        ]

        for extract_re in extract_regex:
            re_extract = re.compile(extract_re)
            for item in overlay_items:
                if re_extract.search(item.value):
                    item.matches_extract = True

        overlay_items.sort(key=lambda x: x.value)

        overlay_items_str = "\n".join(
            item.as_div(indent=8, vertical_offset=overlay.vertical_offset)
            for item in overlay_items
        )

        for item in overlay_items:
            item.xml.text = ""

        cleaned_image = etree.tostring(image_data, encoding="utf8")
        with Path(overlay.gap_image).open("wb") as img_file:
            img_file.write(cleaned_image)

        overlay_str = f"""
        <div style="position:relative;transform: scale({overlay.scale_image});transform-origin: 0 0;">
            <div style="background-image:url('{overlay.gap_image}'); width: {width}px; height: {height}px; background-size: 100% 100%">
        {overlay_items_str}
            </div>
        </div>
        """

        replace_box = re.search(RE_IMAGEBOX, question)

        if not replace_box:
            raise ParsingError(f"Box for image '{image}' not found in the question text.")

        question = question.replace(replace_box.group(0), overlay_str)

        # FIXME if comments are set, add debug image output

        # if overlay.debug_image:
        #     for item in overlay_items:
        #         item.xml.text = f"[[{item.internal_id}]]"
        #
        #     debug_image_data = etree.tostring(image_data, encoding="utf8")
        #     with Path(overlay.debug_image).open("wb") as img_file:
        #         img_file.write(debug_image_data)


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
