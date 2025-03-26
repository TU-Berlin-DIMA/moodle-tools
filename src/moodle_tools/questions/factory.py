from typing import Any

from moodle_tools.utils import ParsingError

from .cloze import ClozeQuestion
from .description import Description
from .matching import MatchingQuestion
from .missing_words import MissingWordsQuestion
from .multiple_choice import MultipleChoiceQuestion
from .multiple_true_false import MultipleTrueFalseQuestion
from .numerical import NumericalQuestion
from .question import Question
from .shortanswer import ShortAnswerQuestion
from .true_false import TrueFalseQuestion

SUPPORTED_QUESTION_TYPES: dict[str, type[Question]] = {
    "true_false": TrueFalseQuestion,
    "multiple_true_false": MultipleTrueFalseQuestion,
    "multiple_choice": MultipleChoiceQuestion,
    "cloze": ClozeQuestion,
    "numerical": NumericalQuestion,
    "missing_words": MissingWordsQuestion,
    "description": Description,
    "shortanswer": ShortAnswerQuestion,
    "matching": MatchingQuestion,
}

try:
    from .coderunner_sql import CoderunnerDDLQuestion, CoderunnerDQLQuestion
    from .coderunner_streaming import CoderunnerStreamingQuestion

    SUPPORTED_QUESTION_TYPES.update(
        {
            "sql_ddl": CoderunnerDDLQuestion,
            "sql_dql": CoderunnerDQLQuestion,
            "isda_streaming": CoderunnerStreamingQuestion,
        }
    )
except ImportError:
    pass


def create_question(question_type: str, **properties: Any) -> Question:  # noqa: ANN401
    if question_type in SUPPORTED_QUESTION_TYPES:
        return SUPPORTED_QUESTION_TYPES[question_type](**properties)
    raise ParsingError(f"Unsupported Question Type: {question_type}.")
