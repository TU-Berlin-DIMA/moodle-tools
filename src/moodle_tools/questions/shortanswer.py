import re

from moodle_tools.questions.numerical import NumericalQuestion
from moodle_tools.questions.question import QuestionAnalysis


class ShortAnswerQuestion(NumericalQuestion):
    """General template for a short answer question."""

    QUESTION_TYPE = "shortanswer"
    XML_TEMPLATE = "shortanswer.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        answers: list[str],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        answer_case_sensitive: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(question, title, answers, category, grade, general_feedback, **flags)
        self.answer_case_sensitive = answer_case_sensitive

        self.inline_answer_box()

    def inline_answer_box(self) -> None:
        re_box = re.compile(r"\[\[ANSWERBOX(?:|=(\d+))\]\]")
        answerbox = re.search(re_box, self.question)

        if answerbox:
            answerbox_length = max(int(answerbox.group(1)), 5) if answerbox.group(1) else 10
            self.question = re.sub(re_box, "_" * answerbox_length, self.question)


class ShortAnswerQuestionAnalysis(QuestionAnalysis):
    pass
