from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from moodle_tools import ParsingError
from moodle_tools.make_questions import load_questions
from moodle_tools.questions import (
    ClozeQuestion,
    MissingWordsQuestion,
    MultipleTrueFalseQuestion,
    NumericalQuestion,
    Question,
    SingleSelectionMultipleChoiceQuestion,
    TrueFalseQuestion,
)

# Dictionary with a correspondance between input file and tests references
test_cases = {
    "true_false": ("true-false.yaml", TrueFalseQuestion),
    "multiple_choice": (
        "single-selection-multiple-choice.yaml",
        SingleSelectionMultipleChoiceQuestion,
    ),
    "numerical": ("numerical.yaml", NumericalQuestion),
    "multiple_true_false": ("multiple-true-false.yaml", MultipleTrueFalseQuestion),
    "missing_words": ("missing-words.yaml", MissingWordsQuestion),
    "cloze": ("cloze.yaml", ClozeQuestion),
}


class TestGeneralQuestion:
    def test_question_type_property(self) -> None:

        # Input from a true_false question type
        input_yaml_with_property = dedent(
            """
        ---
        type: true_false
        title: "Minimal false question"
        question: "Some question"
        correct_answer: false
        """
        )

        # TODO: rename to input_yaml_with_no_type
        input_yaml_with_no_property = dedent(
            """
        ---
        title: "Minimal false question"
        question: "Some question"
        correct_answer: false
        """
        )

        input_yaml_with_no_support = dedent(
            """
        ---
        type: not_supported
        title: "Minimal false question"
        question: "Some question"
        correct_answer: false
        """
        )

        # TODO: Test absence of title

        # Test supported question
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_property),
            strict_validation=False,
            parse_markdown=False,
            add_table_border=False,
        )
        question_with_type = next(questions)
        assert isinstance(question_with_type, TrueFalseQuestion)

        # Test no type property provided
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_no_property),
            strict_validation=False,
            parse_markdown=False,
            add_table_border=False,
        )

        with pytest.raises(ParsingError) as e_no_type:
            next(questions)
        assert "Question type not provided:" in str(e_no_type.value)

        # Test unsupported question
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_no_support),
            strict_validation=False,
            parse_markdown=False,
            add_table_border=False,
        )

        with pytest.raises(ParsingError) as e_no_support:
            next(questions)
        assert str(e_no_support.value) == "Unsupported Question Type: not_supported."

    @pytest.mark.parametrize("question_type, test_data", test_cases.items())
    def test_question_types(
        self, question_type: str, test_data: tuple[str, type[Question]]
    ) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../../examples"

        # Load content from the file
        with open(test_resources_dir / test_data[0], "r", encoding="utf-8") as f:
            reference_yaml = f.read().strip()

        questions = load_questions(
            yaml.safe_load_all(reference_yaml),
            strict_validation=False,
            parse_markdown=False,
            add_table_border=False,
        )
        question_to_test = next(questions)
        assert isinstance(question_to_test, test_data[1])
