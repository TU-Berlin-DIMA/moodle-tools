import pytest
import sys
from moodle_tools.make_questions import main


class TestTrueFalse:

    def test_yml_parsing(self,capsys):
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i","examples/true-false.yaml", "true_false"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert 'type="truefalse"' in captured.out
        assert '---' in captured.err