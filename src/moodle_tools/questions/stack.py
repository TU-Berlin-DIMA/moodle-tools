import re
from typing import Any

import dacite
from dacite import Config

from moodle_tools.enums import ScoreMode, STACKMatchType
from moodle_tools.questions.question import Question
from moodle_tools.questions.stack_subquestions.dataclasses import PRT, Input
from moodle_tools.questions.stack_subquestions.diff_set_equality_sq import (
    DifferentiatedSetEqualitySubQuestion,
)
from moodle_tools.questions.stack_subquestions.exact_set_equality_sq import (
    ExactSetEqualitySubQuestion,
)
from moodle_tools.utils import preprocess_text

re_id = re.compile(r"""\[\[(\"?[^\"\]]*\"?)\]\]""")


class STACKQuestion(Question):
    """A class representing a STACK question in Moodle."""

    QUESTION_TYPE = "stack"
    XML_TEMPLATE = "stack.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        input_variables: list[str] | None = None,
        specific_feedback: str = "",
        question_note: str = "",
        question_simplify: bool = True,
        assume_positive: bool = False,
        assume_real: bool = False,
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        decimal_separator: str = ".",
        scientific_notation: str = "*10",
        multiplication_sign: str = "dot",
        square_root_sign: str = "1",
        complex_number_variable: str = "i",
        inverse_trigonometry: str = "cos-1",
        logic_symbol: str = "lang",
        matrix_parentheses: str = "[",
        variants_selection_seed: str = "",
        inputs: dict[str, dict[str, Any]] | None = None,
        response_trees: dict[str, dict[str, Any]] | None = None,
        subquestions: dict[str, dict[str, Any]] | None = None,
        **flags: bool,
    ) -> None:
        """Initialize a new STACK question.

        Args:
            question: The question text.
            title: The title of the question.
            category: The category of the question.
            grade: The grade for the question.
            general_feedback: General feedback for the question.
            input_variables: List of maxime-specific input variables used in the question.
                             This has to include the expected answer variable (tans)
            specific_feedback: feedback deduced from the partial response tree (PRT).
            question_note: Note to be displayed with the question (STACK-Specific).
            question_simplify: Whether to simplify the question (STACK-Specific).
            assume_positive: Whether to assume positive values (STACK-Specific).
            assume_real: Whether to assume real values (STACK-Specific).
            correct_feedback: Feedback for correct answers.
            partial_feedback: Feedback for partially correct answers.
            incorrect_feedback: Feedback for incorrect answers.
            decimal_separator: The decimal separator used in the question (STACK-Specific).
            scientific_notation: The scientific notation used in the question (STACK-Specific).
            multiplication_sign: The multiplication sign used in the question (STACK-Specific).
            square_root_sign: The square root sign used in the question (STACK-Specific).
            complex_number_variable: The variable used for complex numbers (STACK-Specific).
            inverse_trigonometry: The notation for inverse trigonometric functions
                                  (STACK-Specific).
            logic_symbol: The logic symbol used in the question (STACK-Specific).
            matrix_parentheses: The parentheses used for matrices (STACK-Specific).
            variants_selection_seed: Seed for variants selection (STACK-Specific).
            inputs: Input Variables in the Qeustion.
            response_trees: partial response trees. Moodle tends to allow only one of those (prt1).
            subquestions: Subquestions that are used in the question.
            flags: Additional flags for the question.
        """
        super().__init__(question, title, category, grade, general_feedback, **flags)
        self.input_variables = input_variables or []
        self.specific_feedback = preprocess_text(specific_feedback, **flags)
        self.question_note = preprocess_text(question_note, **flags)
        self.question_simplify = question_simplify
        self.assume_positive = assume_positive
        self.assume_real = assume_real
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partial_feedback = preprocess_text(partial_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)
        self.decimal_separator = decimal_separator
        self.scientific_notation = scientific_notation
        self.multiplication_sign = multiplication_sign
        self.square_root_sign = square_root_sign
        self.complex_number_variable = complex_number_variable
        self.inverse_trigonometry = inverse_trigonometry
        self.logic_symbol = logic_symbol
        self.matrix_parentheses = matrix_parentheses
        self.variants_selection_seed = variants_selection_seed
        self.inputs = {
            k: dacite.from_dict(data_class=Input, data=v) for k, v in (inputs or {}).items()
        }
        self.response_trees = {
            k: dacite.from_dict(
                data_class=PRT,
                data=v,
                config=Config(
                    type_hooks={
                        ScoreMode: ScoreMode.from_str,
                        STACKMatchType: STACKMatchType.from_str,
                    }
                ),
            )
            for k, v in (response_trees or {}).items()
        }
        self.subquestions = subquestions or {}

        self.fill_input_placeholder()

    def fill_input_placeholder(self) -> None:
        input_matches = list(re_id.finditer(self.question))
        inputs = {match.group(1): match.group(0) for match in input_matches}

        if len(inputs) != len(input_matches):
            raise ValueError("Duplicate input variables found in the question text.")

        for key, i in inputs.items():
            clean_key = key.strip('"')

            if clean_key in self.subquestions:
                curr_sq = self.subquestions[clean_key]

                match curr_sq["type"]:
                    case "diff_set_equality":
                        del curr_sq["type"]

                        curr_sq.update()

                        subquestion = DifferentiatedSetEqualitySubQuestion(
                            expected_set=curr_sq.get("expected_set", []),
                            additional_sets_until_wrong=curr_sq.get(
                                "additional_sets_until_wrong", 0
                            ),
                            grade=curr_sq.get("grade", 1.0),
                            subset_prefix="dse",
                            expected_answer_var="dseexpected",
                            received_answer_var="dsereceived",
                            prt_name="prtdse",
                        )

                    case "exact_set_equality":
                        del curr_sq["type"]

                        subquestion = ExactSetEqualitySubQuestion(
                            expected_set=curr_sq.get("expected_set", []),
                            grade=curr_sq.get("grade", 1.0),
                            subset_prefix="ese",
                            expected_answer_var="ese_expected",
                            received_answer_var="ese_received",
                            prt_name="ese_prt",
                        )

                    case _:
                        raise ValueError(f"Unknown subquestion type: {curr_sq['type']}")

                self.inputs.update(subquestion.inputs)
                self.response_trees.update(subquestion.response_trees)
                self.input_variables.extend(subquestion.input_variables)
                self.specific_feedback += "\n" + subquestion.specific_feedback
                self.question = re.sub(
                    re.escape(i),
                    f"[[input:{subquestion.received_answer_var}]] "
                    f"[[validation:{subquestion.received_answer_var}]]",
                    self.question,
                )
            else:
                strip_key = key.strip('"')
                if strip_key in self.inputs:
                    self.question = re.sub(
                        re.escape(i),
                        f"[[input:{strip_key}]] [[validation:{strip_key}]]",
                        self.question,
                    )

    def validate(self) -> list[str]:
        """Validate the STACK question.

        Returns:
            list[str]: A list of validation errors.
        """
        errors = super().validate()
        if not self.input_variables:
            errors.append("No input variables specified.")
        if not self.response_trees:
            errors.append("No response trees specified.")
        if not self.inputs:
            errors.append("No inputs specified.")
        if not self.correct_feedback:
            errors.append("No feedback for correct answer provided.")
        if not self.partial_feedback:
            errors.append("No feedback for partially correct answer provided.")
        if not self.incorrect_feedback:
            errors.append("No feedback for incorrect answer provided.")
        return errors
