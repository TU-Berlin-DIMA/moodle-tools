from typing import Any
from xml.etree.ElementTree import Element

from moodle_tools.questions.cloze import ClozeQuestion
from moodle_tools.questions.coderunner_sql import CoderunnerDDLQuestion, CoderunnerDQLQuestion
from moodle_tools.questions.coderunner_streaming import CoderunnerStreamingQuestion
from moodle_tools.questions.description import Description
from moodle_tools.questions.missing_words import MissingWordsQuestion
from moodle_tools.questions.multiple_choice import MultipleChoiceQuestion
from moodle_tools.questions.multiple_true_false import MultipleTrueFalseQuestion
from moodle_tools.questions.numerical import NumericalQuestion
from moodle_tools.questions.question import Question
from moodle_tools.questions.shortanswer import ShortAnswerQuestion
from moodle_tools.questions.true_false import TrueFalseQuestion
from moodle_tools.utils import ParsingError


class QuestionFactory:
    SUPPORTED_QUESTION_TYPES: dict[str, type[Question]] = {
        "true_false": TrueFalseQuestion,
        "multiple_true_false": MultipleTrueFalseQuestion,
        "multiple_choice": MultipleChoiceQuestion,
        "cloze": ClozeQuestion,
        "numerical": NumericalQuestion,
        "missing_words": MissingWordsQuestion,
        "sql_ddl": CoderunnerDDLQuestion,
        "sql_dql": CoderunnerDQLQuestion,
        "isda_streaming": CoderunnerStreamingQuestion,
        "description": Description,
        "shortanswer": ShortAnswerQuestion,
    }

    @staticmethod
    def create_question(question_type: str, **properties: Any) -> Question:
        if question_type in QuestionFactory.SUPPORTED_QUESTION_TYPES:
            return QuestionFactory.SUPPORTED_QUESTION_TYPES[question_type](**properties)
        raise ParsingError(f"Unsupported Question Type: {question_type}.")

    @staticmethod
    def is_valid_type(question_type: str) -> bool:
        return question_type in QuestionFactory.SUPPORTED_QUESTION_TYPES

    @staticmethod
    def create_from_xml(question_type: str, element: Element, **properties: Any):
        if question_type in QuestionFactory.SUPPORTED_QUESTION_TYPES:
            properties = properties | QuestionFactory.SUPPORTED_QUESTION_TYPES[
                question_type
            ].extract_properties_from_xml(element)
            return QuestionFactory.SUPPORTED_QUESTION_TYPES[question_type](**properties)
        raise ParsingError(f"Unsupported Question Type: {question_type}.")
