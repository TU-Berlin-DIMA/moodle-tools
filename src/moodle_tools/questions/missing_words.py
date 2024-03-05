import re

from moodle_tools.questions.base import BaseQuestion
from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.utils import optional_text, preprocess_text


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
        **flags,
    ):
        super().__init__(title, **flags)
        self.question = preprocess_text(question, **flags)
        self.options = options
        self.general_feedback = preprocess_text(general_feedback, **flags)
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partial_feedback = preprocess_text(partial_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)

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


class MissingWordsQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_number):
        super().__init__(question_number, r"{(.*?)}", " ")

    def normalize_answers(self, response):
        answers = {}
        if not response:
            return answers
        response += self.separator
        for i, match in enumerate(re.finditer(self.answer_re, response, re.MULTILINE)):
            subquestion_answer = match.group(1)
            subquestion_text = str(i)
            subquestion_answer = self.normalize_response(subquestion_answer.strip())
            answers[subquestion_text] = subquestion_answer
        return answers
