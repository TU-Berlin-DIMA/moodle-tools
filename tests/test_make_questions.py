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
        with pytest.raises(IOError):
            list(iterate_inputs(iter(["file1.yml", "unknown", "folder2"]), strict=True))
