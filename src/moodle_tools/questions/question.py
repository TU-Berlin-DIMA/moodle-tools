import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any, NamedTuple

from jinja2 import Environment

from moodle_tools.utils import preprocess_text


class Question(ABC):
    """General template for a question."""

    QUESTION_TYPE: str
    XML_TEMPLATE: str

    def __init__(
        self,
        question: str,
        title: str,
        category: str | None,
        grade: float = 1.0,
        general_feedback: str = "",
        **flags: bool,
    ) -> None:
        """General template for a question."""
        self.question = preprocess_text(question, **flags)
        self.title = title
        self.category = category
        self.grade = grade
        self.general_feedback = preprocess_text(general_feedback, **flags)
        self.flags = flags

    @abstractmethod
    def validate(self) -> list[str]:
        """Validate the question.

        Returns:
            list[str]: A list of validation errors.
        """
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback provided.")

        return errors

    def to_xml(self, env: Environment) -> str:
        """Generate a Moodle XML export of the question."""
        template = env.get_template(self.XML_TEMPLATE)
        return template.render(self.__dict__ | {"type": self.QUESTION_TYPE})


class AnalysisItem(NamedTuple):
    question_id: str
    variant_number: int
    question: str
    subquestion: str
    correct_answer: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AnalysisItem):
            return NotImplemented
        return self.question == other.question and self.subquestion == other.subquestion

    def __hash__(self) -> int:
        return hash((self.question, self.subquestion))


class QuestionAnalysis:
    def __init__(self, question_id: str) -> None:
        self.question_id = question_id
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
            self.question_id,
            self.question_texts.index(question) + 1,
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
            # TODO: This method should consider numerical euqivalance plus a tolerance for
            # numerical questions (and cloze)
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
