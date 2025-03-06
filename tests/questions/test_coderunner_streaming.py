import sys
from pathlib import Path

import pytest

from moodle_tools.make_questions import main


class TestCoderunnerQuestionStreaming:
    def test_yml_parsing_non_strict(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/coderunner-streaming.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="coderunner">' in captured.out
        assert "<text>Sample Streaming Coderunner Question</text>" in captured.out
        assert captured.err == ""

    def test_correct_number_of_testcases(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/coderunner-streaming.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is expected
        assert str(captured.out).count("<testcode>") == 5
        assert captured.err == ""

    def test_correct_file_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/coderunner-streaming.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is expected
        assert """file name=\"data_stream.py\" path=\"/\" encoding=\"base64\"""" in captured.out
        assert """file name=\"synopsis.py\" path=\"/\" encoding=\"base64\"""" in captured.out
        assert """file name=\"autobahn.csv\" path=\"/\" encoding=\"base64\"""" in captured.out
        assert captured.err == ""

    def test_e2e_cli_make_question_stream(self, tmp_path: Path) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with (test_resources_dir / "coderunner-streaming.xml").open(encoding="utf-8") as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/coderunner-streaming.yaml",
            "-o",
            str(output_file_path),
            "-s",
        ]

        # Call the main function
        main()

        # Assert the output is as expected by loading the created xml file into a string object
        with output_file_path.open("r", encoding="utf-8") as f:
            generated_xml = f.read().strip()
        assert reference_xml == generated_xml
