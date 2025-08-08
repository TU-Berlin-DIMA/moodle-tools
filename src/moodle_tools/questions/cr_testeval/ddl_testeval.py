import io
import re
import shutil
from contextlib import redirect_stdout
from pathlib import Path
from typing import cast

import duckdb

from .cr_testeval import CRTestCase, CRTestEval


class DDLTestCase(CRTestEval):
    @staticmethod
    def evaluate_testcase(  # noqa: C901, PLR0912, PLR0915
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

        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            con = duckdb.connect(db_working_path, config={"temp_directory": Path.cwd()})

            # Set DB parameters
            con.sql(
                f"""SET memory_limit = '{kwargs.get("question_memlimitmb", 2000)}MB';"""
                """SET threads = 1;"""
            )

            errors = []

            try:
                # Execute student answer
                con.sql(student_answer)
            except duckdb.Error as e:
                errors.append(str(e))
                con.close()

                return "", "", False, errors

            # Execute test code
            statements = [s for s in testcase.testcode.split(";") if s.strip()]

            for statement in statements:
                try:
                    res = con.sql(statement)
                    res.show(max_width=max_width, max_rows=max_rows) if res else print(res)
                except (duckdb.ConstraintException, duckdb.ConversionException) as e:
                    # DuckDB prints the individual constraint implementation in the error message
                    # so we have to filter it out.
                    tut = re.search(r"INSERT INTO (.+?) ", statement)
                    table_under_test = tut.group(1) if tut else "## unknown_table ##"
                    table_flex_enums = additional_info.get("flex_enum_tables", [])

                    match_check = re.search(
                        r"^Constraint Error: CHECK constraint failed on table (.+?) .*$", str(e)
                    )

                    match_enum = re.search(
                        r"^Conversion Error: Could not convert.*$", str(e), re.MULTILINE
                    )

                    if (match_check or match_enum) and table_under_test in table_flex_enums:
                        print(
                            f"CHECK constraint failed or wrong ENUM in "
                            f"table {table_under_test}".lower()
                        )
                    elif match_check:
                        print(f"CHECK constraint failed on table {table_under_test}".lower())
                    else:
                        print(str(e).lower())
                        # errors.append(str(e) if not hide_rest_if_fail else "")
                except duckdb.Error as e:
                    print(str(e).lower())
                    errors.append(str(e) if not hide_rest_if_fail else "")
                except Exception as e:
                    raise (e)

            con.close()

            if db_working_path != ":memory:":
                # Remove the temporary database file after use
                Path(db_working_path).unlink()

            received_result = stdout_capture.getvalue()

            evaluated_result = received_result == testcase.expected_result
            # Restore stdout.

        return received_result, testcase.expected_result, evaluated_result, errors
