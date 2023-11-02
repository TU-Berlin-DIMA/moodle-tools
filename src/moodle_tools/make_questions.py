import argparse
import base64
import functools
import re
import sqlite3
import sys
import textwrap
from pathlib import Path

import markdown
import yaml

import moodle_tools.isis_database_configurations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input file (default: %(default)s)",
        type=argparse.FileType("r", encoding="utf-8"),
        default=sys.stdin,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: %(default)s)",
        type=argparse.FileType("w", encoding="utf-8"),
        default=sys.stdout,
    )
    parser.add_argument(
        "-t",
        "--title",
        help="Default question title (default: %(default)s)",
        type=str,
        default="Knowledge question",
    )
    parser.add_argument(
        "-l", "--lenient", help="Skip strict validation.", action="store_true"
    )
    parser.add_argument(
        "-m",
        "--markdown",
        help="Specify question and answer text in Markdown.",
        action="store_true",
    )
    parser.add_argument(
        "--table-border",
        help="Put a 1 Pixel solid black border around each table cell",
        action="store_true",
    )
    parser.add_argument(
        "--add-question-index",
        help="Extend each question title with an increasing number.",
        action="store_true",
    )
    parser.set_defaults(command=lambda args: parser.print_help())
    subparsers = parser.add_subparsers(title="Possible commands")

    # Generate a true false question
    true_false_question = subparsers.add_parser(
        "true_false", help="Generate Moodle XML for a true/false question."
    )
    true_false_question.set_defaults(
        command=functools.partial(
            generate_moodle_questions, TrueFalseQuestion.generate_xml, TrueFalseQuestion
        )
    )

    # Generate a question with multiple true false questions
    multiple_true_false_question = subparsers.add_parser(
        "multiple_true_false",
        help="Generate Moodle XML for a multiple true/false question.",
    )
    multiple_true_false_question.set_defaults(
        command=functools.partial(
            generate_moodle_questions,
            MultipleTrueFalseQuestion.generate_xml,
            MultipleTrueFalseQuestion,
        )
    )

    # Generate a multiple choice question with a single possible selection
    multiple_choice_question = subparsers.add_parser(
        "multiple_choice",
        help="Generate Moodle XML for a multiple choice question with a single answer.",
    )
    multiple_choice_question.set_defaults(
        command=functools.partial(
            generate_moodle_questions,
            SingleSelectionMultipleChoiceQuestion.generate_xml,
            SingleSelectionMultipleChoiceQuestion,
        )
    )

    # Generate a Cloze question
    cloze_question = subparsers.add_parser(
        "cloze", help="Generate Moodle XML for a Cloze question."
    )
    cloze_question.set_defaults(
        command=functools.partial(
            generate_moodle_questions, ClozeQuestion.generate_xml, ClozeQuestion
        )
    )

    numerical_question = subparsers.add_parser(
        "numerical", help="Generate Moodle XML for a numerical question."
    )
    numerical_question.set_defaults(
        command=functools.partial(
            generate_moodle_questions, NumericalQuestion.generate_xml, NumericalQuestion
        )
    )

    # Generate a missing words question
    missing_words_question = subparsers.add_parser(
        "missing_words", help="Generate Moodle XML for a missing words question."
    )
    missing_words_question.set_defaults(
        command=functools.partial(
            generate_moodle_questions,
            MissingWordsQuestion.generate_xml,
            MissingWordsQuestion,
        )
    )

    # Generate Coderunner Question
    coderunner_question = subparsers.add_parser(
        "coderunner", help="Generate Moodle XML for a coderunner question."
    )
    coderunner_question.set_defaults(
        command=functools.partial(
            generate_moodle_questions,
            CoderunnerQuestionSQL.generate_xml,
            CoderunnerQuestionSQL,
        )
    )

    return parser.parse_args()


def optional_text(text: str | None) -> str:
    return f"<![CDATA[{text}]]>" if text else ""


def inline_image(text: str) -> str:
    """This function detects SVG or PNG images and inlines them."""
    re_img = re.compile(
        '<img alt="[^"]*" src="([^"]*).(png|svg)" (?:style="[^"]*" )?/>'
    )
    for match in re_img.finditer(text):
        filename = f"{match.group(1)}.{match.group(2)}"
        base64_str = base64.b64encode(open(filename, "rb").read()).decode("utf-8")
        img_type = "svg+xml" if match.group(2) == "svg" else match.group(2)
        text = text.replace(filename, f"data:image/{img_type};base64,{base64_str}")

    return text


