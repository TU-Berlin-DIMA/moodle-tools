import contextlib
import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from moodle_tools import ParsingError
from moodle_tools.make_questions import load_questions, main
from moodle_tools.questions.cloze import ClozeQuestion
from moodle_tools.questions.coderunner_sql import CoderunnerDDLQuestion, CoderunnerDQLQuestion
from moodle_tools.questions.coderunner_streaming import CoderunnerStreamingQuestion
from moodle_tools.questions.missing_words import MissingWordsQuestion
from moodle_tools.questions.multiple_choice import MultipleChoiceQuestion
from moodle_tools.questions.multiple_true_false import MultipleTrueFalseQuestion
from moodle_tools.questions.numerical import NumericalQuestion
from moodle_tools.questions.question import Question
from moodle_tools.questions.true_false import TrueFalseQuestion

# Dictionary with a correspondance between input file and tests references
test_cases = {
    "true_false": ("true-false.yaml", TrueFalseQuestion),
    "multiple_choice": ("multiple-choice.yaml", MultipleChoiceQuestion),
    "numerical": ("numerical.yaml", NumericalQuestion),
    "multiple_true_false": ("multiple-true-false.yaml", MultipleTrueFalseQuestion),
    "missing_words": ("missing-words.yaml", MissingWordsQuestion),
    "cloze": ("cloze.yaml", ClozeQuestion),
    "sql_dql": ("coderunner-dql-wo_connection.yaml", CoderunnerDQLQuestion),
    "sql_ddl": ("coderunner-ddl.yaml", CoderunnerDDLQuestion),
    "isda_streaming": ("coderunner-streaming.yaml", CoderunnerStreamingQuestion),
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
        type: not_supported
        question: "Some question"
        correct_answer: false
        """
        )

        # Test supported question
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_property),
            strict_validation=False,
            parse_markdown=False,
            table_styling=False,
        )
        question_with_type = next(questions)
        assert isinstance(question_with_type, TrueFalseQuestion)

        # Test no type property provided
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_no_question_type),
            strict_validation=False,
            parse_markdown=False,
            table_styling=False,
        )

        with pytest.raises(ParsingError) as e_no_type:
            next(questions)
        assert "Question type not provided:" in str(e_no_type.value)

        # Test unsupported question
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_no_support),
            strict_validation=False,
            parse_markdown=False,
            table_styling=False,
        )

        with pytest.raises(ParsingError) as e_no_support:
            next(questions)
        assert str(e_no_support.value) == "Unsupported Question Type: not_supported."

        # Test no title property provided
        questions = load_questions(
            yaml.safe_load_all(input_yaml_with_no_title),
            strict_validation=False,
            parse_markdown=False,
            table_styling=False,
        )

        with pytest.raises(ParsingError) as e_no_type:
            next(questions)
        assert "Question title not provided" in str(e_no_type.value)

    @pytest.mark.parametrize("test_data", test_cases.values())
    def test_question_types(self, test_data: tuple[str, type[Question]]) -> None:
        # Change to the directory containing the test resources
        with contextlib.chdir(Path(__file__).parent / "../../examples"):
            # Load content from the file
            with Path(test_data[0]).open(encoding="utf-8") as f:
                reference_yaml = f.read().strip()

            questions = load_questions(
                yaml.safe_load_all(reference_yaml),
                strict_validation=False,
                parse_markdown=False,
                table_styling=False,
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
