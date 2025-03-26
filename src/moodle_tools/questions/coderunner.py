"""This module implements the abstract base for questions in Moodle CodeRunner."""

import abc
from pathlib import Path
from typing import Required, TypedDict

from jinja2 import Environment

from moodle_tools.questions.question import Question
from moodle_tools.utils import ParsingError, format_code


class Testcase(TypedDict, total=False):
    """Template for a test case in a Moodle CodeRunner question.

    Args:
        description: A description of the testcase (default `Testfall _i_`).
        code: A piece of code that depending on the test logic is executed before or after the
            student answer.
        result: The expected result of the testcase. If you do not provide it, it will be generated
            by running the correct answer and testcode.
        grade: Number of points for the test (default 1). Only used if all_or_nothing is False.
        hiderestiffail: If True, all following tests are hidden if the test fails (default False).
        hidden: If True, the test hidden. Otherwise, it is shown to students (default False).
        show: If the test is hidden, this is set to "HIDE". Otherwise, it is set to "SHOW".
    """

    description: str
    code: Required[str]
    result: Required[str]
    grade: float
    hiderestiffail: bool
    hidden: bool
    show: str


class CoderunnerQuestion(Question):
    """Template for a generic question in Moodle CodeRunner."""

    QUESTION_TYPE = "coderunner"
    XML_TEMPLATE = "coderunner.xml.j2"
    ACE_LANG: str
    CODERUNNER_TYPE: str
    RESULT_COLUMNS_DEFAULT: str
    RESULT_COLUMNS_DEBUG: str
    TEST_TEMPLATE: str

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answer: str,
        testcases: list[Testcase],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        answer_preload: str = "",
        all_or_nothing: bool = True,
        check_results: bool = False,
        parser: str | None = None,
        internal_copy: bool = False,
        **flags: bool,
    ) -> None:
        """Create a new CodeRunner question.

        Args:
            question: The question text displayed to students.
            title: Title of the question.
            answer: The piece of code that, when executed, leads to the correct result.
            testcases: List of testcases for checking the student answer.
            category: The category of the question.
            grade: The total number of points of the question.
            general_feedback: Feedback that is displayed once the quiz has closed.
            answer_preload: Text that is preloaded into the answer box.
            all_or_nothing: If True, the student must pass all test cases to receive any
                points. If False, the student gets partial credit for each test case passed.
            check_results: If testcase_results are provided, run the reference solution and check
                if the results match.
            parser: Code parser for formatting the correct answer and testcases.
            internal_copy: Flag to create an internal copy for debugging purposes.
            flags: Additional flags that can be used to control the behavior of the
                question.
        """
        super().__init__(question, title, category, grade, general_feedback, **flags)
        self.answer = answer
        self.answer_preload = answer_preload
        self.all_or_nothing = all_or_nothing
        self.parser = parser
        self.result_columns = (
            self.RESULT_COLUMNS_DEBUG if internal_copy else self.RESULT_COLUMNS_DEFAULT
        )

        # Apply consistent formatting to the answer code
        self.answer = format_code(self.answer, formatter=self.parser)

        with (Path(__file__).parent / "templates" / self.TEST_TEMPLATE).open(
            "r", encoding="utf-8"
        ) as file:
            self.test_logic = file.read()

        # Execute test cases and fetch results
        self.testcases: list[Testcase] = []
        for i, testcase in enumerate(testcases):
            if "code" not in testcase:
                raise ParsingError(
                    "A testcase must include the key code. Leave it empty if no changes are "
                    "needed."
                )
            if "result" not in testcase:
                if check_results:
                    raise ParsingError(
                        "You must provide a result for each test case if check_results is True."
                    )
                testcase["result"] = self.fetch_expected_result(testcase["code"])
            if "grade" not in testcase:
                testcase["grade"] = 1.0
            if "hiderestiffail" not in testcase:
                testcase["hiderestiffail"] = False
            if "description" not in testcase:
                testcase["description"] = f"Testfall {i}"
            if "hidden" not in testcase or testcase["hidden"] is False:
                testcase["show"] = "SHOW"
            else:
                testcase["show"] = "HIDE"

            # Apply consistent formatting to each testcase code, same parser as answer
            testcase["code"] = format_code(testcase["code"], formatter=self.parser)

            self.testcases.append(testcase)

    @property
    @abc.abstractmethod
    def files(self) -> list[dict[str, str]]:
        """Get all supporting files for the question as base64 strings.

        Returns:
            A list of dictionaries with the keys "name" and "encoding".
        """

    @abc.abstractmethod
    def fetch_expected_result(self, test_code: str) -> str:
        """Fetch the result of the correct solution for a given test case.

        Args:
            test_code: Changes to be applied before or after the correct solution.

        Returns:
            str: The result of the correct solution.
        """
        raise NotImplementedError

    def check_results(self) -> bool:
        """Verify that the manually provided results match the dynamically fetched results."""
        for testcase in self.testcases:
            result = self.fetch_expected_result(testcase["code"]).strip()
            if result != testcase["result"].strip():
                raise ParsingError(
                    f"Provided result:\n{testcase['result'].strip()}\ndid not match the "
                    f"result from the provided 'answer':\n{result}"
                )
        return True

    def validate(self) -> list[str]:
        return super().validate()

    def to_xml(self, env: Environment) -> str:
        """Generate a Moodle XML export of the question."""
        template = env.get_template(self.XML_TEMPLATE)
        return template.render(
            self.__dict__
            | {
                "type": self.QUESTION_TYPE,
                "ace_lang": self.ACE_LANG,
                "coderunner_type": self.CODERUNNER_TYPE,
                "files": self.files,
            }
        )
