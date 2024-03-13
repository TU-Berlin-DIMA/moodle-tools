import pytest
import sys
from moodle_tools.make_questions import main

class TestArguments:
    def test_argument_parsing_help(self, capsys):
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-h"]

        # Call the main function
        with pytest.raises(SystemExit) as e:
            main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert 'usage: make-questions [-h] [-i INPUT] [-o OUTPUT] [-t TITLE] [-l] [-m]' in captured.out