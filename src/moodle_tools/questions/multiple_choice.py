from moodle_tools.questions.base import QuestionAnalysis


class MultipleChoiceQuestionAnalysis(QuestionAnalysis):
    def normalize_question(self, question_text: str) -> str:
        return question_text[: question_text.rindex(":")]
