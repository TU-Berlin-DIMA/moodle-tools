import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from moodle_tools.make_questions import main
from moodle_tools.questions import (
    ClozeQuestion,
    MissingWordsQuestion,
    MultipleTrueFalseQuestion,
    NumericalQuestion,
    SingleSelectionMultipleChoiceQuestion,
    TrueFalseQuestion,
    converter,
)
from moodle_tools.questions.factory import QuestionFactory

# Dictionary with a correspondance between input file and tests references
test_cases = {
    "true_false": ("true-false.yaml", TrueFalseQuestion),
    "multiple_choice": ("single-selection-multiple-choice.yaml", SingleSelectionMultipleChoiceQuestion),
    "numerical": ("numerical.yaml", NumericalQuestion),
    "multiple_true_false": ("multiple-true-false.yaml", MultipleTrueFalseQuestion),
    "missing_words": ("missing-words.yaml", MissingWordsQuestion),
    "cloze": ("cloze.yaml", ClozeQuestion),
}


class TestGeneralQuestion:
    def test_question_type_property(self):

        # Input from a true_false question type
        input_yaml_with_property = dedent(
            """
        ---
        type: true_false
        statement: "Minimal false question"
        correct_answer: false
        """
        )

        input_yaml_with_no_property = dedent(
            """
        ---
        statement: "Minimal false question"
        correct_answer: false
        """
        )

        input_yaml_with_no_support = dedent(
            """
        ---
        type: not_supported
        statement: "Minimal false question"
        correct_answer: false
        """
        )

        # Test supported question
        question = converter.load_questions(
            False,
            yaml.safe_load_all(input_yaml_with_property),
            markdown=False,
            table_border=False,
            title="Knowledge question",
        )
        question_with_type = next(question)
        assert isinstance(question_with_type, TrueFalseQuestion)

        # Test no type property provided
        question = converter.load_questions(
            False,
            yaml.safe_load_all(input_yaml_with_no_property),
            markdown=False,
            table_border=False,
            title="Knowledge question",
        )

        with pytest.raises(ValueError) as e_no_type:
            next(question)
        assert str(e_no_type.value) == "Question type not provided."

        # Test unsupported question
        question = converter.load_questions(
            False,
            yaml.safe_load_all(input_yaml_with_no_support),
            markdown=False,
            table_border=False,
            title="Knowledge question",
        )

        with pytest.raises(ValueError) as e_no_support:
            next(question)
        assert str(e_no_support.value) == "Unsupported Question Type: not_supported."

    @pytest.mark.parametrize("question_type, test_data", test_cases.items())
    def test_question_types(self, question_type, test_data):
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../../examples"

        # Load content from the file
        with open(test_resources_dir / test_data[0], "r", encoding="utf-8") as f:
            reference_yaml = f.read().strip()

        question = converter.load_questions(
            False,
            yaml.safe_load_all(reference_yaml),
            markdown=False,
            table_border=False,
            title="Knowledge question",
        )
        question_to_test = next(question)
        assert isinstance(question_to_test, test_data[1])
