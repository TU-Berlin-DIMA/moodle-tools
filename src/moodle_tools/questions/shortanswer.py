from moodle_tools.questions.numerical import NumericalQuestion
from moodle_tools.questions.question import QuestionAnalysis


class ShortAnswerQuestion(NumericalQuestion):
    """General template for a short answer question."""

    QUESTION_TYPE = "shortanswer"
    XML_TEMPLATE = "shortanswer.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answers: list[str],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        answer_case_sensitive: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(
            question=question,
            title=title,
            answers=answers,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            **flags,
        )
        self.answer_case_sensitive = answer_case_sensitive


class ShortAnswerQuestionAnalysis(QuestionAnalysis):
    pass
