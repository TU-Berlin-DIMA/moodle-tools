import sys
from pathlib import Path

import pytest

from moodle_tools.make_questions import main


class TestCoderunnerQuestionSQL:
    def test_yml_parsing_non_strict(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/coderunner-dql-wo_connection.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="coderunner">' in captured.out
        assert "<text>Sample SQL Coderunner Question</text>" in captured.out
        assert captured.err == ""

    def test_correct_number_of_testcases(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/coderunner-dql-wo_connection.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is expected
        assert str(captured.out).count("Testfall") == 2
        assert captured.err == ""

    def test_correct_number_of_inserts_into(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/coderunner-dql-wo_connection.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is expected
        captured_out_str = str(captured.out)
        assert captured_out_str.count("INSERT INTO") == 3
        assert (
            captured_out_str.count("""VALUES (34567, 'Pokemon Glurak Holo Karte', 50000);""") == 1
        )
        assert captured_out_str.count("""VALUES (12345, 'Audi A6', 25000""") == 1
        assert captured_out_str.count("""VALUES (23456, 'BMW', 50000);""") == 1
        assert captured.err == ""

    def test_correct_file_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/coderunner-dql-wo_connection.yaml", "-s"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is expected
        assert """file name=\"eshop.db\" path=\"/\" encoding=\"base64\"""" in captured.out
        assert captured.err == ""

    def test_e2e_cli_make_question_wo_connection(self, tmp_path: Path) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with (test_resources_dir / "coderunner-dql-wo_connection.xml").open(encoding="utf-8") as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/coderunner-dql-wo_connection.yaml",
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

    def test_e2e_cli_make_question_w_connection(self, tmp_path: Path) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with (test_resources_dir / "coderunner-dql-w_connection.xml").open(encoding="utf-8") as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/coderunner-dql-w_connection.yaml",
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

    def test_e2e_cli_make_question_ddl_test_template(self, tmp_path: Path) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with (test_resources_dir / "coderunner-ddl_replace_tablecorrectness.xml").open(
            encoding="utf-8"
        ) as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/coderunner-ddl.yaml",
            "-o",
            str(output_file_path),
        ]

        # Call the main function
        main()

        # Assert the output is as expected by loading the created xml file into a string object
        with output_file_path.open("r", encoding="utf-8") as f:
            generated_xml = f.read().strip()
        assert reference_xml == generated_xml

    def test_e2e_cli_make_question_ddl_copy_intern(self, tmp_path: Path) -> None:
        # Get the path to the directory containing the test resources
        test_resources_dir = Path(__file__).parent / "../resources"

        # Load content from the file
        with (test_resources_dir / "coderunner-ddl-intern.xml").open(encoding="utf-8") as f:
            reference_xml = f.read().strip()

        # Generate the file using the xyz function
        output_file_path = tmp_path / "output.txt"

        # Simulate command-line arguments
        sys.argv = [
            "make-questions",
            "-i",
            "examples/coderunner-ddl-intern.yaml",
            "-o",
            str(output_file_path),
        ]

        # Call the main function
        main()

        # Assert the output is as expected by loading the created xml file into a string object
        with output_file_path.open("r", encoding="utf-8") as f:
            generated_xml = f.read().strip()
        assert reference_xml == generated_xml
