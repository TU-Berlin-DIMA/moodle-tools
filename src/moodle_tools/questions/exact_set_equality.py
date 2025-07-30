from moodle_tools.questions.diff_set_equality import DifferentiatedSetEquality
from moodle_tools.questions.stack_subquestions.exact_set_equality_sq import (
    ExactSetEqualitySubQuestion,
)


class ExactSetEquality(DifferentiatedSetEquality):
    """An Exact Set Equality question type for Moodle based on STACK.

    This question type checks if the expected set matches the received fully,
    giving no partial points.
    """

    def build_question_logic(self) -> ExactSetEqualitySubQuestion:
        return ExactSetEqualitySubQuestion(
            expected_set=self.expected_set,
            grade=self.grade,
        )
