from typing import Any, Sequence
from xml.etree.ElementTree import Element

from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import parse_html, preprocess_text


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
    ):
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
            if not answer["choice"] in self.choices:
                errors.append(f"The answer {answer['answer']!r} does not use a valid choice.")
        return errors

    @staticmethod
    def extract_properties_from_xml(element: Element) -> dict[str, str | Any | None]:
        question_props = Question.extract_properties_from_xml(element)

        question_props.update(
            {
                "scoringmethod": element.find("scoringmethod").find("text").text,
                "shuffle_answers": element.find("shuffleanswers") == "True",
                "answernumbering": element.find("answernumbering").text,
            }
        )

        choices = [
            c.find("responsetext").find("text").text
            for c in sorted(element.findall("column"), key=lambda c: c.get("number"))
        ]
        question_props.update({"choices": choices})

        answers = [
            {
                "answer": parse_html(a.find("optiontext").find("text").text),
                "feedback": parse_html(a.find("feedbacktext").find("text").text or ""),
            }
            for a in sorted(element.findall("row"), key=lambda a: a.get("number"))
        ]

        for w in element.findall("weight"):
            if float(w.find("value").text) == 1.0:
                answers[int(w.get("rownumber")) - 1]["choice"] = choices[
                    int(w.get("columnnumber")) - 1
                ]

        question_props.update({"answers": answers})

        return question_props


class MultipleTrueFalseQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_id: str):
        super().__init__(question_id, r"(.*?)\n?: (False|Falsch|True|Wahr)", "; ")
