import sys
from pathlib import Path

import pytest

from moodle_tools.make_questions import main


class TestMissingWords:
    def test_yml_parsing_strict(self, capsys):
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/missing-words.yaml", "missing_words"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="gapselect">' in captured.out
        assert "The following question did not pass strict validation:" in captured.err

    def test_yml_parsing_non_strict(self, capsys):
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/missing-words.yaml", "-l", "missing_words"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="gapselect">' in captured.out
        assert "<text>Simple missing words question</text>" in captured.out
        assert captured.err == ""

    def test_make_question(self, capsys, tmp_path):
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with open(test_resources_dir / "missing-wordsRef.xml", "r", encoding="utf-8") as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/missing-words.yaml",
            "-o",
            str(output_file_path),
            "-l",
            "missing_words",
        ]

        # Call the main function
        main()
        captured = capsys.readouterr()

        with open(output_file_path, "r", encoding="utf-8") as f:
            generated_xml = f.read().strip()

        # Assert the output is as expected
        assert reference_xml == generated_xml
