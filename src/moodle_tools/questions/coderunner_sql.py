import sqlite3
from pathlib import Path

import sqlparse

import moodle_tools.isis_database_configurations
from moodle_tools.questions.base import Question, QuestionAnalysis
from moodle_tools.utils import ParsingError, optional_text


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

    def __init__(
        self,
        database,
        question,
        correct_query,
        title,
        testcases,
        check_results=False,
        general_feedback="",
        database_connection=True,
        **flags,
    ) -> None:
        # Todo: Create a way (possible with extra script) to apply moodle-tools to entire folders
        # with '.yaml' files
        super().__init__(title, **flags)
        self.database_name = database
        self.database_path = Path().cwd() / ("../datenbanken/" + database + ".db")
        self.question = question
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

    def execute_change_queries(self, change_queries):
        if ";" not in change_queries:
            raise ParsingError(
                "Additional testcases supplied, but no SQL queries that are terminated with a ';' "
                "symbol were found."
            )
        change_queries_list = change_queries.split(";")
        for change_query in change_queries_list:
            self.cursor.execute(change_query.rstrip().lstrip())

    def fetch_database_result(self):
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

    def generate_testcases(self):
        # Todo: is this requried?
        if self.testcases is None:
            self.testcases = [None]
        for i, testcase in enumerate(self.testcases):
            # A 'change' is used to modify a table to produce different results for a new testcase
            change = ""
            if testcase is not None:
                change = testcase["testcase_changes"].replace("\n ", "\n")
            # Only show the first testcase (Todo: make configurable)
            show_or_hide = "SHOW"
            if i > 0:
                show_or_hide = "HIDE"
            self.testcases_string += (
                '\n<testcase testtype="0" useasexample="0" hiderestiffail="0"'
                ' mark="1.0000000">\n<testcode>\n<text>--Testfall '
                + str(i + 1)
                + "</text>\n</testcode>\n<stdin>\n   <text></text>\n</stdin>\n<expected>\n<text>"
                + self.results[i]
                + "</text>\n</expected>\n<extra>\n   <text><![CDATA["
                + change
                + "]]></text>\n</extra>\n<display>\n<text>"
                + show_or_hide
                + "</text>\n</display>\n</testcase>"
            )

    def generate_xml(self) -> str:
        self.generate_testcases()
        question_xml = f"""\
          <question type="coderunner">
            <name>
              <text>{self.title}</text>
            </name>
            <questiontext format="html">
              <text><![CDATA[{self.question}]]></text>
            </questiontext>
            <generalfeedback format="html">
              <text>{optional_text(self.general_feedback)}</text>
            </generalfeedback>
            <defaultgrade>1</defaultgrade>
            <penalty>0</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
            <coderunnertype>sql</coderunnertype>
            <prototypetype>0</prototypetype>
            <allornothing>1</allornothing>
            <penaltyregime>0</penaltyregime>
            <precheck>0</precheck>
            <hidecheck>0</hidecheck>
            <showsource>0</showsource>
            <answerboxlines>18</answerboxlines>
            <answerboxcolumns>100</answerboxcolumns>
            <answerpreload></answerpreload>
            <globalextra></globalextra>
            <useace></useace>
            <resultcolumns></resultcolumns>
            <template></template>
            <iscombinatortemplate></iscombinatortemplate>
            <allowmultiplestdins></allowmultiplestdins>
            <answer><![CDATA[{self.correct_query}]]></answer>
            <validateonsave>1</validateonsave>
            <testsplitterre></testsplitterre>
            <language></language>
            <acelang></acelang>
            <sandbox></sandbox>
            <grader></grader>
            <cputimelimitsecs></cputimelimitsecs>
            <memlimitmb></memlimitmb>
            <sandboxparams></sandboxparams>
            <templateparams><![CDATA[{self.column_widths_string}]]></templateparams>
            <hoisttemplateparams>0</hoisttemplateparams>
            <templateparamslang>twig</templateparamslang>
            <templateparamsevalpertry>0</templateparamsevalpertry>
            <templateparamsevald><![CDATA[{self.column_widths_string}]]></templateparamsevald>
            <twigall>0</twigall>
            <uiplugin></uiplugin>
            <uiparameters></uiparameters>
            <attachments>0</attachments>
            <attachmentsrequired>0</attachmentsrequired>
            <maxfilesize>10240</maxfilesize>
            <filenamesregex></filenamesregex>
            <filenamesexplain></filenamesexplain>
            <displayfeedback>0</displayfeedback>
            <giveupallowed>0</giveupallowed>
            <prototypeextra></prototypeextra>
            <testcases> {self.testcases_string}
              {moodle_tools.isis_database_configurations.get_database_config(self.database_name)}
            </testcases>
          </question>"""
        return question_xml


class CoderunnerQuestionSQLAnalysis(QuestionAnalysis):
    pass
