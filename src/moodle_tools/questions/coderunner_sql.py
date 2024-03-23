import sqlite3
from pathlib import Path

import sqlparse  # type: ignore

from moodle_tools.isis_database_configurations import get_base64_database_encoding
from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import ParsingError


class CoderunnerQuestionSQL(Question):
    """General template for a coderunner question. Currently, we are limited to SQL queries.

    The YML format is the following:
        title: Title of the question.
        database: Name of the ISIS database (for example "eshop" or "uni").
        question: The coderunner question displayed to students.
        correct_query: The SQL string that, when executed, leads to the correct result.
        (optional) testcases:
                testcase_changes: A change applied between testcases to adapt the data in the
                    tables to a new testcase.(NOTE: to run the query without testcase_changes,
                    write 'testcase_changes = ""'.)
                (optional) testcase_result: The result of the testcase (right now the correct
                    result of the SQL query).
        (optional) check_results: If testcase_results were provided, runs query and checks if
            results match.
        (optional) general_feedback: Feedback that is provided when an answer to a coderunner
            question is submitted.
        (optional) database_connection: If this bool flag is set (default), you must execute
            moodle_tools in the GIT repo 'klausuraufgaben' or spoof it. If this bool flag is false,
            we do not attempt to create a database connection.
    """

    QUESTION_TYPE = "coderunner"
    TEMPLATE = "coderunner_sql.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        database: str,
        correct_query: str,
        testcases: list[dict[str, str]],
        category: str | None = None,
        check_results: bool = False,
        general_feedback: str = "",
        database_connection: bool = True,
        **flags: bool,
    ) -> None:
        # Todo: Create a way (possible with extra script) to apply moodle-tools to entire folders
        # with '.yaml' files
        super().__init__(question, title, category, **flags)
        self.database_name = database
        self.database_path = Path().cwd() / ("../datenbanken/" + database + ".db")
        if correct_query[-1] != ";":
            raise ParsingError(
                "SQL Queries must end with a ';' symbol. But the last symbol was: "
                + correct_query[-1]
            )
        self.correct_query = sqlparse.format(correct_query, reindent=True, keyword_case="upper")
        if check_results and not database_connection:
            raise ParsingError(
                "Checking results requires a database connection. "
                "However, you set database_connection to False."
            )
        if database_connection:
            if not self.database_path.exists():
                raise FileNotFoundError(
                    "Provided database path did not exists: "
                    + str(self.database_path)
                    + ".Moodle-tools must be executed in the the folder of the"
                    " 'klausurfragen' repo that contains the 'question_x.yaml'"
                    " files. For example, 'klausurfragen/sql-dql/uni/questions'. The"
                    " corresponding database file is located on the same level as the"
                    " 'questions' folder in 'databases'.For example,"
                    " 'klausurfragen/sql-dql/uni/databases."
                )
            self.con = sqlite3.connect(str(self.database_path), timeout=5)
            self.cursor = self.con.cursor()
        # Execute additional test cases and get results.
        self.column_widths_string = ""
        self.testcases = testcases
        self.testcases_string = ""
        self.general_feedback = general_feedback
        self.results = []
        # Add additional results if present
        if testcases is None:
            self.results.append(self.fetch_database_result())
        else:
            for additional_testcase in self.testcases:
                if "testcase_result" not in additional_testcase:
                    # reset connection
                    self.con = sqlite3.connect(str(self.database_path), timeout=5)
                    self.cursor = self.con.cursor()
                    # If a user mistypes 'testcase_result' or names it differently, we generate one
                    if not database_connection:
                        raise ParsingError(
                            "You must provide a result if you set database_connection to false. "
                            "Otherwise we cannot automatically fetch the result from the database."
                        )
                    # need to reset database
                    if additional_testcase["testcase_changes"] != "":
                        self.execute_change_queries(additional_testcase["testcase_changes"])
                    self.results.append(self.fetch_database_result())
                else:
                    # reset connection
                    self.con = sqlite3.connect(str(self.database_path), timeout=5)
                    self.cursor = self.con.cursor()
                    self.results.append(
                        additional_testcase["testcase_result"].replace("\n ", "\n")
                    )
                    if check_results:
                        if additional_testcase["testcase_changes"] != "":
                            self.execute_change_queries(additional_testcase["testcase_changes"])
                        correct_query_result = self.fetch_database_result()
                        if correct_query_result != self.results[-1]:
                            raise ParsingError(
                                f"Provided result: {self.results[-1]} did not match the result "
                                f"from the provided 'correct_query': {correct_query_result}"
                            )
        self.con.close()

        self.database_encoding = get_base64_database_encoding(self.database_name)

    def execute_change_queries(self, change_queries: str) -> None:
        if ";" not in change_queries:
            raise ParsingError(
                "Additional testcases supplied, but no SQL queries that are terminated with a ';' "
                "symbol were found."
            )
        change_queries_list = change_queries.split(";")
        for change_query in change_queries_list:
            self.cursor.execute(change_query.rstrip().lstrip())

    def fetch_database_result(self) -> str:
        # TODO: This method can probably be refactored/removed with duckdb
        self.cursor.execute(self.correct_query)
        name_string = ""
        rows = self.cursor.fetchall()
        column_names = [description[0] for description in self.cursor.description]
        column_lengths = [
            max(len(name), max(len(str(row[i])) for row in rows))
            for i, name in enumerate(column_names)
        ]
        for i, name in enumerate(column_names):
            name_string += name + ((column_lengths[i] - len(name)) * " ") + "  "
        name_string += "\n"
        for length in column_lengths:
            name_string += length * "-" + "  "
        name_string += "\n"
        for row in rows:
            for i, value in enumerate(row):
                value = str(value)
                name_string += str(value) + ((column_lengths[i] - len(value)) * " ") + "  "
            name_string += "\n"
        return name_string

    def validate(self) -> list[str]:
        errors = []
        if not self.database_name:
            errors.append("No database name supplied")
        if not self.question:
            errors.append("No question supplied.")
        if not self.correct_query:
            errors.append("No correct query supplied.")
        return errors


class CoderunnerQuestionSQLAnalysis(QuestionAnalysis):
    pass
