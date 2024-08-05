import re

from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text


class MissingWordsQuestion(Question):

    QUESTION_TYPE = "gapselect"
    XML_TEMPLATE = "missing_words.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        options: list[dict[str, str]],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        shuffle_answers: bool = True,
        **flags: bool,
    ):
        super().__init__(question, title, category, grade, general_feedback, **flags)
        self.options = options
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partial_feedback = preprocess_text(partial_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)
        self.shuffle_answers = shuffle_answers

    def validate(self) -> list[str]:
        errors = super().validate()
        if not self.correct_feedback:
            errors.append("No feedback for correct answer provided.")
        if not self.partial_feedback:
            errors.append("No feedback for partially correct answer provided.")
        if not self.incorrect_feedback:
            errors.append("No feedback for incorrect answer provided.")
        return errors


class MissingWordsQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_id: str) -> None:
        super().__init__(question_id, r"{(.*?)}", " ")

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
