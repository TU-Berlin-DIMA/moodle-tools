"""This module implements SQL questions in Moodle CodeRunner."""

import io
import json
import random
import re
import shutil
import string
import tempfile
from base64 import b64encode
from collections.abc import Generator, Iterable
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from typing import Any, TypedDict, cast

import duckdb
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger

from moodle_tools.enums import CRGrader
from moodle_tools.questions.coderunner import CoderunnerQuestion, Testcase
from moodle_tools.utils import ParsingError, preprocess_text

DB_CONNECTION_ERROR = (
    "Question parsing requested a database connection but `database_connection` is False. In this "
    "case, you must provide a result for each test case since we cannot automatically fetch the "
    "result from the database."
)

JinjaEnv = Environment(
    loader=PackageLoader("moodle_tools.questions"),
    lstrip_blocks=True,
    trim_blocks=True,
    autoescape=select_autoescape(),
)


@contextmanager
def open_tmp_db_connection(path: str | Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Open a connection to a temporary copy of a provided database.

    Args:
        path: Path to the database file.

    Yields:
        duckdb.DuckDBPyConnection: A connection to the database.
    """
    with tempfile.NamedTemporaryFile("wb") as tmp_db:
        shutil.copy2(path, tmp_db.name)
        con = duckdb.connect(tmp_db.name, config={"threads": 1})
        try:
            yield con
        finally:
            con.close()


class FlexType(TypedDict):
    """TypedDict for flex type."""

    attribute: str
    allowed: list[str]
    used_in: list[str]


class CoderunnerSQLQuestion(CoderunnerQuestion):
    """Template for a SQL question in Moodle CodeRunner."""

    ACE_LANG = "sql"
    MAX_ROWS = 50
    MAX_WIDTH = 500

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answer: str,
        testcases: list[Testcase],
        database_path: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        answer_preload: str = "",
        all_or_nothing: bool = True,
        check_results: bool = False,
        parser: str | None = None,
        extra: dict[str, str | dict[str, Any]] | None = None,
        grader: CRGrader = CRGrader.EQUALITY_GRADER,
        is_combinator: bool = True,
        internal_copy: bool = False,
        database_connection: bool = True,
        **flags: bool,
    ) -> None:
        """Create a new SQL question.

        Args:
            question: The question text displayed to students.
            title: Title of the question.
            answer: The piece of code that, when executed, leads to the correct result.
            testcases: List of testcases for checking the student answer.
            database_path: Path to the DuckDB database (e.g., "./eshop.db").
            category: The category of the question.
            grade: The total number of points of the question.
            general_feedback: Feedback that is displayed once the quiz has closed.
            answer_preload: Text that is preloaded into the answer box.
            all_or_nothing: If True, the student must pass all test cases to receive any
                points. If False, the student gets partial credit for each test case passed.
            check_results: If testcase_results are provided, run the reference solution and check
                if the results match.
            parser: Code parser for formatting the correct answer and testcases.
            extra: Extra information for parsing the question.
            grader: Grader to use for the question.
            is_combinator: If True, the question automatically builds testcases with TWIG
            internal_copy: Flag to create an internal copy for debugging purposes.
            database_connection: If True, connect to the provided database to fetch the expected
                result. If False, use the provided result.
            flags: Additional flags that can be used to control the behavior of the
                question.
        """
        self.inmemory_db = database_path == ":memory:"

        if self.inmemory_db:
            self.database_path = Path(
                f"db-{''.join(random.choices(string.digits, k=12))}.db"  # noqa: S311
            ).absolute()
            duckdb.connect(self.database_path, config={"threads": 1}).close()

        else:
            self.database_path = Path(database_path).absolute()
            if not self.database_path.exists():
                raise FileNotFoundError(
                    f"Provided database path does not exist: {self.database_path}"
                )

        self.database_connection = database_connection

        answer = answer.strip()

        if answer[-1] != ";":
            raise ParsingError(
                f"SQL queries must end with a ';' symbol. But the last symbol was: {answer[-1]}"
            )

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
            extra=extra,
            grader=grader,
            is_combinator=is_combinator,
            internal_copy=internal_copy,
            **flags,
        )

    @property
    def files(self) -> list[dict[str, str]]:
        if self.inmemory_db:
            # If the database is in memory, we don't need to send it
            return []
        with self.database_path.open("rb") as file:
            files = {
                "name": self.database_path.name,
                "encoding": b64encode(file.read()).decode("utf-8"),
            }

        return [files]

    def cleanup(self) -> None:
        logger.debug("Cleaning up {}.", self.__class__.__name__)

        if self.inmemory_db:
            logger.debug("Removing temporary DB file.")
            self.database_path.unlink()


class CoderunnerDDLQuestion(CoderunnerSQLQuestion):
    """Template for a SQL DDL/DML question in Moodle CodeRunner."""

    CODERUNNER_TYPE = "python3"
    RESULT_COLUMNS_DEFAULT = """[["Testfall", "extra"], ["Bewertung", "awarded"]]"""
    RESULT_COLUMNS_DEBUG = (
        """[["Beschreibung", "extra"], """
        """["Erwartet", "expected"], ["Erhalten", "got"], """
        """["Test", "testcode"], ["Bewertung", "awarded"]]"""
    )
    TEST_TEMPLATE = "testlogic_ddl.py.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answer: str,
        testcases: list[Testcase],
        database_path: str,
        category: str | None = None,
        grade: float = 1,
        general_feedback: str = "",
        answer_preload: str = "",
        all_or_nothing: bool = False,
        check_results: bool = False,
        parser: str | None = None,
        extra: dict[str, str | dict[str, Any]] | None = None,
        internal_copy: bool = False,
        database_connection: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(
            question=question,
            title=title,
            answer=answer,
            testcases=testcases,
            database_path=database_path,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            answer_preload=answer_preload,
            all_or_nothing=all_or_nothing,
            check_results=check_results,
            parser=parser,
            extra=extra,
            grader=CRGrader.TEMPLATE_GRADER,
            is_combinator=True,
            internal_copy=internal_copy,
            database_connection=database_connection,
            **flags,
        )

        if check_results:
            self.check_results()

    def update_testcase_from_extra(self, testcase: Testcase) -> None:
        self.put_flextypes_to_testcases(testcase)

        testcase["code"] = self.render_test_templates(testcase)

    def put_flextypes_to_testcases(self, testcase: Testcase) -> None:
        tested_tables = [
            statement.split(" ")[1].strip()
            for statement in testcase["code"].split(";")
            if statement.split(" ")[0].strip() == "MT_testtablecorrectness"
        ]

        if not tested_tables:
            return

        if isinstance(testcase["extra"], dict) and "flex_datatypes" in testcase["extra"]:
            flex_datatypes: list[FlexType] = testcase["extra"]["flex_datatypes"]

            if isinstance(testcase["extra"]["flex_datatypes"], dict):
                # This exists for legacy reasons
                testcase["extra"]["flex_datatypes"] = [
                    {"attribute": attr, "allowed": ft, "used_in": tested_tables}
                    for attr, ft in testcase["extra"]["flex_datatypes"].items()
                ]
            else:
                raise ParsingError(
                    "Testcase {} has an invalid flex_datatypes entry.", testcase["description"]
                )
            testcase["extra"]["flex_datatypes"] = flex_datatypes

        if self.extra:
            question_flex_datatypes: list[FlexType] = cast(
                "list[FlexType]", self.extra.get("flex_datatypes", [])
            )

            testcase_extra = cast("dict[str, Any]", testcase.get("extra", {}))

            if question_flex_datatypes and "flex_datatypes" in testcase_extra:
                raise ParsingError(
                    "Testcase {} already contains a flex_datatypes entry.", testcase["description"]
                )

            table_flex_types: list[FlexType] = [
                ft
                for ft in question_flex_datatypes
                if any(table for table in tested_tables if table in ft["used_in"])
            ]

            if table_flex_types:
                testcase_extra["flex_datatypes"] = table_flex_types
                testcase["extra"] = testcase_extra

    @staticmethod
    def render_test_templates(testcase: Testcase) -> str:
        """Replace test templates with the respective Jinja templates and render them.

        The tests are modified in-place. The function returns the same list it received.

        Args:
            testcase: the testcase.

        Returns:
            str: The rendered test code.
        """
        rendered_statements = []

        test_statements = [t.strip() for t in testcase["code"].split(";") if t.strip()]
        for statement in test_statements:
            match statement.split(" "):
                case ["MT_testtablecorrectness", table_name, *tests]:
                    flex_datatypes_str = ""
                    if isinstance(testcase["extra"], dict):
                        flex_datatypes: list[FlexType] = testcase["extra"].get(
                            "flex_datatypes", []
                        )
                        flex_datatypes_str = (
                            json.dumps(
                                {
                                    ft["attribute"]: ft["allowed"]
                                    for ft in flex_datatypes
                                    if table_name in ft["used_in"]
                                },
                                indent=4,
                                ensure_ascii=False,
                            )
                            .replace("'", "''")
                            .replace('"', "'")
                        )

                    templates: Iterable[Path] = [
                        Path(template)
                        for template in JinjaEnv.list_templates(
                            filter_func=lambda n: n.startswith("ddl_check_tablecorrectness/")
                        )
                    ]

                    # If tests are provided, filter the templates to only include those
                    if tests:
                        templates = filter(
                            lambda t: t.name.split(".")[0].split("-")[1] in tests, templates
                        )

                    rendered_statements.append(
                        "\n\n----------\n\n".join(
                            [
                                JinjaEnv.get_template(str(template)).render(
                                    tablename=table_name, flex_datatypes=flex_datatypes_str
                                )
                                for template in templates
                            ]
                        )
                    )

                case ["MT_testkeywordpresent", keyword]:
                    additional_info = testcase.get("additional_info", {})
                    additional_info["keyword_present"] = keyword.lower()
                    testcase["additional_info"] = additional_info

                    testcase["code"] = ""

                case _:
                    if statement.startswith("MT_"):
                        logger.warning(
                            "Test code {} does not match any known template.", testcase["code"]
                        )
                    else:
                        rendered_statements.append(statement + ";")

        return "\n\n".join(rendered_statements)

    def fetch_expected_result(self, testcase: Testcase) -> str:  # noqa: C901
        if not self.database_connection:
            raise ParsingError(DB_CONNECTION_ERROR)

        # A DDL/DML test might include multiple statements, so we need to split them
        statements = [code for code in testcase["code"].split(";") if code.strip()]
        additional_info = testcase.get("additional_info", {})

        if not statements and "keyword_present" in additional_info:
            return f"Keyword '{additional_info['keyword_present']}' is present.".lower()

        stdout_capture = io.StringIO()

        with redirect_stdout(stdout_capture), open_tmp_db_connection(self.database_path) as con:
            con.sql(self.answer)
            for statement in statements:
                try:
                    res = con.sql(statement)
                    if res:
                        res.show(max_width=self.MAX_WIDTH, max_rows=self.MAX_ROWS)
                    else:
                        print(res)
                except (duckdb.ConstraintException, duckdb.ConversionException) as e:
                    # DuckDB prints the individual constraint implementation in the error message
                    # so we have to filter it out.

                    match_tut = re.search(r"INSERT INTO (.+?) ", statement)

                    if not match_tut:
                        print(e)
                        continue

                    table_under_test = match_tut.group(1)

                    testcase_extra = cast("dict[str, Any]", testcase["extra"])

                    flex_datatypes = cast(
                        "list[FlexType]", testcase_extra.get("flex_datatypes", [])
                    )

                    table_flex_types = [
                        flex_types
                        for flex_types in flex_datatypes
                        if table_under_test in flex_types.get("used_in", [])
                    ]

                    table_flex_dt = [ft.get("allowed", []) for ft in table_flex_types]

                    table_has_flex_enum = any(
                        "ENUM" in item for allowed in table_flex_dt for item in allowed
                    ) and not all("ENUM" in item for allowed in table_flex_dt for item in allowed)

                    match_check = re.search(
                        r"^Constraint Error: CHECK constraint failed on table (.+?) .*$", str(e)
                    )

                    match_enum = re.search(r"^Conversion Error: Could not convert.*$", str(e))

                    if (match_check or match_enum) and table_has_flex_enum:
                        additional_info = cast("dict[str, Any]", testcase["additional_info"])
                        flex_enum_tables = additional_info.get("flex_enum_tables", [])
                        if table_under_test not in flex_enum_tables:
                            flex_enum_tables.append(table_under_test)
                            additional_info["flex_enum_tables"] = flex_enum_tables
                            testcase["additional_info"] = additional_info

                        print(
                            f"CHECK constraint failed or wrong "
                            f"ENUM in table {table_under_test}".lower()
                        )
                    elif match_check:
                        print(f"CHECK constraint failed on table {table_under_test}".lower())
                    else:
                        print(str(e).lower())
                except duckdb.Error as e:
                    print(e)

        return stdout_capture.getvalue()

    def validate_query(self, testcase: Testcase) -> None:
        if "## non_viable_flex_type ##" in testcase["result"]:
            logger.warning(
                "Non-viable flex type detected in test case {}. "
                "Please check that the set of possible types matches the sample solution.",
                testcase.get("description", "Untitled test"),
            )


class CoderunnerDQLQuestion(CoderunnerSQLQuestion):
    """Template for a SQL DQL question in Moodle CodeRunner."""

    CODERUNNER_TYPE = "python3"
    RESULT_COLUMNS_DEFAULT = ""  # TODO
    RESULT_COLUMNS_DEBUG = ""  # TODO
    TEST_TEMPLATE = "testlogic_dql.py.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answer: str,
        testcases: list[Testcase],
        database_path: str,
        category: str | None = None,
        grade: float = 1,
        general_feedback: str = "",
        answer_preload: str = "",
        all_or_nothing: bool = True,
        check_results: bool = False,
        parser: str | None = None,
        extra: dict[str, str | dict[str, Any]] | None = None,
        internal_copy: bool = False,
        database_connection: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(
            question=question,
            title=title,
            answer=answer,
            testcases=testcases,
            database_path=database_path,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            answer_preload=answer_preload,
            all_or_nothing=all_or_nothing,
            check_results=check_results,
            parser=parser,
            extra=extra,
            grader=CRGrader.EQUALITY_GRADER,
            is_combinator=True,
            internal_copy=internal_copy,
            database_connection=database_connection,
            **flags,
        )

        if database_connection:
            self.question += preprocess_text(self.extract_expected_output_schema(answer), **flags)

        # We use standardized test names and hide all tests but the first for this type of question
        for i, testcase in enumerate(self.testcases):
            testcase["description"] = f"Testfall {i + 1}"
            if i > 0 and "hidden" not in testcase:
                testcase["show"] = "HIDE"

        if check_results:
            self.check_results()

    def fetch_expected_result(self, testcase: Testcase) -> str:
        if not self.database_connection:
            raise ParsingError(DB_CONNECTION_ERROR)

        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture), open_tmp_db_connection(self.database_path) as con:
            con.sql(testcase["code"])
            res = con.sql(self.answer)
            if res:
                res.show(max_width=self.MAX_WIDTH, max_rows=self.MAX_ROWS)
            else:
                print(res)

        return stdout_capture.getvalue()

    def extract_expected_output_schema(self, query: str) -> str:
        """Extract the output schema of a query from its operators and its result.

        Args:
            query: The SQL query to parse.

        Returns:
            str: The output schema of the query.
        """
        if not self.database_connection:
            raise ParsingError(DB_CONNECTION_ERROR)

        with open_tmp_db_connection(self.database_path) as con:
            # Run the query, so that we can then get the schema output
            result = con.sql(query)
            result_schema = result.description

        # Grab the ORDER BY statement so that we can get sorting information
        match = re.search(".*ORDER BY (.*);?", query, flags=re.IGNORECASE)
        column_orderings = {}
        if match:
            # Splitting the order on "," and on " " to get the column name and the order modifier
            order_by_statements = match.group(1).replace(";", "").split(",")
            for item in order_by_statements:
                item_split = item.strip().split(" ")
                if len(item_split) == 1:
                    item_split.append("ASC")
                column_orderings.update({item_split[0]: item_split[1]})
        else:
            logger.warning(
                "No ORDER BY statement found in the query. Please ensure that this was intended. "
                "CodeRunner only performs string comparisons between solutions so usually an "
                "ordering is necessary to ensure solution robustness."
            )

        # Creating the output schema string, appending it to the question_text, and return it
        asc_desc_map = {"asc": "↑", "desc": "↓"}
        output_elements: list[str] = []
        for column in result_schema:
            column_name = column[0]
            found_column = False
            for column_order, order_statement in column_orderings.items():
                if column_name in column_order:
                    output_elements.append(
                        f"{column_name} ({asc_desc_map[order_statement.lower()]})"
                    )
                    found_column = True
                    break

            if not found_column:
                output_elements.append(column_name)

        return "\nErgebnisschema:\n\n" + ", ".join(output_elements)
