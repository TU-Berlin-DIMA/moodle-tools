import re

from moodle_tools.questions.question import QuestionAnalysis


class MultipleResponseQuestionAnalysis(QuestionAnalysis):
    def __init__(self, question_id: str, answer_re: str, separator: str) -> None:
        super().__init__(question_id)
        self.answer_re = answer_re + separator
        self.separator = separator

    def process_response(self, question: str, response: str, correct_answer: str) -> None:
        question = self.normalize_question(question)
        responses = self.normalize_answers(response)
        correct_answers = self.normalize_answers(correct_answer)
        for subquestion_text, subquestion_right_answer in correct_answers.items():
            subquestion = self.add_question(question, subquestion_text, subquestion_right_answer)
            if subquestion:
                self.add_response(subquestion, responses.get(subquestion_text, "-"))

    def normalize_answers(self, response: str) -> dict[str, str]:
        answers: dict[str, str] = {}
        if not response:
            return answers
        response += self.separator
        for match in re.finditer(self.answer_re, response, re.MULTILINE + re.DOTALL):
            subquestion_text, subquestion_answer = match.group(1), match.group(2)
            subquestion_text = self.normalize_subquestion_text(subquestion_text.strip())
            subquestion_answer = self.normalize_response(subquestion_answer.strip())
            answers[subquestion_text] = subquestion_answer
        return answers

    def normalize_subquestion_text(self, subquestion_text: str) -> str:
        return subquestion_text
