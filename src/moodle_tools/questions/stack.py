import re
from dataclasses import dataclass, field
from typing import Any

import dacite
from dacite import Config

from moodle_tools.enums import ScoreMode, STACKMatchType
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text


@dataclass
class PRTNodeBranch:
    score_mode: ScoreMode
    score: float
    penalty: str = ""
    answer_note: str = ""
    feedback: str = ""
    next_node: int = -1


@dataclass
class PRTNode:
    test_type: str
    received_answer: str
    expected_answer: str
    true_branch: PRTNodeBranch
    false_branch: PRTNodeBranch
    description: str = ""
    test_options: str = ""
    quiet: bool = True


@dataclass
class PRT:
    max_points: float
    nodes: dict[int, PRTNode]
    auto_simplify: bool = True
    feedback_style: int = 1
    feedback_variables: list[str] = field(default_factory=list)


@dataclass
class Input:
    type: str
    matching_answer_variable: str
    width: int
    strict_syntax: bool = True
    insert_stars: bool = False
    syntax_hint: str = ""
    syntax_attribute: bool = False
    forbidden_words: list[str] = field(default_factory=list)
    allowed_words: list[str] = field(default_factory=list)
    forbid_floats: bool = True
    require_lowest_terms: bool = False
    check_answer_type: bool = False
    must_verify: bool = True
    show_validation: int = 2
    options: list[str] = field(default_factory=list)


re_id = re.compile(r"""\[\[\"([^\"]*)\"\]\]""")


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
            flags: Additional flags for the question.
        """
        super().__init__(question, title, category, grade, general_feedback, **flags)
        self.input_variables = input_variables or []
        self.specific_feedback = preprocess_text(specific_feedback)
        self.question_note = preprocess_text(question_note)
        self.question_simplify = question_simplify
        self.assume_positive = assume_positive
        self.assume_real = assume_real
        self.correct_feedback = preprocess_text(correct_feedback)
        self.partial_feedback = preprocess_text(partial_feedback)
        self.incorrect_feedback = preprocess_text(incorrect_feedback)
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
                data_class=PRT, data=v, config=Config(cast=[ScoreMode, STACKMatchType])
            )
            for k, v in (response_trees or {}).items()
        }

        self.replace_input_placeholder()

    def replace_input_placeholder(self) -> None:
        input_matches = list(re_id.finditer(self.question))
        inputs = {match.group(1): match.group(0) for match in input_matches}

        if len(inputs) != len(input_matches):
            raise ValueError("Duplicate input variables found in the question text.")

        for i in inputs.items():
            self.question = self.question.replace(i[1], f"[[input:{i[0]}]] [[validation:{i[0]}]]")

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
