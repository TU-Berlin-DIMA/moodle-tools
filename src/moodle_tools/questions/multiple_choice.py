from moodle_tools.questions.base import BaseQuestionAnalysis


class MultipleChoiceQuestionAnalysis(BaseQuestionAnalysis):
    def normalize_question_text(self, question_text):
        return question_text[: question_text.rindex(":")]
