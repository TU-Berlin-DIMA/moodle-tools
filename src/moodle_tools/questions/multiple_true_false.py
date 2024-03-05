from moodle_tools.questions.base import BaseQuestion
from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.utils import optional_text, preprocess_text


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
        **flags,
    ):
        super().__init__(title, **flags)
        self.question = preprocess_text(question, **flags)
        self.answers = answers
        self.choices = choices
        self.general_feedback = general_feedback
        self.shuffle_answers = shuffle_answers

        for answer in self.answers:
            # Update missing feedback
            if "feedback" not in answer:
                answer["feedback"] = ""
            # Inline images
            answer["answer"] = preprocess_text(answer["answer"], **flags)

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
        rows = newline.join([generate_row(index, answer) for index, answer in enumerate(self.answers, start=1)])
        columns = newline.join([generate_column(index, choice) for index, choice in enumerate(self.choices, start=1)])
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


class MultipleTrueFalseQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_number):
        super().__init__(question_number, r"(.*?)\n?: (False|Falsch|True|Wahr)", "; ")
