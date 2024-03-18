import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from moodle_tools.make_questions import main
from moodle_tools.questions import TrueFalseQuestion, converter
from moodle_tools.questions.factory import QuestionFactory


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

        question = converter.load_questions(
            QuestionFactory,
            False,
            yaml.safe_load_all(input_yaml_with_property),
            markdown=False,
            table_border=False,
            title="Knowledge question",
        )
        question_with_type = next(question)

        question = converter.load_questions(
            QuestionFactory,
            False,
            yaml.safe_load_all(input_yaml_with_no_property),
            markdown=False,
            table_border=False,
            title="Knowledge question",
        )
        question_with_no_type = next(question)

        # Assert the output is as expected
        assert isinstance(question_with_type, TrueFalseQuestion)
        assert question_with_no_type == "Question type not supported."
