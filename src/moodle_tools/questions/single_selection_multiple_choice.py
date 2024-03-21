from typing import Any

from moodle_tools.questions.base import Question
from moodle_tools.utils import optional_text, preprocess_text


class SingleSelectionMultipleChoiceQuestion(Question):
    """General template for a multiple choice question with a single selection."""

    def __init__(
        self,
        question: str,
        title: str,
        answers: str,
        general_feedback: str = "",
        correct_feedback: str = "Your answer is correct.",
        partially_correct_feedback: str = "Your answer is partially correct.",
        incorrect_feedback: str = "Your answer is incorrect.",
        shuffle_answers: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(question, title, **flags)
        self.general_feedback = preprocess_text(general_feedback, **flags)
        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partially_correct_feedback = preprocess_text(partially_correct_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)
        self.shuffle_answers = shuffle_answers

        # Transform simple string answers into complete answers
        self.answers: list[dict[str, Any]] = [
            answer if isinstance(answer, dict) else {"answer": answer} for answer in answers
        ]

        # Update missing answer points and feedback
        for i, answer in enumerate(self.answers):
            if "points" not in answer:
                answer["points"] = 100 if i == 0 else 0
            if "feedback" not in answer:
                answer["feedback"] = ""

        # Inline images
        for answer in self.answers:
            answer["answer"] = preprocess_text(answer["answer"], **flags)

    def validate(self) -> list[str]:
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback.")
        num_full_points: int = len(list(filter(lambda x: x["points"] == 100, self.answers)))
        if num_full_points != 1:
            errors.append("Exactly one answer must have 100 points.")
        for answer in self.answers:
            if not answer["feedback"] and answer["points"] != 100:
                errors.append(f"The incorrect answer '{answer['answer']}' has no feedback.")
        return errors

    def generate_xml(self) -> str:
        def generate_answer(answer: dict[str, Any]) -> str:
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
              <text>{optional_text(self.correct_feedback)}</text>
            </correctfeedback>
            <partiallycorrectfeedback format="html">
              <text>{optional_text(self.partially_correct_feedback)}</text>
            </partiallycorrectfeedback>
            <incorrectfeedback format="html">
              <text>{optional_text(self.incorrect_feedback)}</text>
            </incorrectfeedback>
            <shownumcorrect/>
              {newline.join([generate_answer(answer) for answer in self.answers])}
          </question>"""
        return question_xml
