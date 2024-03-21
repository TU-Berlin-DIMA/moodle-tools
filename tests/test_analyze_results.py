import sys

import pytest

from moodle_tools.analyze_results import main


class TestAnalyzeResultsArguments:
    def test_argument_parsing_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["analyze-results", "-h"]

        expected_output = """
        usage: analyze-results [-h] [-i INPUT] [-o OUTPUT] [--n [N ...]]
        """.strip()

        # Call the main function
        with pytest.raises(SystemExit) as e:
            main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert expected_output in captured.out
        assert str(e.value) == "0"
