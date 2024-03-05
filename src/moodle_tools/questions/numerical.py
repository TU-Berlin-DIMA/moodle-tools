from moodle_tools.questions.base import BaseQuestion, BaseQuestionAnalysis
from moodle_tools.questions.single_selection_multiple_choice import (
    SingleSelectionMultipleChoiceQuestion,
)
from moodle_tools.utils import optional_text, preprocess_text


class NumericalQuestion(BaseQuestion):
    """General template for a numerical question.

    The YML format is similar to the single selection multiple choice format,
    except that there is no partial and incorrect feedback.
    """

    def __init__(self, question, answers, title="", general_feedback="", **flags):
        super().__init__(title, **flags)
        self.question = preprocess_text(question, **flags)
        self.general_feedback = general_feedback

        # Transform simple string answers into complete answers
        self.answers = [answer if isinstance(answer, dict) else {"answer": answer} for answer in answers]

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


# TODO: Resolve naming mismatch between analysis.NumericQuestion and questions/NumericalQuestion.py
class NumericalQuestionAnalysis(BaseQuestionAnalysis):
    pass
