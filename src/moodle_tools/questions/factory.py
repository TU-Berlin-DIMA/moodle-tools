from typing import Any

from .. import ParsingError
from .base import Question
from .cloze import ClozeQuestion
from .coderunner_sql import CoderunnerQuestionSQL
from .missing_words import MissingWordsQuestion
from .multiple_true_false import MultipleTrueFalseQuestion
from .numerical import NumericalQuestion
from .single_selection_multiple_choice import SingleSelectionMultipleChoiceQuestion
from .true_false import TrueFalseQuestion


class QuestionFactory:
    SUPPORTED_QUESTION_TYPES: dict[str, type[Question]] = {
        "true_false": TrueFalseQuestion,
        "multiple_true_false": MultipleTrueFalseQuestion,
        "multiple_choice": SingleSelectionMultipleChoiceQuestion,
        "cloze": ClozeQuestion,
        "numerical": NumericalQuestion,
        "missing_words": MissingWordsQuestion,
        "coderunner": CoderunnerQuestionSQL,
    }

    @staticmethod
    def create_question(question_type: str, **properties: Any) -> Question:
        if question_type in QuestionFactory.SUPPORTED_QUESTION_TYPES:
            return QuestionFactory.SUPPORTED_QUESTION_TYPES[question_type](**properties)
        raise ParsingError(f"Unsupported Question Type: {question_type}.")

    @staticmethod
    def is_valid_type(question_type: str) -> bool:
        return question_type in QuestionFactory.SUPPORTED_QUESTION_TYPES
