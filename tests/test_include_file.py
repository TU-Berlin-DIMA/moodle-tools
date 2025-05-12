import sys

import pytest

from moodle_tools.make_questions import main


class TestIncludeFile:
    def test_include_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/include_file.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="numerical">' in captured.out
        assert '<question type="cloze">' in captured.out
        assert "<text><![CDATA[<p>What is the value of π?</p>]]></text>" in captured.out
        assert (
            "<![CDATA[<p>The value of pi is {:NUMERICAL:%100%3.14:0.01#Some Feedback}.</p>]]>"
            in captured.out
        )
        assert "!include" not in captured.out
        assert "subquestion_pi.yaml" not in captured.out
        assert "question_pi.txt" not in captured.out
        assert captured.err == ""
