from abc import ABC, abstractmethod
from collections import Counter, namedtuple


class BaseQuestion(ABC):
    def __init__(self, title, **flags):
        # Set the title and pass flags
        self.title = title
        self.flags = flags

    @abstractmethod
    def validate(self):
        pass

    @abstractmethod
    def generate_xml(self):
        pass


class QuestionAnalysis(
    namedtuple(
        "Question",
        [
            "question_number",
            "variant_number",
            "question",
            "subquestion",
            "correct_response",
        ],
    )
):
    def __eq__(self, other):
        return self.question == other.question and self.subquestion == other.subquestion

    def __hash__(self):
        return hash((self.question, self.subquestion))


class BaseQuestionAnalysis:
    def __init__(self, question_number):
        self.question_number = question_number
        self.questions = {}
        self.question_texts = []

    def process_response(self, question_text, response, right_answer):
        response = self.normalize_response(response)
        question_text = self.normalize_question_text(question_text)
        right_answer = self.normalize_response(right_answer)
        question = self.add_question(question_text, "", right_answer)
        if question:
            self.add_response(question, response)

    def add_question(self, question_text, sub_question_text, right_answer):
        if question_text not in self.question_texts:
            self.question_texts.append(question_text)
        question = QuestionAnalysis(
            self.question_number,
            len(self.question_texts),
            question_text,
            sub_question_text,
            right_answer,
        )
        if question not in self.questions:
            self.questions[question] = Counter()
        return question

    def add_response(self, question, response):
        self.questions[question][response] += 1

    def normalize_response(self, response):
        return response

    def normalize_question_text(self, question_text):
        return question_text

    def grade(self, responses, correct_answer):
        total = sum(responses.values())

        def correct_responses(responses, correct_answer):
            grade = responses[correct_answer]
            if re.match(r"^([0-9]*)?\.[0-9]+$", correct_answer):
                grade += responses[correct_answer.replace(".", ",")]
            elif re.match(r"^([0-9]*)?,[0-9]+$", correct_answer):
                grade += responses[correct_answer.replace(",", ".")]
            return grade

        return {
            "grade": correct_responses(responses, correct_answer) / total * 100,
            "occurrence": total,
            "responses": dict(responses),
        }