# It is not possible to assign attribute lists to table elements.
# So we edit the HTML directly.
def table_borders(text):
    global args
    return (
        text.replace(
            "<table>", '<table border="1px solid black" style="margin-bottom: 2ex">'
        )
        if args.table_border
        else text
    )


def convert_markdown(text):
    global args
    return (
        markdown.markdown(text, extensions=["tables", "attr_list"])
        if args.markdown
        else text
    )


def preprocess_text(text):
    return table_borders(inline_image(convert_markdown(text)))


class FormatError(BaseException):
    pass


class BaseQuestion:
    def __init__(self, title):
        # Set the title
        global args
        self.title = title if title else args.title

    def validate(self):
        return []

    def generate_xml(self):
        pass


class TrueFalseQuestion(BaseQuestion):
    """General template for a True/False question."""

    def __init__(
        self,
        statement,
        title="",
        correct_answer=True,
        general_feedback="",
        correct_feedback="",
        wrong_feedback="",
    ):
        super().__init__(title)
        self.statement = preprocess_text(statement)
        self.correct_answer = correct_answer
        self.general_feedback = general_feedback
        self.correct_feedback = correct_feedback
        self.wrong_feedback = wrong_feedback

        # Convert boolean answers to strings
        self.correct_answer, self.wrong_answer = (
            ("true", "false") if self.correct_answer else ("false", "true")
        )

    def validate(self):
        errors = []
        if self.correct_answer == self.wrong_answer:
            # How can this happen?!
            errors.append("Correct answer == wrong answer")
        if not self.general_feedback:
            errors.append("No general feedback")
        if not self.wrong_feedback:
            errors.append("No feedback for wrong answer")
        return errors

    def generate_xml(self):
        question_xml = f"""\
          <question type="truefalse">
            <name>
              <text>{self.title}</text>
            </name>
            <questiontext format="html">
              <text><![CDATA[{self.statement}]]></text>
            </questiontext>
            <generalfeedback format="html">
                <text>{optional_text(self.general_feedback)}</text>
            </generalfeedback>
            <defaultgrade>1.0000000</defaultgrade>
            <penalty>1.0000000</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
            <answer fraction="0" format="moodle_auto_format">
              <text>{self.wrong_answer}</text>
              <feedback format="html">
                <text>{optional_text(self.wrong_feedback)}</text>
              </feedback>
            </answer>
            <answer fraction="100" format="moodle_auto_format">
              <text>{self.correct_answer}</text>
              <feedback format="html">
                <text>{optional_text(self.correct_feedback)}</text>
              </feedback>
            </answer>
          </question>"""
        return question_xml


