from moodle_tools.questions.base import BaseQuestion
from moodle_tools.utils import optional_text, preprocess_text


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
        **flags,
    ):
        super().__init__(title, **flags)
        self.question = preprocess_text(question, **flags)
        self.general_feedback = general_feedback
        self.correct_feedback = correct_feedback
        self.partially_correct_feedback = partially_correct_feedback
        self.incorrect_feedback = incorrect_feedback
        self.shuffle_answers = shuffle_answers

        # Transform simple string answers into complete answers
        self.answers = [answer if isinstance(answer, dict) else {"answer": answer} for answer in answers]

        # Update missing answer points and feedback
        for index, answer in enumerate(self.answers):
            if "points" not in answer:
                answer["points"] = 100 if index == 0 else 0
            if "feedback" not in answer:
                answer["feedback"] = ""

        # Inline images
        for answer in self.answers:
            answer["answer"] = preprocess_text(answer["answer"], **flags)

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
