from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text


class ClozeQuestion(Question):
    """General template for a Cloze question."""

    QUESTION_TYPE = "cloze"
    TEMPLATE = "cloze.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        category: str | None = None,
        general_feedback: str = "",
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, **flags)
        self.general_feedback = preprocess_text(general_feedback, **flags)

    def validate(self) -> list[str]:
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback")
        return errors


class ClozeQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_number: int | str) -> None:
        super().__init__(question_number, r"(.*?): (.*?)", "; ")
