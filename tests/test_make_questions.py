import sys

import pytest

from moodle_tools.make_questions import main


class TestMakeQuestionArguments:
    def test_argument_parsing_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-h"]

        expected_output = """
        usage: make-questions [-h] -i INPUT [INPUT ...] [-o OUTPUT] [-s] [-q]
        """.strip()

        # Call the main function
        with pytest.raises(SystemExit) as e:
            main()
        captured = capsys.readouterr()

        # Assert the output is as expected

        assert expected_output in captured.out
        assert str(e.value) == "0"

    def test_automatic_numbering(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = [
            "make-questions",
            "-i",
            "examples/multiple-choice.yaml",
            "-s",
            "--add-question-index",
        ]
        main()
        captured = capsys.readouterr()
        assert "Question title (1)" in captured.out
        assert "Question title (2)" in captured.out
        assert "Question title (3)" not in captured.out
        assert "Question title (0)" not in captured.out


class TestFilterQuestions:
    """Test class for only exporting a subset of questions."""

    def test_filter_working(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = [
            "make-questions",
            "-i",
            "examples/numerical.yaml",
            "-s",
            "-f",
            "Numerical question",
        ]
        main()
        captured = capsys.readouterr()
        assert captured.err == ""
        assert """Numerical question""" in captured.out
        assert """Simple Numerical""" not in captured.out

    def test_filter_fewer_matches(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = [
            "make-questions",
            "-i",
            "examples/numerical.yaml",
            "-s",
            "-f",
            "Numerical question",
            "-f",
            "Numerical NA",
        ]

        with pytest.raises(SystemExit) as pwe:
            main()

        captured = capsys.readouterr()
        assert "Filter returned fewer questions than expected. Exiting." in captured.out
        assert pwe.type == SystemExit
        assert pwe.value.code == 1

    def test_filter_no_match(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = ["make-questions", "-i", "examples/numerical.yaml", "-s", "-f", "Numerical NA"]

        with pytest.raises(SystemExit) as pwe:
            main()

        captured = capsys.readouterr()
        assert "Filter returned 0 questions. Exiting." in captured.out
        assert pwe.type == SystemExit
        assert pwe.value.code == 1

    def test_automatic_numbering_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = [
            "make-questions",
            "-i",
            "examples/multiple-choice.yaml",
            "-s",
            "-f",
            "Question title",
            "--add-question-index",
        ]

        with pytest.raises(SystemExit) as pwe:
            main()

        captured = capsys.readouterr()
        assert "Filter returned 0 questions. Exiting." in captured.out
        assert pwe.type == SystemExit
        assert pwe.value.code == 1

    def test_automatic_numbering(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = [
            "make-questions",
            "-i",
            "examples/multiple-choice.yaml",
            "-s",
            "-f",
            "Question title (2)",
            "--add-question-index",
        ]
        main()
        captured = capsys.readouterr()
        assert "Question title (1)" not in captured.out
        assert "Question title (2)" in captured.out