class SingleSelectionMultipleChoiceQuestion(BaseQuestion):
    """General template for a multiple choice question with a single selection."""

    def __init__(
        self,
        question,
        answers,
        title="",
        general_feedback="",
        correct_feedback="Your answer is correct.",
        partially_correct_feedback="Your answer is partially correct.",
        incorrect_feedback="Your answer is incorrect.",
        shuffle_answers=True,
    ):
        super().__init__(title)
        self.question = preprocess_text(question)
        self.general_feedback = general_feedback
        self.correct_feedback = correct_feedback
        self.partially_correct_feedback = partially_correct_feedback
        self.incorrect_feedback = incorrect_feedback
        self.shuffle_answers = shuffle_answers

        # Transform simple string answers into complete answers
        self.answers = [
            answer if isinstance(answer, dict) else {"answer": answer}
            for answer in answers
        ]

        # Update missing answer points and feedback
        for index, answer in enumerate(self.answers):
            if "points" not in answer:
                answer["points"] = 100 if index == 0 else 0
            if "feedback" not in answer:
                answer["feedback"] = ""

        # Inline images
        for answer in self.answers:
            answer["answer"] = preprocess_text(answer["answer"])

    def validate(self):
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback")
        has_full_points = list(filter(lambda x: x["points"] == 100, self.answers))
        if not has_full_points:
            errors.append("No answer has 100 points")
        for answer in self.answers:
            if not answer["feedback"] and answer["points"] != 100:
                errors.append(f"The answer '{answer['answer']}' has no feedback")
        return errors

    def generate_xml(self):
        def generate_answer(answer):
            return f"""\
            <answer fraction="{answer["points"]}" format="html">
              <text><![CDATA[{answer["answer"]}]]></text>
              <feedback format="html">
                <text>{optional_text(answer["feedback"])}</text>
              </feedback>
            </answer>"""

        newline = "\n"
        question_xml = f"""\
          <question type="multichoice">
            <name>
              <text>{self.title}</text>
            </name>
            <questiontext format="html">
              <text><![CDATA[{self.question}]]></text>
            </questiontext>
            <generalfeedback format="html">
              <text>{optional_text(self.general_feedback)}</text>
            </generalfeedback>
            <defaultgrade>1.0000000</defaultgrade>
            <penalty>0.3333333</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
            <single>true</single>
            <shuffleanswers>
              {"true" if self.shuffle_answers else "false"}
            </shuffleanswers>
            <answernumbering>none</answernumbering>
            <showstandardinstruction>1</showstandardinstruction>
            <correctfeedback format="html">
              <text>{self.correct_feedback}</text>
            </correctfeedback>
            <partiallycorrectfeedback format="html">
              <text>{self.partially_correct_feedback}</text>
            </partiallycorrectfeedback>
            <incorrectfeedback format="html">
              <text>{self.incorrect_feedback}</text>
            </incorrectfeedback>
            <shownumcorrect/>
{newline.join([generate_answer(answer) for answer in self.answers])}
          </question>"""
        return question_xml


class MultipleTrueFalseQuestion(BaseQuestion):
    """General template for a question with multiple true/false questions."""

    def __init__(
        self,
        question,
        answers,
        choices=(True, False),
        title="",
        general_feedback="",
        shuffle_answers=True,
    ):
        super().__init__(title)
        self.question = preprocess_text(question)
        self.answers = answers
        self.choices = choices
        self.general_feedback = general_feedback
        self.shuffle_answers = shuffle_answers

        for answer in self.answers:
            # Update missing feedback
            if "feedback" not in answer:
                answer["feedback"] = ""
            # Inline images
            answer["answer"] = preprocess_text(answer["answer"])

    def validate(self):
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback")
        for answer in self.answers:
            if not answer["feedback"]:
                errors.append(f"The answer '{answer['answer']}' has no feedback")
            if not answer["choice"] in self.choices:
                errors.append(
                    f"The answer '{answer['answer']} does not use a valid choice"
                )
        return errors

    def generate_xml(self):
        def generate_row(index, answer):
            return f"""\
            <row number="{index}">
              <optiontext format="html">
                <text><![CDATA[{answer["answer"]}]]></text>
              </optiontext>
              <feedbacktext format="html">
                <text>{optional_text(answer["feedback"])}</text>
              </feedbacktext>
            </row>"""

        def generate_column(index, choice):
            return f"""\
            <column number="{index}">
              <responsetext format="moodle_auto_format">
                <text>{choice}</text>
              </responsetext>
            </column>"""

        def generate_field(row_index, column_index, answer, choice):
            return f"""\
            <weight rownumber="{row_index}" columnnumber="{column_index}">
              <value>
                 {"1.000" if answer["choice"] == choice else "0.000"}
              </value>
            </weight>"""

        newline = "\n"
        rows = newline.join(
            [
                generate_row(index, answer)
                for index, answer in enumerate(self.answers, start=1)
            ]
        )
        columns = newline.join(
            [
                generate_column(index, choice)
                for index, choice in enumerate(self.choices, start=1)
            ]
        )
        fields = newline.join(
            [
                generate_field(row_index, column_index, answer, choice)
                for row_index, answer in enumerate(self.answers, start=1)
                for column_index, choice in enumerate(self.choices, start=1)
            ]
        )
        question_xml = f"""\
        <question type="mtf">
            <name>
              <text>{self.title}</text>
            </name>
            <questiontext format="html">
              <text><![CDATA[{self.question}]]></text>
            </questiontext>
            <generalfeedback format="html">
              <text>{optional_text(self.general_feedback)}</text>
            </generalfeedback>
            <defaultgrade>1.0000000</defaultgrade>
            <penalty>0.3333333</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
            <scoringmethod><text>subpoints</text></scoringmethod>
            <shuffleanswers>
              {"true" if self.shuffle_answers else "false"}
            </shuffleanswers>
            <numberofrows>{len(self.answers)}</numberofrows>
            <numberofcolumns>{len(self.choices)}</numberofcolumns>
            <answernumbering>none</answernumbering>
{rows}
{columns}
{fields}
          </question>"""
        return question_xml


