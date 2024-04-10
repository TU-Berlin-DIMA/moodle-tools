import sys

import pytest

from moodle_tools.make_questions import main


class TestMakeQuestionArguments:
    def test_argument_parsing_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-h"]

        expected_output = """
        usage: make-questions [-h] [-i INPUT] [-o OUTPUT] [-s] [-q]
        """.strip()

        # Call the main function
        with pytest.raises(SystemExit) as e:
            main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert expected_output in captured.out
        assert str(e.value) == "0"
