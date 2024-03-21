from moodle_tools.questions.base import Question, QuestionAnalysis
from moodle_tools.utils import optional_text, preprocess_text


class TrueFalseQuestion(Question):
    """General template for a True/False question."""

    def __init__(
        self,
        question: str,
        title: str,
        correct_answer: bool = True,
        general_feedback: str = "",
        correct_feedback: str = "",
        wrong_feedback: str = "",
        **flags: bool,
    ):
        super().__init__(question, title, **flags)
        self.general_feedback = preprocess_text(general_feedback, **flags)
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.wrong_feedback = preprocess_text(wrong_feedback, **flags)

        # Convert boolean answers to strings
        self.correct_answer, self.wrong_answer = (
            ("true", "false") if correct_answer else ("false", "true")
        )

    def validate(self) -> list[str]:
        errors = []
        if self.correct_answer == self.wrong_answer:
            # How can this happen?!
            errors.append("Correct answer == wrong answer")
        if not self.general_feedback:
            errors.append("No general feedback")
        if not self.wrong_feedback:
            errors.append("No feedback for wrong answer")
        return errors

    def generate_xml(self) -> str:
        question_xml = f"""\
          <question type="truefalse">
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


class TrueFalseQuestionAnalysis(QuestionAnalysis):
    pass
