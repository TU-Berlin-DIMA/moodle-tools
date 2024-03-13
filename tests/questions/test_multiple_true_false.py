import pytest
import sys
from moodle_tools.make_questions import main


class TestMultipleTrueFalse:

    def test_yml_parsing(self,capsys):
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i","examples/multiple-true-false.yaml", "multiple_true_false"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert 'type="mtf"' in captured.out
        assert '---' in captured.err