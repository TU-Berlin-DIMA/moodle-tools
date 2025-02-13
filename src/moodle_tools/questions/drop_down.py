import re

from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis


class DropDownQuestionAnalysis(MultipleResponseQuestionAnalysis):
    # TODO: Is this class actually necessary?

    def __init__(self, question_id: str) -> None:
        super().__init__(question_id, r"(.*?)\n -> (.*?)", ";")

    def normalize_question(self, question_text: str) -> str:
        question_text = question_text.replace("\n", " ")
        return re.sub("{.*} -> {.*}", "", question_text, flags=re.DOTALL)
