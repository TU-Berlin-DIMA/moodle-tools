import sys

import pytest

from moodle_tools.make_questions import main


class TestInlineImages:
    """Test inlining of images.

    Because question YAML files can be organized in subfolders and moved around, the paths of
    inlined images should be relative to the folder containing the question file. This test
    verifies this behavior processing input files at different levels of the input folder
    hierarchy.
    """

    @pytest.fixture(autouse=True)
    def chdir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Change working directory before every test.

        This is required to work with a predefined set of files and folders.
        """
        monkeypatch.chdir("tests/resources/TestInlineImages")

    def test_file_in_work_dir(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = ["make-questions", "-i", "file1.yml"]
        main()
        captured = capsys.readouterr()
        assert captured.err == ""
        assert '<img alt="Inline image image1.png" src="data:image/png;base64,iVBO' in captured.out
        assert (
            '<img alt="Inline image folder1/image2.png" src="data:image/png;base64,iVBO'
            in captured.out
        )

    def test_explicit_file_in_folder(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = ["make-questions", "-i", "folder2/file4.yml"]
        main()
        captured = capsys.readouterr()
        assert captured.err == ""
        assert '<img alt="Inline image image4.png" src="data:image/png;base64,iVBO' in captured.out

    def test_recursive_files_in_folder(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = ["make-questions", "-i", "folder1"]
        main()
        captured = capsys.readouterr()
        assert captured.err == ""
        assert '<img alt="Inline image image2.png" src="data:image/png;base64,iVBO' in captured.out
        assert '<img alt="Inline image image3.png" src="data:image/png;base64,iVBO' in captured.out

    def test_image_as_bg_image(self, capsys: pytest.CaptureFixture[str]) -> None:
        sys.argv = ["make-questions", "-i", "file_bg.yml"]
        main()
        captured = capsys.readouterr()
        assert captured.err == ""
        assert """<div style="background-image: url('data:image/png;base64,iVBO""" in captured.out
        assert """'); width: 1vh; height: 20%">""" in captured.out
