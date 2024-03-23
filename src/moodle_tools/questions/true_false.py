from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import preprocess_text


class TrueFalseQuestion(Question):
    """General template for a True/False question."""

    QUESTION_TYPE = "truefalse"
    TEMPLATE = "true_false.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        category: str | None = None,
        correct_answer: bool = True,
        general_feedback: str = "",
        correct_feedback: str = "",
        wrong_feedback: str = "",
        **flags: bool,
    ):
        super().__init__(question, title, category, **flags)
        self.general_feedback = preprocess_text(general_feedback, **flags)
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.wrong_feedback = preprocess_text(wrong_feedback, **flags)

        # Convert boolean answers to strings
        self.correct_answer, self.wrong_answer = (
            ("true", "false") if correct_answer else ("false", "true")
        )

    def validate(self) -> list[str]:
        errors = []
        if self.correct_answer == self.wrong_answer:
            # How can this happen?!
            errors.append("Correct answer == wrong answer")
        if not self.general_feedback:
            errors.append("No general feedback")
        if not self.wrong_feedback:
            errors.append("No feedback for wrong answer")
        return errors


class TrueFalseQuestionAnalysis(QuestionAnalysis):
    pass
