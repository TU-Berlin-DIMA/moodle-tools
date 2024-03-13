import pytest
import sys
from moodle_tools.make_questions import main

class TestMarkdownMultipleChoiceQuestion:

    def test_yml_parsing(self,capsys):
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i","examples/markdown.yaml","-l", "-m", "multiple_choice"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert 'type="multichoice"' in captured.out
        assert captured.err == ''