from collections.abc import Sequence
from typing import Any

from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text


class MultipleTrueFalseQuestion(Question):
    """General template for a question with multiple true/false questions."""

    QUESTION_TYPE = "mtf"
    XML_TEMPLATE = "multiple_true_false.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        answers: Sequence[dict[str, Any]],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        choices: Sequence[str] = ("True", "False"),
        shuffle_answers: bool = True,
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)
        self.answers = answers
        self.choices = choices
        self.shuffle_answers = shuffle_answers

        for answer in self.answers:
            answer["answer"] = preprocess_text(answer["answer"], **flags)
            answer["choice"] = str(answer["choice"])
            if "feedback" not in answer:
                answer["feedback"] = ""
            else:
                answer["feedback"] = preprocess_text(answer["feedback"], **flags)

    def validate(self) -> list[str]:
        errors = super().validate()
        for answer in self.answers:
            if not answer["feedback"]:
                errors.append(f"The answer {answer['answer']!r} has no feedback.")
            if answer["choice"] not in self.choices:
                errors.append(f"The answer {answer['answer']!r} does not use a valid choice.")
        return errors


class MultipleTrueFalseQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_id: str) -> None:
        super().__init__(question_id, r"(.*?)\n?: (False|Falsch|True|Wahr)", "; ")
