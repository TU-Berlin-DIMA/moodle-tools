from typing import Any, Sequence

from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text


class MultipleTrueFalseQuestion(Question):
    """General template for a question with multiple true/false questions."""

    QUESTION_TYPE = "mtf"
    TEMPLATE = "multiple_true_false.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        answers: Sequence[dict[str, Any]],
        category: str | None = None,
        choices: Sequence[str] = ("True", "False"),
        general_feedback: str = "",
        shuffle_answers: bool = True,
        **flags: bool,
    ):
        super().__init__(question, title, category, **flags)
        self.answers = answers
        self.choices = choices
        self.general_feedback = preprocess_text(general_feedback, **flags)
        self.shuffle_answers = shuffle_answers

        for answer in self.answers:
            # Update missing feedback
            if "feedback" not in answer:
                answer["feedback"] = ""
            # Inline images
            answer["answer"] = preprocess_text(answer["answer"], **flags)
            answer["choice"] = str(answer["choice"])

    def validate(self) -> list[str]:
        errors = []
        if not self.general_feedback:
            errors.append("No general feedback")
        for answer in self.answers:
            if not answer["feedback"]:
                errors.append(f"The answer {answer['answer']!r} has no feedback")
            if not answer["choice"] in self.choices:
                errors.append(f"The answer {answer['answer']!r} does not use a valid choice")
        return errors


class MultipleTrueFalseQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_number: int | str):
        super().__init__(question_number, r"(.*?)\n?: (False|Falsch|True|Wahr)", "; ")
