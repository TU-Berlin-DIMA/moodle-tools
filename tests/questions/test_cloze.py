import sys
from pathlib import Path

import pytest

from moodle_tools.make_questions import main


class TestCloze:
    def test_yml_parsing_strict(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/cloze.yaml"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert "The following question did not pass strict validation" in captured.err
        assert "type: cloze" in captured.err

    def test_yml_parsing_non_strict(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/cloze.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="cloze">' in captured.out
        assert "<text>Multiple choice cloze question</text>" in captured.out
        assert captured.err == ""

    def test_cloze_from_obj(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/cloze.yaml",
            "-s",
        ]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert "{2:NUMERICAL:%100%5.57:0.01#Some Feedback~%0%99999}" in captured.out
        assert '[["NUMQUEST"]]' not in captured.out

    def test_e2e_cli_make_question(self, tmp_path: Path) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with (test_resources_dir / "clozeRef.xml").open(encoding="utf-8") as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/cloze.yaml",
            "-o",
            str(output_file_path),
            "-s",
        ]

        # Call the main function
        main()

        with output_file_path.open("r", encoding="utf-8") as f:
            generated_xml = f.read().strip()

        # Assert the output is as expected
        assert reference_xml == generated_xml
