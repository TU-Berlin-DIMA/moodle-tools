#    Copyright 2022 Technische Universität Berlin
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import textwrap
import yaml
import argparse
import sys
import functools
import re
import base64
import markdown


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input file (default stdin).", type=open, default=sys.stdin)
    parser.add_argument("-o", "--output", help="Output file (default stdout).",
                        type=lambda filename: open(filename, "w"), default=sys.stdout)
    parser.add_argument("-t", "--title", help="Default question title (default: Knowledge question).", type=str,
                        default="Knowledge question")
    parser.add_argument("-l", "--lenient", help="Skip strict validation.", action="store_true")
    parser.add_argument("-m", "--markdown", help="Specify question and answer text in Markdown.", action="store_true")
    parser.add_argument("--table-border", help="Put a 1 Pixel solid black border around each table cell",
                        action="store_true")
    parser.add_argument("--add-question-index", help="Extend each question title with an increasing number.",
                        action="store_true")
    parser.set_defaults(command=lambda args: parser.print_help())
    subparsers = parser.add_subparsers(title="Possible commands")

    # Generate a true false question
    true_false_question = subparsers.add_parser("true_false",
                                                help="Generate Moodle XML for a true/false question.")
    true_false_question.set_defaults(
        command=functools.partial(generate_moodle_questions, TrueFalseQuestion.generate_xml, TrueFalseQuestion))

    # Generate a question with multiple true false questions
    multiple_true_false_question = subparsers.add_parser("multiple_true_false",
                                                         help="Generate Moodle XML for a multiple true/false question.")
    multiple_true_false_question.set_defaults(
        command=functools.partial(generate_moodle_questions, MultipleTrueFalseQuestion.generate_xml,
                                  MultipleTrueFalseQuestion))

    # Generate a multiple choice question with a single possible selection
    multiple_choice_question = subparsers.add_parser("multiple_choice",
                                                     help="Generate Moodle XML for a multiple choice question with a single answer.")
    multiple_choice_question.set_defaults(
        command=functools.partial(generate_moodle_questions, SingleSelectionMultipleChoiceQuestion.generate_xml,
                                  SingleSelectionMultipleChoiceQuestion))

    # Generate a Cloze question
    cloze_question = subparsers.add_parser("cloze", help="Generate Moodle XML for a Cloze question.")
    cloze_question.set_defaults(
        command=functools.partial(generate_moodle_questions, ClozeQuestion.generate_xml, ClozeQuestion))

    args = parser.parse_args()
    # print(args, file=sys.stderr)
    return args


def optional_text(text):
    return f"<![CDATA[{text}]]>" if text else ""


def inline_image(text):
    """This function detects SVG or PNG images and inlines them."""

    re_img = re.compile('<img alt="[^"]*" src="([^"]*).(png|svg)" \/>')
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
    return text.replace("<table>", '<table border="1px solid black" style="margin-bottom: 2ex">') if args.table_border else text


def convert_markdown(text):
    global args
    return markdown.markdown(text, extensions=['tables', 'attr_list']) if args.markdown else text


def preprocess_text(text):
    return table_borders(inline_image(convert_markdown(text)))


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

    def __init__(self, statement, title="", correct_answer=True, general_feedback="",
                 correct_feedback="", wrong_feedback=""):
        super().__init__(title)
        self.statement = preprocess_text(statement)
        self.correct_answer = correct_answer
        self.general_feedback = general_feedback
        self.correct_feedback = correct_feedback
        self.wrong_feedback = wrong_feedback

        # Convert boolean answers to strings
        self.correct_answer, self.wrong_answer = ("true", "false") if self.correct_answer else ("false", "true")

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

    def __init__(self, question, answers, title="", general_feedback="", correct_feedback="Your answer is correct.",
                 partially_correct_feedback="Your answer is partially correct.",
                 incorrect_feedback="Your answer is incorrect."):
        super().__init__(title)
        self.question = preprocess_text(question)
        self.general_feedback = general_feedback
        self.correct_feedback = correct_feedback
        self.partially_correct_feedback = partially_correct_feedback
        self.incorrect_feedback = incorrect_feedback

        # Transform simple string answers into complete answers
        self.answers = [answer if type(answer) == dict else {"answer": answer} for answer in answers]

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
            <shuffleanswers>true</shuffleanswers>
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

    def __init__(self, question, answers, choices=(True, False), title="", general_feedback=""):
        super().__init__(title)
        self.question = preprocess_text(question)
        self.answers = answers
        self.choices = choices
        self.general_feedback = general_feedback

        # Update missing feedback
        for index, answer in enumerate(self.answers):
            if "feedback" not in answer:
                answer["feedback"] = ""

        # Inline images
        for answer in self.answers:
            answer["answer"] = preprocess_text(answer["answer"])

    def validate(self):
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback")
        for answer in self.answers:
            if not answer["feedback"]:
                errors.append(f"The answer '{answer['answer']}' has no feedback")
            if not answer["choice"] in self.choices:
                errors.append(f"The answer '{answer['answer']} does not use a valid choice")
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
            <shuffleanswers>true</shuffleanswers>
            <numberofrows>{len(self.answers)}</numberofrows>
            <numberofcolumns>{len(self.choices)}</numberofcolumns>
            <answernumbering>none</answernumbering>
{newline.join([generate_row(index, answer) for index, answer in enumerate(self.answers, start=1)])}
{newline.join([generate_column(index, choice) for index, choice in enumerate(self.choices, start=1)])}
{newline.join([generate_field(row_index, column_index, answer, choice) for row_index, answer in enumerate(self.answers, start=1) for column_index, choice in enumerate(self.choices, start=1)])}
          </question>"""
        return question_xml


class ClozeQuestion(BaseQuestion):
    """General template for a Cloze question."""

    def __init__(self, question, title=""):
        super().__init__(title)
        self.question = preprocess_text(question)

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
                <text></text>
            </generalfeedback>
            <penalty>0.3333333</penalty>
            <hidden>0</hidden>
            <idnumber></idnumber>
        </question>"""
        return question_xml


def load_questions(question_class, strict_validation, yaml_documents):
    """
    Iterate over the YAML documents and generate a question for each YAML document.

    If `strict_validation` is set, filter those questions that contain missing optional information (e.g., feedback).
    """

    bullet = "\n- "

    for properties in yaml_documents:
        question = question_class(**properties)
        if strict_validation:
            errors = question.validate()
            if errors:
                message = f"""---\

The following question did not pass strict validation:

{yaml.safe_dump(properties)}

Errors:
- {bullet.join(errors)}
"""
                print(message, file=sys.stderr)
                continue
        yield question


def generate_moodle_questions(generate_question_xml, question_class, args):
    """Generate an XML document containing Moodle questions.
    The type of Moodle question is defined by `question_type`.
    The actual question is defined by `question_class`."""

    # Create question instances from a list of YAML documents.
    questions = [question for question in load_questions(question_class, not args.lenient, yaml.safe_load_all(args.input))]

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


if __name__ == '__main__':
    args = parse_args()
    args.command(args)
