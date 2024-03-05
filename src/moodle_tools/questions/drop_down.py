import re

from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis


class DropDownQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_number):
        super().__init__(question_number, r"(.*?)\n -> (.*?)", ";")

    def normalize_question_text(self, question_text):
        question_text = question_text.replace("\n", " ")
        question_text = re.sub("{.*} -> {.*}", "", question_text, flags=re.DOTALL)
        return question_text
