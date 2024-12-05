from typing import Any
from xml.etree.ElementTree import Element

from moodle_tools.enums import ShuffleAnswersEnum
from moodle_tools.questions.question import Question
from moodle_tools.utils import parse_html, preprocess_text


class MatchingQuestion(Question):
    """General template for a Matching question."""

    QUESTION_TYPE = "matching"
    XML_TEMPLATE = "matching.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        options: list[dict[str, str]],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        shuffle_answers: ShuffleAnswersEnum = ShuffleAnswersEnum.SHUFFLE,
        **flags: bool,
    ):
        super().__init__(question, title, category, grade, general_feedback, **flags)

        self.options = options
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partial_feedback = preprocess_text(partial_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)
        self.shuffle_answers = ShuffleAnswersEnum.from_str(shuffle_answers)

        self.parse_questions()
        self.sort_answers()

    def parse_questions(self):
        for option in self.options:
            if "question" in option:
                option["question"] = preprocess_text(option["question"], **self.flags)

    def sort_answers(self):
        if self.shuffle_answers == ShuffleAnswersEnum.LEXICOGRAPHICAL:
            self.options.sort(key=lambda x: x["answer"])

    @staticmethod
    def extract_properties_from_xml(element: Element) -> dict[str, str | Any | None]:
        question_props = Question.extract_properties_from_xml(element)

        question_props.update(
            {
                "shuffle_answers": (
                    ShuffleAnswersEnum.SHUFFLE
                    if element.find("shuffleanswers").text.lower() == "true"
                    else ShuffleAnswersEnum.IN_ORDER
                )
            }
        )

        subquestions = []
        for sq in element.findall("subquestion"):
            sq_el = {
                "answer": sq.find("answer").find("text").text,
            }

            question = sq.find("text").text

            if question is not None:
                sq_el.update({"question": parse_html(sq.find("text").text)})

            subquestions.append(sq_el)

        question_props.update({"options": subquestions})

        return question_props

    def validate(self) -> list[str]:
        pass
