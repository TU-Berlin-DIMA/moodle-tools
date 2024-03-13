import pytest
import sys
from moodle_tools.make_questions import main


class TestNumerical:

    def test_yml_parsing(self,capsys):
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i","examples/numerical.yml", "numerical"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert 'type="numerical"' in captured.out
        assert '---' in captured.err