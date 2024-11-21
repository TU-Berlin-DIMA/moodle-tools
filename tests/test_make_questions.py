import sys

import pytest

from moodle_tools.make_questions import iterate_inputs, main


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


class TestIterateInputs:
    """Test class for handling input files and folders."""

    @pytest.fixture(autouse=True)
    def chdir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Change working directory before every test.

        This is required to work with a predefined set of files and folders.
        """
        monkeypatch.chdir("tests/resources/TestIterateInputs")

    def test_files(self) -> None:
        """Transform filenames into an open file objects."""
        results = iterate_inputs(iter(["file1.yml", "file2.yml"]))
        names = [str(path) for path in results]
        assert names == ["file1.yml", "file2.yml"]

    def test_folders(self) -> None:
        """Recursively walk folders and return file objects for the YAML files in the folders."""
        results = iterate_inputs(iter(["folder1", "folder2"]))
        names = sorted([str(path) for path in results])
        assert names == sorted(
            [
                "folder1/folder1_1/file1.yml",
                "folder1/file1.yml",
                "folder1/file2.yml",
                "folder2/file1.yml",
            ]
        )

    def test_files_and_folders(self) -> None:
        """Process mixed files and folders."""
        results = iterate_inputs(iter(["file1.yml", "folder2"]))
        names = sorted([str(path) for path in results])
        assert names == sorted(["file1.yml", "folder2/file1.yml"])

    def test_not_a_file_or_folder_relaxed(self) -> None:
        """Ignore inputs that are not files or folders."""
        results = iterate_inputs(iter(["file1.yml", "unknown", "folder2"]), strict=False)
        names = sorted([str(path) for path in results])
        assert names == sorted(["file1.yml", "folder2/file1.yml"])

    def test_not_a_file_or_folder_strict(self) -> None:
        """Raise an exception on inputs that are not files or folders."""
        with pytest.raises(OSError, match="Not a file or folder"):
            list(iterate_inputs(iter(["file1.yml", "unknown", "folder2"]), strict=True))


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
        assert pwe.type is SystemExit
        assert pwe.value.code == 1

    def test_filter_no_match(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = ["make-questions", "-i", "examples/numerical.yaml", "-s", "-f", "Numerical NA"]

        with pytest.raises(SystemExit) as pwe:
            main()

        captured = capsys.readouterr()
        assert "Filter returned 0 questions. Exiting." in captured.out
        assert pwe.type is SystemExit
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
        assert pwe.type is SystemExit
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
