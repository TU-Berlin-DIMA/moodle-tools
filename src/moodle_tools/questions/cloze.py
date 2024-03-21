from moodle_tools.questions.base import Question
from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.utils import optional_text, preprocess_text


class ClozeQuestion(Question):
    """General template for a Cloze question."""

    def __init__(self, question: str, title: str, feedback: str = "", **flags: bool) -> None:
        super().__init__(question, title, **flags)
        self.feedback = preprocess_text(feedback, **flags)

    def validate(self) -> list[str]:
        errors = []
        if not self.feedback:
            errors.append("No general feedback")
        return errors

    def generate_xml(self) -> str:
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


class ClozeQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_number: int | str) -> None:
        super().__init__(question_number, r"(.*?): (.*?)", "; ")
