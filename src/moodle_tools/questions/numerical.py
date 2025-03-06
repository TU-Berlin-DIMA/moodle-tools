import re
from typing import Any

from loguru import logger

from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import ParsingError, preprocess_text


class NumericalQuestion(Question):
    """General template for a numerical question."""

    QUESTION_TYPE = "numerical"
    XML_TEMPLATE = "numerical.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answers: list[str] | list[dict[str, Any]],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)

        self.answers = self.expand_answers_from_list(answers)
        self.inline_answer_box()
        self.fix_answer_points(**flags)

    @staticmethod
    def expand_answers_from_list(
        answers: list[str] | list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Transform simple string answers into complete answers."""
        return [answer if isinstance(answer, dict) else {"answer": answer} for answer in answers]

    def inline_answer_box(self) -> None:
        re_box = re.compile(r"\[\[ANSWERBOX(?:|=(\d+))\]\]")
        answerbox = re.search(re_box, self.question)

        if answerbox:
            answerbox_length = max(int(answerbox.group(1)), 5) if answerbox.group(1) else 10
            self.question = re.sub(re_box, "_" * answerbox_length, self.question)

    def fix_answer_points(self, **flags: bool) -> None:
        # Update points if not provided or raise an error if they are not consistent
        # TODO: Create corner case test for this functionality

        all_points_specified = all("points" in answer for answer in self.answers)
        no_points_specified = all("points" not in answer for answer in self.answers)

        if not (all_points_specified or no_points_specified):
            raise ParsingError("All or no answers must have points specified.")

        if all_points_specified and any(answer["points"] > 100 for answer in self.answers):
            raise ParsingError("Points must be between 0 and 100.")

        if all_points_specified and all(0 <= answer["points"] < 100 for answer in self.answers):
            raise ParsingError("At least one answer must have 100 points.")

        if no_points_specified:
            logger.debug("Not all answer points specified, first answer is assumed to be correct.")
            for i, answer in enumerate(self.answers):
                answer["points"] = 100 if i == 0 else 0
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
