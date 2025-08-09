import io
import json
import shutil
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import duckdb

from .cr_testeval import CRTestCase, CRTestEval


@dataclass
class DQLTestResult:
    test_name: str
    received: str
    expected: str
    awarded: float | None
    max_points: float | None
    is_correct: bool
    is_hidden: bool

    @property
    def awarded_str(self) -> str:
        """Return awarded points as a formatted string."""
        return (
            "↓↓↓"
            if self.awarded is None
            else f"{self.awarded:.3f}"
            if cast("float", self.max_points) > 0.005
            else "–––"  # noqa: RUF001
        )

    @property
    def max_points_str(self) -> str:
        """Return max points as a formatted string."""
        return (
            "↓↓↓"
            if self.max_points is None
            else f"{self.max_points:.3f}"
            if self.max_points > 0.005
            else "–––"  # noqa: RUF001
        )

    @staticmethod
    def get_header() -> list[str]:
        """Return a header string for the test result."""
        return [
            "Testfall",
            "Erhalten",
            "Erwartet",
            "Punkte",
            "max. Punkte",
            "iscorrect",
            "ishidden",
        ]

    def to_list(self) -> list[str | float | bool]:
        """Convert the test result to a list for display."""
        return [
            self.test_name,
            self.received,
            self.expected,
            self.awarded_str,
            self.max_points_str,
            self.is_correct,
            self.is_hidden,
        ]


class DQLTestCase(CRTestEval):
    @staticmethod
    def evaluate_testcase(  # noqa: PLR0911
        testcase: CRTestCase,
        student_answer: str,
        hide_rest_if_fail: bool,
        **kwargs: str | int,
    ) -> tuple[str, str, bool, list[str]]:
        db_path = cast("str", kwargs.get("db_working"))
        max_width = cast("int", kwargs.get("max_width"))
        max_rows = cast("int", kwargs.get("max_rows"))

        if db_path == ":memory:":
            db_working_path = db_path  # Use in-memory database
        else:
            db_working_path = f"{db_path}.copy"
            shutil.copyfile(db_path, db_working_path)  # Copy clean writeable db file

        additional_info = testcase.additional_info if testcase.additional_info else {}
        if "keyword_present" in additional_info:
            keyword = additional_info["keyword_present"].lower()
            if keyword in student_answer.lower():
                actual_response = f"Keyword '{keyword}' is present.".lower()
                return actual_response, testcase.expected_result, True, []
            actual_response = f"Keyword '{keyword}' not found in student answer.".lower()
            return actual_response, testcase.expected_result, False, []
        if "required_tables" in additional_info:
            required_tables = additional_info["required_tables"]

            # Connect to the database and explain the query
            con = duckdb.connect(db_working_path, config={"temp_directory": Path.cwd()})
            plan_json = DQLTestCase.explain_query(con, student_answer)
            con.close()

            if not plan_json:
                return "", "", False, ["Failed to retrieve query plan."]

            base_tables = DQLTestCase.extract_base_tables_from_json_plan(plan_json)

            missing_tables = [table for table in required_tables if table not in base_tables]
            if missing_tables:
                actual_response = "Missing required tables."
                return actual_response, testcase.expected_result, False, []
            actual_response = "All required tables are present."
            return actual_response, testcase.expected_result, True, []

        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            con = duckdb.connect(db_working_path, config={"temp_directory": Path.cwd()})

            # Set DB parameters
            con.sql(
                f"""SET memory_limit = '{kwargs.get("question_memlimitmb", 2000)}MB';"""
                """SET threads = 1;"""
            )

            # Execute database modification
            con.sql(testcase.testcode)

            errors = []

            try:
                # Execute student answer
                res = con.sql(student_answer)
                res.show(max_width=max_width, max_rows=max_rows) if res else print(res)
                con.close()
            except duckdb.Error as e:
                errors.append(str(e))
                con.close()

                return "", "", False, errors

        Path(db_working_path).unlink(missing_ok=True)  # Clean up the copied database file

        actual_response = stdout_capture.getvalue().strip()
        is_correct = actual_response == testcase.expected_result

        return actual_response, testcase.expected_result, is_correct, errors

    @staticmethod
    def extract_base_tables_from_json_plan(plan_json: dict[str, Any]) -> set[str]:
        """Recursively traverse DuckDB JSON query plan to extract base tables.

        Look for operators like 'SEQ_SCAN' or 'INDEX_SCAN' and grab the table name.

        Args:
            plan_json (dict[str, Any]): The JSON representation of the query plan.

        Returns:
            set[str]: A set of base table names used in the query.
        """
        base_tables = set()

        def traverse(node: dict[str, Any]) -> None:
            op_name = str(node.get("name")).strip()
            if op_name in ("SEQ_SCAN", "INDEX_SCAN", "TABLE_SCAN"):
                table_name = node.get("extra_info", {}).get("Table", "")
                if table_name:
                    base_tables.add(table_name)
            else:
                # Recurse into children nodes
                for child in node.get("children", []):
                    traverse(child)

        traverse(plan_json)
        return base_tables

    @staticmethod
    def explain_query(con: duckdb.DuckDBPyConnection, query: str) -> dict[str, Any] | None:
        try:
            plan_json_str = con.execute(f"EXPLAIN (FORMAT JSON) {query}").fetchone()[1]  # type: ignore
            return json.loads(plan_json_str)[0]  # type: ignore
        except Exception as e:
            print(f"[ERROR] Failed to EXPLAIN query: {e}")
            return None
