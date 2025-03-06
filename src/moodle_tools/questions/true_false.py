from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import preprocess_text


class TrueFalseQuestion(Question):
    """General template for a True/False question."""

    QUESTION_TYPE = "truefalse"
    XML_TEMPLATE = "true_false.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "",
        incorrect_feedback: str = "",
        correct_answer: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)

        # Convert boolean answers to strings
        self.correct_answer, self.wrong_answer = (
            ("true", "false") if correct_answer else ("false", "true")
        )

    def validate(self) -> list[str]:
        errors = super().validate()
        if self.correct_answer == self.wrong_answer:
            errors.append("Correct answer is equal to the wrong answer.")
        if not self.incorrect_feedback:
            errors.append("No feedback for wrong answer provided.")
        return errors


class TrueFalseQuestionAnalysis(QuestionAnalysis):
    pass
