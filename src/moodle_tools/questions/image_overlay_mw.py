import re
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import dacite
import yaml
from loguru import logger
from lxml import etree
from lxml.etree import ElementBase

from moodle_tools.enums import ShuffleAnswersEnum
from moodle_tools.questions.missing_words import MissingWordsQuestion, OptionItem


class TextAnchor(IntEnum):
    START = 0
    MIDDLE = 50
    END = 100

    @classmethod
    def from_str(cls, value: str) -> "TextAnchor":
        return cls[value.upper()] if value else cls.MIDDLE


@dataclass
class InputItem:
    value: str
    group: str
    remark: str
    x: float
    y: float
    text_anchor: TextAnchor
    xml: ElementBase

    @property
    def internal_id(self) -> str:
        return f"{self.group}-{self.value[0:3]}-{self.remark}"


RE_INPUT = r"(.+)\s*\[([A-T])(:(\w+))?\]\s*"
RE_IMAGEBOX = r"\[\[IMAGEBOX\]\]"


class ImageOverlayMissingWordsQuestion(MissingWordsQuestion):
    def __init__(
        self,
        question: str,
        title: str,
        options: list[dict[str, str | int]],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        shuffle_answers: ShuffleAnswersEnum = ShuffleAnswersEnum.SHUFFLE,
        image: str | None = None,
        gap_image: str | None = None,
        debug_image: str | None = None,
        scale_coords: float = 1.0,
        scale_image: float = 1.0,
        vertical_offset: float = 0.5,
        **flags: bool,
    ):
        if not image:
            raise ValueError(
                "Path to Image must be provided for ImageOverlayMissingWordsQuestion."
            )
        if not gap_image:
            raise ValueError(
                "Path to store generated image with gaps must be provided for ImageOverlayMissingWordsQuestion."
            )

        if any(option.get("ordinal", 1) < 1 for option in options):
            raise ValueError("Ordinal values must be larger than 1.")

        options = [
            dacite.from_dict(data_class=OptionItem, data=option)
            if isinstance(option, dict)
            else option
            for option in options
        ]

        if any(re.search(r"\d+", options.group) for options in options):
            raise ValueError(
                "Sorry, this question type requires letter-based groups between A and T."
            )

        self.image = image
        with open(image, "rb") as img_file:
            self.image_data = etree.fromstring(img_file.read())

        min_x, min_y, width, height = [
            int(val) for val in self.image_data.get("viewBox").split(" ")
        ]
        width *= scale_coords
        height *= scale_coords

        doc_width = int(re.search(r"(\d+)", self.image_data.get("width", width)).group(1))
        doc_height = int(re.search(r"(\d+)", self.image_data.get("height", height)).group(1))

        text_inputs = [
            (elem, re.match(RE_INPUT, elem.text.strip()))
            for elem in self.image_data.iter()
            if elem.text and elem.text.strip() and re.match(RE_INPUT, elem.text.strip())
        ]

        def get_text_anchor(elem: ElementBase) -> TextAnchor:
            style = elem.get("style", "")
            re_text_anchor = re.compile(r"text-anchor:\s*(\w+)")
            match = re_text_anchor.search(style)
            if not match:
                parent = elem.getparent().get("style", "")
                match = re_text_anchor.search(parent)

            return TextAnchor.from_str(match.group(1) if match else "middle")

        input_items = [
            InputItem(
                value=elem[1].group(1).strip(),
                group=elem[1].group(2).strip(),
                remark=elem[1].group(4) if elem[1].group(4) else "",
                x=(float(elem[0].get("x")) - min_x) * scale_coords,
                y=(float(elem[0].get("y")) - min_y) * scale_coords,
                text_anchor=get_text_anchor(elem[0]),
                xml=elem[0],
            )
            for elem in text_inputs
        ]

        input_items.sort(key=lambda x: (x.group, x.value, x.remark))

        overlay_items = ""
        last_group = ""
        indent = " " * 8

        for item in input_items:
            if item.group != last_group:
                last_group = item.group
                overlay_items += f"\n{indent}<!-- Group {item.group} -->\n"

            overlay_items += f"""{indent}<div style="position: absolute; left: {item.x}px; top: {item.y}px; transform: translate({-item.text_anchor}%, -{vertical_offset * 100}%);">[["{item.value}"]]</div> <!-- {item.internal_id} -->\n"""

        for item in input_items:
            item.xml.text = ""

        cleaned_image = etree.tostring(self.image_data, encoding="utf8")
        with Path(gap_image).open("wb") as img_file:
            img_file.write(cleaned_image)

        overlay = f"""
<div style="position:relative;transform: scale({scale_image});transform-origin: 0 0;">
    <div style="background-image:url('{gap_image}'); width: {width}px; height: {height}px; background-size: 100% 100%">
{overlay_items}
    </div>
</div>
"""

        imagebox = re.search(RE_IMAGEBOX, question)
        if imagebox:
            question = re.sub(RE_IMAGEBOX, overlay, question)
        else:
            question += "\n\n" + overlay

        # do an anti-join between input_items and options to find new options
        options_from_image = [
            OptionItem(answer=item.value, group=item.group) for item in input_items
        ]

        new_options_from_image = sorted(
            set(
                [item for item in options_from_image if item not in options],
            ),
            key=lambda x: (x.group, x.answer),
        )

        if new_options_from_image:
            logger.warning(
                "Appending {} new options from image to lit of options",
                len(new_options_from_image),
            )
            logger.warning(
                "Please add them to the list of options in order to prevent messed-up answer sorting: \n{}",
                yaml.dump(
                    [
                        {"answer": item.answer, "group": item.group}
                        for item in new_options_from_image
                    ],
                    indent=2,
                ),
            )
            options.extend(new_options_from_image)

        if debug_image:
            for item in input_items:
                item.xml.text = f"[[{item.internal_id}]]"

            debug_image_data = etree.tostring(self.image_data, encoding="utf8")
            with Path(debug_image).open("wb") as img_file:
                img_file.write(debug_image_data)

        super().__init__(
            question=question,
            title=title,
            options=options,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            correct_feedback=correct_feedback,
            partial_feedback=partial_feedback,
            incorrect_feedback=incorrect_feedback,
            shuffle_answers=shuffle_answers,
            **flags,  # type: ignore
        )
