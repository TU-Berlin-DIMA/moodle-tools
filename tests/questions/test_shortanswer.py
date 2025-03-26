import sys
from pathlib import Path

import pytest

from moodle_tools.make_questions import main


class TestShortAnswer:
    def test_yml_parsing_strict(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/shortanswer.yaml"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert "The following question did not pass strict validation" in captured.err
        assert "type: shortanswer" in captured.err

    def test_yml_parsing_non_strict(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/shortanswer.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="shortanswer">' in captured.out
        assert "<text>Short Answer question</text>" in captured.out
        assert captured.err == ""

    def test_e2e_cli_make_question(self, tmp_path: Path) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with (test_resources_dir / "shortanswerRef.xml").open(encoding="utf-8") as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/shortanswer.yaml",
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

    def test_answerbox_replacement(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # create shortanswer question yaml with answerbox
        yaml_base = """
---
type: shortanswer
title: Short answer question
question: "This is a {{abph}} question."
answers:
  - ananswer
        """

        # create temporary yaml file
        yaml_file_path = tmp_path / "shortanswer.yaml"
        with yaml_file_path.open("w", encoding="utf-8") as f:
            f.write(yaml_base.replace("{{abph}}", "[[ANSWERBOX]]"))
            f.write(yaml_base.replace("{{abph}}", "[[ANSWERBOX=8]]"))
            f.write(yaml_base.replace("{{abph}}", "[[ANSWERBOX=4]]"))

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            str(yaml_file_path),
            "-s",
        ]

        # Call the main function
        main()
        captured = capsys.readouterr()

        assert '<question type="shortanswer">' in captured.out
        assert "This is a __________ question." in captured.out
        assert "This is a ________ question." in captured.out
        assert "This is a _____ question." in captured.out
        assert "This is a ____ question." not in captured.out
