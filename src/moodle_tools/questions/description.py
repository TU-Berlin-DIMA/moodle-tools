from moodle_tools.questions.question import Question, QuestionAnalysis


class Description(Question):
    """General template for a description that does not have an answer option."""

    QUESTION_TYPE = "description"
    XML_TEMPLATE = "description.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 0.0,
        general_feedback: str = "",
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)

    def validate(self) -> list[str]:
        return []


class DescriptionAnalysis(QuestionAnalysis):
    pass
