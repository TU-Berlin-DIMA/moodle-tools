"""This module implements ISDA Streaming questions in Moodle CodeRunner."""

import inspect
import io
import shutil
from base64 import b64encode
from contextlib import redirect_stdout
from pathlib import Path

from isda_streaming import data_stream, synopsis

from moodle_tools.questions.coderunner import CoderunnerQuestion, Testcase

ISDA_STREAMING_IMPORTS = """
from typing import Any
from isda_streaming.data_stream import DataStream, TimedStream, WindowedStream, KeyedStream, \
    _check_element_structure_in_stream
from isda_streaming.synopsis import CountMinSketch, BloomFilter, ReservoirSample
"""


class CoderunnerStreamingQuestion(CoderunnerQuestion):
    """Template for a question using ISDA Streaming in Moodle CodeRunner."""

    ACE_LANG = "python"
    CODERUNNER_TYPE = "python3"
    RESULT_COLUMNS_DEFAULT = """[["Erwartet", "expected"], ["Erhalten", "got"]]"""
    RESULT_COLUMNS_DEBUG = (
        """[["Test", "testcode"], ["Erwartet", "expected"], ["Erhalten", "got"]]"""
    )
    TEST_TEMPLATE = "testlogic_streaming.py.j2"

    def __init__(
        self,
        *,
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
        parser: str | None = None,
        internal_copy: bool = False,
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
            parser: Code parser for formatting the correct answer and testcases.
            internal_copy: Flag to create an internal copy for debugging purposes.
            **flags: Additional flags for the question.
        """
        self.input_stream = Path(input_stream).absolute()

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
            parser=parser,
            internal_copy=internal_copy,
            **flags,
        )

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
        with self.input_stream.open("r", encoding="utf-8") as file:
            files.append(
                {
                    "name": self.input_stream.name,
                    "encoding": b64encode(file.read().encode()).decode("utf-8"),
                }
            )
        return files

    def fetch_expected_result(self, test_code: str) -> str:
        # TODO: Add test
        shutil.copy(self.input_stream, self.input_stream.name)

        stdout_capture = io.StringIO()
        combined_code = f"{ISDA_STREAMING_IMPORTS}\n\n{self.answer}\n\n{test_code}"

        try:
            with redirect_stdout(stdout_capture):
                exec(combined_code, {})  # noqa: S102
        except Exception as e:
            # Error occurred during execution of the test code
            error_type = type(e).__name__
            raise RuntimeError(
                f"""Error occurred during execution of the test code.
                The test code trying to execute was the following:

                {combined_code}

                ------------------------------

                This is error obtained during execution:

                {error_type}: {e}

                ------------------------------"""
            ) from e
        finally:
            Path(self.input_stream.name).unlink()

        return stdout_capture.getvalue()
