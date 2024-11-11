from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question


class ClozeQuestion(Question):
    """General template for a Cloze question."""

    QUESTION_TYPE = "cloze"
    XML_TEMPLATE = "cloze.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)

    def validate(self) -> list[str]:
        errors = super().validate()
        return errors


class ClozeQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_id: str) -> None:
        super().__init__(question_id, r"(.*?): (.*?)", "; ")
