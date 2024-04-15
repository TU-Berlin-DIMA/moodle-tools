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
        # TODO: Create corner case test fr this functionality
        num_full_points: int = len(list(filter(lambda x: x["points"] == 100, self.answers)))
        for i, answer in enumerate(self.answers):
            if "points" not in answer:
                if i == 0 and num_full_points == 0:
                    answer["points"] = 100
                    # TODO: Change this print to a LOG
                    print("First answer is assumed to be correct.")
                else:
                    answer["points"] = 0

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
