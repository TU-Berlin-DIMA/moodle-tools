import re

from moodle_tools.questions.stack import STACKQuestion
from moodle_tools.questions.stack_subquestions.diff_set_equality_sq import (
    DifferentiatedSetEqualitySubQuestion,
)


class DifferentiatedSetEquality(STACKQuestion):
    """A Differentiated Set Equivalence question type for Moodle based on STACK.

    This question type checks if the expected set matches the received set fully,
    giving partial points if not.
    """

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        expected_set: list[str] | None = None,
        additional_sets_until_wrong: int = 0,
        variants_selection_seed: str = "",
        **flags: bool,
    ) -> None:
        if expected_set is None:
            raise ValueError("Expected set must be provided.")

        super().__init__(
            question=question,
            title=title,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            correct_feedback=correct_feedback,
            partial_feedback=partial_feedback,
            incorrect_feedback=incorrect_feedback,
            variants_selection_seed=variants_selection_seed,
            **flags,  # type: ignore
        )

        self.expected_set = expected_set
        self.additional_sets_until_wrong = additional_sets_until_wrong
        self.question_logic = self.build_question_logic()

        self.input_variables.extend(self.question_logic.input_variables)
        self.inputs.update(self.question_logic.inputs)
        self.response_trees.update(self.question_logic.response_trees)

        self.question_note = self.question_logic.question_note
        self.specific_feedback = self.question_logic.specific_feedback

        self.inline_answer_box(self.question_logic.received_answer_var)

    def build_question_logic(self) -> DifferentiatedSetEqualitySubQuestion:
        return DifferentiatedSetEqualitySubQuestion(
            expected_set=self.expected_set or [],
            additional_sets_until_wrong=self.additional_sets_until_wrong,
            grade=self.grade,
        )

    def inline_answer_box(self, received_answer_name: str) -> None:
        re_box = re.compile(r"\[\[ANSWERBOX\]\]")
        answerbox = re.search(re_box, self.question)

        if answerbox:
            self.question = re.sub(
                re_box,
                f"[[input:{received_answer_name}]] [[validation:{received_answer_name}]]",
                self.question,
            )
        else:
            self.question += (
                f"\n[[input:{received_answer_name}]] [[validation:{received_answer_name}]]"
            )
