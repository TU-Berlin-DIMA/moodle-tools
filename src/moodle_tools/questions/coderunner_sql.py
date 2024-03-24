"""This module implements SQL DQL questions in Moodle CodeRunner."""

import base64
from pathlib import Path

import duckdb
import sqlparse  # type: ignore

from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import ParsingError


class CoderunnerQuestionSQL(Question):
    """Template for a SQL DQL question in Moodle CodeRunner."""

    QUESTION_TYPE = "coderunner"
    TEMPLATE = "coderunner_sql.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        database_path: str,
        correct_query: str,
        result: str | None = None,
        additional_testcases: list[dict[str, str]] | None = None,
        category: str | None = None,
        general_feedback: str = "",
        check_results: bool = False,
        database_connection: bool = True,
        **flags: bool,
    ) -> None:
        """Create a new SQL DQL question.

        Args:
            question: The question text displayed to students.
            title: Title of the question.
            database_path: Path to the DuckDB database (e.g., "./eshop.db").
            correct_query: The SQL string that, when executed, leads to the correct result.
            result: The expected result of the correct query.
            additional_testcases:
                    changes: A change applied between testcases to adapt the data in the tables to
                        a new testcase. (NOTE: to run the query without changes, write
                        'changes = ""'.)
                    (optional) result: The result of the testcase (right now the correct result of
                        the SQL query).
            category: The category of the question.
            general_feedback: Feedback that is provided when an answer to a coderunner
                question is submitted.
            check_results: If testcase_results were provided, runs query and checks if
                results match.
            database_connection: If this bool flag is set (default), you must execute
                moodle_tools in the GIT repo 'klausuraufgaben' or spoof it. If this bool flag is
                false, we do not attempt to create a database connection.
            flags: Additional flags that can be used to control the behavior of the
                question.
        """
        super().__init__(question, title, category, **flags)
        self.database_path = Path(database_path)
        self.database_name = self.database_path.stem
        self.general_feedback = general_feedback
        self.correct_query = sqlparse.format(correct_query, reindent=True, keyword_case="upper")

        # Query parsing and parameter validation
        if correct_query[-1] != ";":
            raise ParsingError(
                "SQL Queries must end with a ';' symbol. But the last symbol was: "
                + correct_query[-1]
            )
        if database_connection:
            if not self.database_path.exists():
                raise FileNotFoundError(
                    f"Provided database path does not exist: {self.database_path}"
                )
            self.con = duckdb.connect(str(self.database_path))
        else:
            if result is None or (
                additional_testcases
                and any("result" not in testcase for testcase in additional_testcases)
            ):
                raise ParsingError(
                    "You must provide a result if you set database_connection to false. "
                    "Otherwise we cannot automatically fetch the result from the database."
                )
            if check_results:
                raise ParsingError(
                    "Checking results requires a database connection. "
                    "However, you set database_connection to False."
                )
        if (
            check_results
            and result is None
            or (
                additional_testcases
                and any("result" not in testcase for testcase in additional_testcases)
            )
        ):
            raise ParsingError(
                "You must provide a result for each testcase if you set check_results to True."
            )

        # Execute test cases and fetch result
        self.testcases: list[dict[str, str]] = []

        if result is not None:
            self.testcases.append({"changes": "", "result": result})
        else:
            self.testcases.append({"changes": "", "result": self.fetch_database_result("")})

        if additional_testcases is not None:
            for testcase in additional_testcases:
                if "changes" not in testcase or testcase["changes"] == "":
                    raise ParsingError("An additional testcase must make changes to the database.")
                if "result" not in testcase:
                    self.testcases.append(
                        {
                            "changes": sqlparse.format(
                                testcase["changes"], reindent=True, keyword_case="upper"
                            ),
                            "result": self.fetch_database_result(testcase["changes"]),
                        }
                    )
                else:
                    self.testcases.append(
                        {
                            "changes": sqlparse.format(
                                testcase["changes"], reindent=True, keyword_case="upper"
                            ),
                            "result": testcase["result"],
                        }
                    )

        if check_results:
            for testcase in self.testcases:
                result = self.fetch_database_result(testcase["changes"]).strip()
                if result != testcase["result"].strip():
                    raise ParsingError(
                        f"Provided result:\n{testcase['result'].strip()}\ndid not match the "
                        f"result from the provided 'correct_query':\n{result}"
                    )

        if database_connection:
            self.con.close()
        self.column_widths_string = ""  # TODO: Maybe remove this

        with open(self.database_path, "rb") as file:
            self.database_encoding = base64.b64encode(file.read()).decode("utf-8")

    def fetch_database_result(self, changes: str) -> str:
        """Fetch the result of the query from the database.

        Args:
            changes: Changes to be applied to the database before executing the query.

        Returns:
            str: The result of the query.
        """
        self.con.sql("BEGIN TRANSACTION")
        self.con.sql(changes)
        result = str(self.con.sql(self.correct_query))
        self.con.sql("ROLLBACK")
        return result

    def validate(self) -> list[str]:
        """Validate the question.

        Returns:
            list[str]: A list of errors.
        """
        errors = []
        if not self.database_path:
            errors.append("No database path supplied")
        if not self.question:
            errors.append("No question supplied.")
        if not self.correct_query:
            errors.append("No correct query supplied.")
        return errors


class CoderunnerQuestionSQLAnalysis(QuestionAnalysis):
    pass
