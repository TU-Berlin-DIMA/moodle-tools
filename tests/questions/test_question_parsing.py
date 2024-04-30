import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from moodle_tools import ParsingError
from moodle_tools.make_questions import load_questions, main
from moodle_tools.questions import (
    ClozeQuestion,
    CoderunnerDQLQuestion,
    MissingWordsQuestion,
    MultipleChoiceQuestion,
    MultipleTrueFalseQuestion,
    NumericalQuestion,
    Question,
    TrueFalseQuestion,
)

# Dictionary with a correspondance between input file and tests references
# TODO: add example/yaml template for general coderunner, coderunner dql, and coderunner streaming
test_cases = {
    "true_false": ("true-false.yaml", TrueFalseQuestion),
    "multiple_choice": (
        "multiple-choice.yaml",
        MultipleChoiceQuestion,
    ),
    "numerical": ("numerical.yaml", NumericalQuestion),
    "multiple_true_false": ("multiple-true-false.yaml", MultipleTrueFalseQuestion),
    "missing_words": ("missing-words.yaml", MissingWordsQuestion),
    "cloze": ("cloze.yaml", ClozeQuestion),
    "sql_dql": ("coderunner-w_connection.yaml", CoderunnerDQLQuestion),
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
        input_yaml_with_no_question_type = dedent(
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

        input_yaml_with_no_title = dedent(
            """
        ---
        type: true_false
        question: "Some question"
        correct_answer: false
        """
        )

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
            yaml.safe_load_all(input_yaml_with_no_question_type),
            strict_validation=False,
            parse_markdown=False,
            add_table_border=False,
        )

        with pytest.raises(ParsingError) as e_no_type:
            next(questions)
        assert "is a required property" in str(e_no_type.value)

        # Test unsupported question
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_no_support),
            strict_validation=False,
            parse_markdown=False,
            add_table_border=False,
        )

        with pytest.raises(ParsingError) as e_no_support:
            next(questions)
        assert "'not_supported' is not one of" in str(e_no_support.value)

        # Test no title property provided
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_no_title),
            strict_validation=False,
            parse_markdown=False,
            add_table_border=False,
        )

        with pytest.raises(ParsingError) as e_no_type:
            next(questions)
        assert "is a required property" in str(e_no_type.value)

    @pytest.mark.parametrize("test_data", test_cases.values())
    def test_question_types(self, test_data: tuple[str, type[Question]]) -> None:
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

    def test_all_template_strict_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments all types in strict mode
        sys.argv = ["make-questions", "-i", "examples/yaml_templates.yaml"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="truefalse">' in captured.out
        assert '<question type="numerical">' in captured.out
        assert '<question type="mtf">' in captured.out
        assert '<question type="multichoice">' in captured.out
        assert '<question type="gapselect">' in captured.out
        assert '<question type="coderunner">' in captured.out
        assert '<question type="cloze">' in captured.out
        assert captured.err == ""
