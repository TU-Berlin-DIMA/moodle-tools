"""This module implements ISDA Streaming questions in Moodle CodeRunner."""

import inspect
import io
from base64 import b64encode
from contextlib import redirect_stdout
from pathlib import Path

from isda_streaming import data_stream, synopsis

from moodle_tools.questions.coderunner import CoderunnerQuestion, Testcase


class CoderunnerStreamingQuestion(CoderunnerQuestion):
    """Template for a question using ISDA Streaming in Moodle CodeRunner."""

    ACE_LANG = "pyhthon"
    CODERUNNER_TYPE = "PROTOTYPE_isda_streaming"
    RESULT_COLUMNS = """[["Erwartet", "expected"], ["Erhalten", "got"]]"""
    TEST_TEMPLATE = "testlogic_streaming.py.j2"

    def __init__(
        self,
        question: str,
        title: str,
        answer: str,
        testcases: list[Testcase],
        input_stream: str | Path,
        category: str | None = None,
        grade: float = 1,
        general_feedback: str = "",
        answer_preload: str = "",
        all_or_nothing: bool = True,
        check_results: bool = False,
        **flags: bool,
    ) -> None:
        """Create a new ISDA Streaming question.

        Args:
            question: The question text displayed to students.
            title: Title of the question.
            answer: The piece of code that, when executed, leads to the correct result.
            testcases: List of testcases for checking the student answer.
            input_stream: Path to a CSV file that simulates the input data stream.
            category: The category of the question.
            grade: The total number of points of the question.
            general_feedback: Feedback that is displayed once the quiz has closed.
            answer_preload: Text that is preloaded into the answer box.
            all_or_nothing: If True, the student must pass all test cases to receive any
                points. If False, the student gets partial credit for each test case passed.
            check_results: If True, the expected results are checked against the provided answer
                and testcases.
            **flags: Additional flags for the question.
        """
        # pylint: disable=duplicate-code
        super().__init__(
            question=question,
            title=title,
            answer=answer,
            testcases=testcases,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            answer_preload=answer_preload,
            all_or_nothing=all_or_nothing,
            check_results=check_results,
            **flags,
        )
        self.input_stream = Path(input_stream)

        if check_results:
            self.check_results()

    @property
    def files(self) -> list[dict[str, str]]:
        files = []
        files.append(
            {
                "name": "data_stream.py",
                "encoding": b64encode(inspect.getsource(data_stream).encode()).decode("utf-8"),
            }
        )
        files.append(
            {
                "name": "synopsis.py",
                "encoding": b64encode(inspect.getsource(synopsis).encode()).decode("utf-8"),
            }
        )
        with open(self.input_stream, "r", encoding="utf-8") as file:
            files.append(
                {
                    "name": self.input_stream.name,
                    "encoding": b64encode(file.read().encode()).decode("utf-8"),
                }
            )
        return files

    def fetch_expected_result(self, test_code: str) -> str:
        stdout_capture = io.StringIO()
        eval(self.answer)
        with redirect_stdout(stdout_capture):
            eval(test_code)
        return stdout_capture.getvalue()
