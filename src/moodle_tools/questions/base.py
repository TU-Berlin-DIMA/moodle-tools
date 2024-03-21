import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, NamedTuple

from moodle_tools.utils import preprocess_text


class Question(ABC):
    def __init__(self, question: str, title: str, **flags: bool) -> None:
        """General template for a question."""
        self.question = preprocess_text(question, **flags)
        self.title = title
        self.flags = flags

    @abstractmethod
    def validate(self) -> list[str]:
        """Function that validates the question. It returns a list of errors."""
        raise NotImplementedError

    @abstractmethod
    def generate_xml(self) -> str:
        """Generate a Moodle XML export of the question."""
        raise NotImplementedError


class AnalysisItem(NamedTuple):
    question_number: int
    variant_number: int
    question: str
    subquestion: str
    correct_response: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AnalysisItem):
            return NotImplemented
        return self.question == other.question and self.subquestion == other.subquestion

    def __hash__(self) -> int:
        return hash((self.question, self.subquestion))


class QuestionAnalysis:
    def __init__(self, question_number: int | str) -> None:
        if isinstance(question_number, str):
            question_number = int(question_number)
        self.question_number = question_number
        self.questions: dict[AnalysisItem, Counter[str]] = {}
        self.question_texts: list[str] = []

    def process_response(self, question: str, response: str, correct_answer: str) -> None:
        response = self.normalize_response(response)
        question = self.normalize_question(question)
        correct_answer = self.normalize_response(correct_answer)
        parsed_question = self.add_question(question, "", correct_answer)
        if parsed_question:
            self.add_response(parsed_question, response)

    def add_question(self, question: str, sub_question: str, correct_answer: str) -> AnalysisItem:
        if question not in self.question_texts:
            self.question_texts.append(question)
        parsed_question = AnalysisItem(
            self.question_number,
            len(self.question_texts),
            question,
            sub_question,
            correct_answer,
        )
        if parsed_question not in self.questions:
            self.questions[parsed_question] = Counter()
        return parsed_question

    def add_response(self, question: AnalysisItem, response: str) -> None:
        self.questions[question][response] += 1

    def normalize_response(self, response: str) -> str:
        return response

    def normalize_question(self, question_text: str) -> str:
        return question_text

    def grade(self, responses: Counter[str], correct_answer: str) -> dict[str, Any]:
        total = sum(responses.values())

        def correct_responses(responses: Counter[str], correct_answer: str) -> int:
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
