import re

from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text


class MissingWordsQuestion(Question):

    QUESTION_TYPE = "gapselect"
    TEMPLATE = "missing_words.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        options: list[dict[str, str]],
        category: str | None = None,
        general_feedback: str = "",
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        **flags: bool,
    ):
        super().__init__(question, title, category, **flags)
        self.options = options
        self.general_feedback = preprocess_text(general_feedback, **flags)
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partial_feedback = preprocess_text(partial_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)

    def validate(self) -> list[str]:
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback")
        if not self.correct_feedback:
            errors.append("No feedback for correct answer")
        if not self.partial_feedback:
            errors.append("No feedback for partially correct answer")
        if not self.incorrect_feedback:
            errors.append("No feedback for incorrect answer")
        return errors


class MissingWordsQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_number: int | str) -> None:
        super().__init__(question_number, r"{(.*?)}", " ")

    def normalize_answers(self, response: str) -> dict[str, str]:
        answers: dict[str, str] = {}
        if not response:
            return answers
        response += self.separator
        for i, match in enumerate(re.finditer(self.answer_re, response, re.MULTILINE)):
            subquestion_answer = match.group(1)
            subquestion_text = str(i)
            subquestion_answer = self.normalize_response(subquestion_answer.strip())
            answers[subquestion_text] = subquestion_answer
        return answers
