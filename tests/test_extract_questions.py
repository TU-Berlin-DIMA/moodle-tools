import sys

import pytest

from moodle_tools.extract_questions import main


class TestExtractQuestionArguments:
    def test_argument_parsing_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["extract-questions", "-h"]

        expected_output = """
        usage: extract-questions [-h] -i INPUT [INPUT ...] [-o OUTPUT]
        """.strip()

        # Call the main function
        with pytest.raises(SystemExit) as e:
            main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert expected_output in captured.out
        assert str(e.value) == "0"