class ClozeQuestion(BaseQuestion):
    """General template for a Cloze question."""

    def __init__(self, question, feedback="", title=""):
        super().__init__(title)
        self.question = preprocess_text(question)
        self.feedback = preprocess_text(feedback)

    def validate(self):
        errors = []
        if not self.feedback:
            errors.append("No general feedback")
        return errors

    def generate_xml(self):
        question_xml = f"""\
        <question type="cloze">
            <name>
                <text>{self.title}</text>
            </name>
            <questiontext format="html">
                 <text><![CDATA[{self.question}]]></text>
           </questiontext>
            <generalfeedback format="html">
                <text>{optional_text(self.feedback)}</text>
            </generalfeedback>
            <penalty>0.3333333</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
        </question>"""
        return question_xml


class NumericalQuestion(BaseQuestion):
    """General template for a numerical question.

    The YML format is similar to the single selection multiple choice format,
    except that there is no partial and incorrect feedback.
    """

    def __init__(self, question, answers, title="", general_feedback=""):
        super().__init__(title)
        self.question = preprocess_text(question)
        self.general_feedback = general_feedback

        # Transform simple string answers into complete answers
        self.answers = [
            answer if isinstance(answer, dict) else {"answer": answer}
            for answer in answers
        ]

        # Update missing answer points and feedback
        for index, answer in enumerate(self.answers):
            if "points" not in answer:
                answer["points"] = 100 if index == 0 else 0
            if "feedback" not in answer:
                answer["feedback"] = ""
            if "tolerance" not in answer:
                answer["tolerance"] = 0

    def validate(self):
        # noinspection PyTypeChecker
        return SingleSelectionMultipleChoiceQuestion.validate(self)

    def generate_xml(self):
        def generate_answer(answer):
            return f"""\
            <answer fraction="{answer["points"]}" format="html">
              <text>{answer["answer"]}</text>
              <feedback format="html">
                <text>{optional_text(answer["feedback"])}</text>
              </feedback>
              <tolerance>{answer["tolerance"]}</tolerance>
            </answer>"""

        newline = "\n"
        question_xml = f"""\
          <question type="numerical">
            <name>
              <text>{self.title}</text>
            </name>
            <questiontext format="html">
              <text><![CDATA[{self.question}]]></text>
            </questiontext>
            <generalfeedback format="html">
              <text>{optional_text(self.general_feedback)}</text>
            </generalfeedback>
            <defaultgrade>1.0000000</defaultgrade>
            <penalty>0.3333333</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
{newline.join([generate_answer(answer) for answer in self.answers])}
            <unitgradingtype>0</unitgradingtype>
            <unitpenalty>1.000000</unitpenalty>
            <showunits>3</showunits>
            <unitsleft>0</unitsleft>
          </question>"""
        return question_xml


class MissingWordsQuestion(BaseQuestion):
    def __init__(
        self,
        question,
        options,
        title="",
        general_feedback="",
        correct_feedback="",
        partial_feedback="",
        incorrect_feedback="",
    ):
        super().__init__(title)
        self.question = preprocess_text(question)
        self.options = options
        self.general_feedback = preprocess_text(general_feedback)
        self.correct_feedback = preprocess_text(correct_feedback)
        self.partial_feedback = preprocess_text(partial_feedback)
        self.incorrect_feedback = preprocess_text(incorrect_feedback)

    def validate(self):
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback")
        if not self.correct_feedback:
            errors.append("No feedback for correct answer")
        if not self.partial_feedback:
            errors.append("No feedback for partially correct answer")
        if not self.incorrect_feedback:
            errors.append("No feedback for incorrect answer")
        return errors

    def generate_xml(self):
        def generate_option(option):
            return f"""\
            <selectoption>
                <text>{option["answer"]}</text>
                <group>{option["group"]}</group>
            </selectoption>"""

        newline = "\n"
        question_xml = f"""\
          <question type="gapselect">
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
            <penalty>0.3333333</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
            <shuffleanswers>1</shuffleanswers>
            <correctfeedback format="html">
              <text>{optional_text(self.correct_feedback)}</text>
            </correctfeedback>
            <partiallycorrectfeedback format="html">
              <text>{optional_text(self.partial_feedback)}</text>
            </partiallycorrectfeedback>
            <incorrectfeedback format="html">
              <text>{optional_text(self.incorrect_feedback)}</text>
            </incorrectfeedback>
            <shownumcorrect/>
{newline.join([generate_option(option) for option in self.options])}
          </question>"""
        return question_xml


