from typing import Any

from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import preprocess_text


class NumericalQuestion(Question):
    """General template for a numerical question."""

    QUESTION_TYPE = "numerical"
    TEMPLATE = "numerical.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        answers: list[str],
        category: str | None = None,
        general_feedback: str = "",
        **flags: bool,
    ):
        super().__init__(question, title, category, **flags)
        self.general_feedback = preprocess_text(general_feedback, **flags)

        # Transform simple string answers into complete answers
        self.answers: list[dict[str, Any]] = [
            answer if isinstance(answer, dict) else {"answer": answer} for answer in answers
        ]

        # Update missing answer points and feedback
        for i, answer in enumerate(self.answers):
            if "points" not in answer:
                answer["points"] = 100 if i == 0 else 0

    def validate(self) -> list[str]:
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback.")
        num_full_points: int = len(list(filter(lambda x: x["points"] == 100, self.answers)))
        if num_full_points != 1:
            errors.append("Exactly one answer must have 100 points.")
        for answer in self.answers:
            if "feedback" not in answer and answer["points"] != 100:
                errors.append(f"The incorrect answer '{answer['answer']}' has no feedback.")
        return errors


class NumericalQuestionAnalysis(QuestionAnalysis):
    pass
