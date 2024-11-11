from typing import Any

from loguru import logger

from moodle_tools import ParsingError
from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import preprocess_text


class NumericalQuestion(Question):
    """General template for a numerical question."""

    QUESTION_TYPE = "numerical"
    XML_TEMPLATE = "numerical.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answers: list[str],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        **flags: bool,
    ):
        super().__init__(question, title, category, grade, general_feedback, **flags)

        # Transform simple string answers into complete answers
        self.answers: list[dict[str, Any]] = [
            answer if isinstance(answer, dict) else {"answer": answer} for answer in answers
        ]

        # Update points if not provided or raise an error if they are not consistent
        # TODO: Create corner case test for this functionality
        all_points_specified = len(
            list(filter(lambda x: "points" in x and 0 <= x["points"] <= 100, self.answers))
        ) == len(self.answers)
        if all_points_specified and 100 not in [answer["points"] for answer in self.answers]:
            raise ParsingError("At least one answer must have 100 points if you specify points.")
        if not all_points_specified:
            logger.debug("Not all answer points specified, first answer is assumed to be correct.")
            for i, answer in enumerate(self.answers):
                if "points" not in answer:
                    answer["points"] = 100 if i == 0 else 0
                else:
                    raise ParsingError("All or no answers must have points specified.")
                if "feedback" not in answer:
                    answer["feedback"] = ""
                else:
                    answer["feedback"] = preprocess_text(answer["feedback"], **flags)

    def validate(self) -> list[str]:
        errors = super().validate()
        num_full_points: int = len(list(filter(lambda x: x["points"] == 100, self.answers)))
        if num_full_points == 0:
            errors.append("At least one answer must have 100 points.")
        for answer in self.answers:
            if "feedback" not in answer and answer["points"] != 100:
                errors.append(f"The incorrect answer '{answer['answer']}' has no feedback.")
        return errors


class NumericalQuestionAnalysis(QuestionAnalysis):
    pass