class CoderunnerQuestionSQL(BaseQuestion):
    """General template for a coderunner question. Currently, we are limited to SQL queries.
    The YML format is the following:
        (optional) title: Title of the question
        database: Name of the ISIS database (for example "eshop" or "uni")
        question: The coderunner question displayed to students
        correct_query: The SQL string that, when executed, leads to the correct result
        (optional) additional_testcases:
                changes: A change applied between testcases to adapt the data in the tables to a new testcase.
                         (NOTE: to run the query without changes, add 'additional_testcases: ""' as the first additional_change)
                (optional) new_result: The result of an additional testcase (right now the correct result of the SQL query)
        (optional) check_results: Whether the provided query is run and the result is compared against the manually provided.
        (optional) general_feedback: Feedback that is provided when an answer to a coderunner question is submitted
        (optional) database_connection: If this bool flag is set (default), you must execute moodle_tools in the GIT repo
                                        'klausuraufgaben' or spoof it. If this bool flag is false, we do not attempt to
                                        create a database connection.
    """

    def __init__(self, database, question, correct_query, title="", additional_testcases="", check_results=False, general_feedback="", database_connection=True):
        # Todo: Create a way (possible with extra script) to apply moodle-tools to entire folder with '.yml' files
        super().__init__(title)
        self.database_name = database
        self.database_path = Path().cwd() / ("sql-aufgaben/datenbanken/" + database + ".db")
        self.question = question
        correct_query = correct_query.replace(';\n', ';')
        if correct_query[-1] != ';':
            raise Exception("SQL Queries must end with a ';' symbol. But the last symbol was: " + correct_query[-1])
        self.correct_query = sqlparse.format(correct_query.replace('\n ', '\n'), reindent=True, keyword_case='upper')
        if check_results and not database_connection:
            raise Exception("Checking results requires a database connection. However, you set database_connection to false.")
        if database_connection:
            if Path().cwd().name != "klausurfragen" or not (Path().cwd() / "dbs").exists():
                raise Exception("moodle-tools is not executed in the correct folder. The correct repository should be "
                              "'klausuraufgaben' and it should contain a folder called 'dbs' that contains the required"
                              "'.db' files to create Coderunner questions.")
            if not self.database_path.exists():
                raise Exception("Provided database path did not exsist: " + str(self.database_path))
            self.con = sqlite3.connect(str(self.database_path), timeout=5)
            self.cursor = self.con.cursor()
        # Execute additional test cases and get results.
        self.column_widths_string = ""
        self.additional_testcases = additional_testcases
        self.testcases_string = ""
        self.general_feedback = general_feedback
        self.results = []
        # Add additional results if present
        if additional_testcases is None:
            self.results.append(self.fetch_database_result())
        else:
            for additional_testcase in self.additional_testcases:
                if "new_result" not in additional_testcase:
                    # reset connection
                    self.con = sqlite3.connect(str(self.database_path), timeout=5)
                    self.cursor = self.con.cursor()
                    # If a user mistypes 'new_result' or names it differently, we simply generate a result.
                    if not database_connection:
                        raise Exception("You must provide a result, if you set database_connection to false, otherwise we"
                                        "cannot automatically fetch the result from the database.")
                    # need to reset database
                    if additional_testcase["changes"] != "":
                        self.execute_change_queries(additional_testcase["changes"])
                    self.results.append(self.fetch_database_result())
                else:
                    # reset connection
                    self.con = sqlite3.connect(str(self.database_path), timeout=5)
                    self.cursor = self.con.cursor()
                    self.results.append(additional_testcase["new_result"].replace('\n ', '\n'))
                    if check_results:
                        if additional_testcase["changes"] != "":
                            self.execute_change_queries(additional_testcase["changes"])
                        correct_query_result = self.fetch_database_result()
                        if correct_query_result != self.results[-1]:
                            raise Exception("Provided result: " + self.results[-1] + "did not match the result"
                                            "returned by executing the provided 'correct_query': " + correct_query_result)
        self.con.close()

    def execute_change_queries(self, change_queries):
        if ';' not in change_queries:
            raise Exception("Additional testcases supplied, but no SQL queries that are "
                            "terminated with a ';' symbol were found.")
        change_queries_list = change_queries.split(';')
        for change_query in change_queries_list:
            self.cursor.execute(change_query.rstrip().lstrip())

    def fetch_database_result(self):
        self.cursor.execute(self.correct_query)
        name_string = ""
        rows = self.cursor.fetchall()
        column_names = [description[0] for description in self.cursor.description]
        column_lengths = [max(len(name), max(len(str(row[i])) for row in rows)) for i, name in enumerate(column_names)]
        for i, name in enumerate(column_names):
            name_string += name + ((column_lengths[i] - len(name)) * ' ') + "  "
        name_string += '\n'
        for length in column_lengths:
            name_string += length * '-' + "  "
        name_string += '\n'
        for row in rows:
            for i, value in enumerate(row):
                value = str(value)
                name_string += str(value) + ((column_lengths[i] - len(value)) * ' ') + "  "
            name_string += '\n'
        return name_string

    def validate(self):
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
        if self.additional_testcases is None:
            self.additional_testcases = [None]
        for i, testcase in enumerate(self.additional_testcases):
            # A 'change' is used to change the data in tables to produce different results for a new testcase.
            change = ""
            if testcase is not None:
                change = testcase["changes"].replace('\n ', '\n')
            # Only show the first testcase (Todo: make configurable)
            show_or_hide = 'SHOW'
            if i > 0:
                show_or_hide = 'HIDE'
            self.testcases_string += '\n<testcase testtype="0" useasexample="0" hiderestiffail="0" mark="1.0000000">\n' \
                                '<testcode>\n' \
                                '<text>--Testfall '+str(i+1)+'</text>\n' \
                                '</testcode>\n' \
                                '<stdin>\n' \
                                '   <text></text>\n' \
                                '</stdin>\n' \
                                '<expected>\n' \
                                '<text>' + self.results[i] + \
                                '</text>\n' \
                                '</expected>\n' \
                                '<extra>\n' \
                                '   <text><![CDATA[' + change + ']]></text>\n' \
                                '</extra>\n' \
                                '<display>\n' \
                                '<text>' + show_or_hide + '</text>\n' \
                                '</display>\n' \
                                '</testcase>'


    def generate_xml(self):
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


