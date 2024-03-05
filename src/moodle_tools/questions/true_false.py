from moodle_tools.questions.base import BaseQuestion, BaseQuestionAnalysis
from moodle_tools.utils import optional_text, preprocess_text


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
        **flags,
    ):
        super().__init__(title, **flags)
        self.statement = preprocess_text(statement, **flags)
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


class TrueFalseQuestionAnalysis(BaseQuestionAnalysis):
    pass
