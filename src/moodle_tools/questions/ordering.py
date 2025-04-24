from typing import Any
from venv import logger

from moodle_tools.enums import DisplayFormatEnum, EnumerationStyle, GradingType, SelectType
from moodle_tools.questions.question import Question
from moodle_tools.utils import parse_markdown, preprocess_text


class OrderingQuestion(Question):
    """General template for an Ordering question."""

    QUESTION_TYPE = "ordering"
    XML_TEMPLATE = "ordering.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        answers: list[str],
        layout_type: str = "vertical",
        select_type: str = "all_elements",
        subset_size: int = -1,
        grading_type: str = "all_or_nothing",
        show_grading_details: bool = False,
        numbering_style: str = "numbers",
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)

        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partial_feedback = preprocess_text(partial_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)

        self.layout_type: DisplayFormatEnum | int = DisplayFormatEnum.from_str(layout_type)
        self.select_type = SelectType.from_str(select_type)
        self.subset_size = subset_size
        self.grading_type = GradingType.from_str(grading_type)
        self.show_grading_details = show_grading_details
        self.numbering_style = EnumerationStyle.from_str(numbering_style)

        logger.warning(
            "Currently, some settings for ordering questions are not imported correctly. "
            "Please check manually afterwards."
        )

        self.answers: list[dict[str, Any]] = [
            {"idx": idx + 1, "answer": parse_markdown(answer)}
            for idx, answer in enumerate(answers)
        ]

        if self.layout_type not in [DisplayFormatEnum.VERTICAL, DisplayFormatEnum.HORIZONTAL]:
            logger.warning("Invalid layout type. Defaulting to vertical.")
            self.layout_type = DisplayFormatEnum.VERTICAL

        match self.layout_type:
            case DisplayFormatEnum.VERTICAL:
                self.layout_type = 0
            case DisplayFormatEnum.HORIZONTAL:
                self.layout_type = 1

    def validate(self) -> list[str]:
        error_list = super().validate()

        if (
            self.select_type in [SelectType.RANDOM_ELEMENTS, SelectType.CONNECTED_ELEMENTS]
            and self.subset_size < 1
        ):
            error_list.append(
                "Subset size must be at least 2 for select types that sample a subset of answers."
            )

        return error_list