def load_questions(question_class, strict_validation, yaml_files):
    """Iterate over the YAML files and generate a question for each YAML document.

    If `strict_validation` is set, filter those questions that contain missing optional
    information (e.g., feedback).
    """
    bullet = "\n- "

    for properties in yaml_files:
        question = question_class(**properties)
        if strict_validation:
            errors = question.validate()
            if errors:
                message = (
                    "---\nThe following question did not pass strict validation:\n"
                    f"{yaml.safe_dump(properties)}"
                    f"Errors:\n- {bullet.join(errors)}"
                )
                print(message, file=sys.stderr)
                continue
        yield question


def generate_moodle_questions(generate_question_xml, question_class, args):
    """Generate an XML document containing Moodle questions.

    The type of Moodle question is defined by `question_type`.
    The actual question is defined by `question_class`.
    """
    # Create question instances from a list of YAML documents.
    questions = [
        question
        for question in load_questions(
            question_class, not args.lenient, yaml.safe_load_all(args.input)
        )
    ]

    # Add question index to title
    if args.add_question_index:
        for index, question in enumerate(questions, 1):
            question.title = f"{question.title} ({index})"

    # Newline constant to make the "\n".join(...) work below.
    newline = "\n"
    # Generate Moodle XML
    xml = f"""\
    <?xml version="1.0" encoding="UTF-8"?>
    <quiz>
{newline.join([generate_question_xml(question) for question in questions])}
    </quiz>
    """
    xml = textwrap.dedent(xml)
    print(xml, file=args.output)


def main() -> None:
    args = parse_args()
    args.command(args)


if __name__ == "__main__":
    main()
