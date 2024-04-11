from typing import Any

from moodle_tools.questions.question import Question, QuestionAnalysis


class NumericalQuestion(Question):
    """General template for a numerical question."""

    QUESTION_TYPE = "numerical"
    XML_TEMPLATE = "numerical.xml.j2"

    def __init__(
        self,
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

        # Update missing answer points and feedback
        for i, answer in enumerate(self.answers):
            if "points" not in answer:
                answer["points"] = 100 if i == 0 else 0

    def validate(self) -> list[str]:
        errors = super().validate()
        for answer in self.answers:
            if "feedback" not in answer and answer["points"] != 100:
                errors.append(f"The incorrect answer '{answer['answer']}' has no feedback.")
        return errors


class NumericalQuestionAnalysis(QuestionAnalysis):
    pass
