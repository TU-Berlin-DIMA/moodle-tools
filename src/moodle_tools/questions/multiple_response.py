import re

from moodle_tools.questions.base import BaseQuestionAnalysis


class MultipleResponseQuestionAnalysis(BaseQuestionAnalysis):
    def __init__(self, question_number, answer_re, separator):
        super().__init__(question_number)
        self.answer_re = answer_re + separator
        self.separator = separator

    def process_response(self, question_text, response, right_answer):
        question_text = self.normalize_question_text(question_text)
        responses = self.normalize_answers(response)
        right_answers = self.normalize_answers(right_answer)
        for subquestion_text, subquestion_right_answer in right_answers.items():
            subquestion = self.add_question(question_text, subquestion_text, subquestion_right_answer)
            if subquestion:
                self.add_response(subquestion, responses.get(subquestion_text, "-"))

    def normalize_answers(self, response):
        answers = {}
        if not response:
            return answers
        response += self.separator
        for match in re.finditer(self.answer_re, response, re.MULTILINE + re.DOTALL):
            subquestion_text, subquestion_answer = match.group(1), match.group(2)
            subquestion_text = self.normalize_subquestion_text(subquestion_text.strip())
            subquestion_answer = self.normalize_response(subquestion_answer.strip())
            answers[subquestion_text] = subquestion_answer
        return answers

    def normalize_question_text(self, question_text):
        return question_text

    def normalize_subquestion_text(self, subquestion_text):
        return subquestion_text
