import sys

import pytest

from moodle_tools.make_questions import main


class TestAllowEval:
    def test_eval(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/numerical_eval.yaml", "-s", "--allow-eval"]

        # Call the main function
        main()
        captured = capsys.readouterr()

        # Assert the output is as expected
        assert '<question type="numerical">' in captured.out
        assert "<text><![CDATA[4]]></text>" in captured.out
        assert "The answer is: 2 + 2 = 4" in captured.out
        assert captured.err == ""

    def test_eval_not_allowed(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Simulate command-line arguments
        sys.argv = ["make-questions", "-i", "examples/numerical_eval.yaml", "-s"]

        # Call the main function
        with pytest.raises(SystemExit) as pwe:
            main()

        captured = capsys.readouterr()

        # Assert the output is as expected
        assert "Explicit evaluation is not allowed but used" in captured.err
        assert pwe.type is SystemExit
        assert pwe.value.code == 1
