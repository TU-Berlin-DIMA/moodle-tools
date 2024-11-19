from typing import Any
from xml.etree.ElementTree import Element

from loguru import logger

from moodle_tools import ParsingError
from moodle_tools.questions.question import Question, QuestionAnalysis
from moodle_tools.utils import parse_html, preprocess_text


class NumericalQuestion(Question):
    """General template for a numerical question."""

    QUESTION_TYPE = "numerical"
    XML_TEMPLATE = "numerical.xml.j2"

    def __init__(
        self,
        question: str,
        title: str,
        answers: list[str],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        **flags: bool,
    ):
        super().__init__(question, title, category, grade, general_feedback, **flags)

        # Transform simple string answers into complete answers
        self.answers: list[dict[str, Any]] = [
            answer if isinstance(answer, dict) else {"answer": answer} for answer in answers
        ]

        # Update points if not provided or raise an error if they are not consistent
        # TODO: Create corner case test for this functionality
        all_points_specified = len(
            list(filter(lambda x: "points" in x and 0 <= x["points"] <= 100, self.answers))
        ) == len(self.answers)
        if all_points_specified and 100 not in [answer["points"] for answer in self.answers]:
            raise ParsingError("At least one answer must have 100 points if you specify points.")
        if not all_points_specified:
            logger.debug("Not all answer points specified, first answer is assumed to be correct.")
            for i, answer in enumerate(self.answers):
                if "points" not in answer:
                    answer["points"] = 100 if i == 0 else 0
                else:
                    raise ParsingError("All or no answers must have points specified.")
                if "feedback" not in answer:
                    answer["feedback"] = ""
                else:
                    answer["feedback"] = preprocess_text(answer["feedback"], **flags)

    def validate(self) -> list[str]:
        errors = super().validate()
        num_full_points: int = len(list(filter(lambda x: x["points"] == 100, self.answers)))
        if num_full_points == 0:
            errors.append("At least one answer must have 100 points.")
        for answer in self.answers:
            if "feedback" not in answer and answer["points"] != 100:
                errors.append(f"The incorrect answer '{answer['answer']}' has no feedback.")
        return errors

    @staticmethod
    def extract_properties_from_xml(element: Element) -> dict[str, str]:
        question_props = Question.extract_properties_from_xml(element)
        for el in [e for e in element.findall("*") if e.tag in ["shuffleanswers", "usecase"]]:
            match el.tag:
                case "shuffleanswers":
                    question_props.update({"shuffle_answers": el.text.lower() == "true"})
                case "usecase":
                    question_props.update({"answer_case_sensitive": el.text.lower() == "1"})

        answers = []
        for answer_xml in element.findall("answer"):
            answer_text = answer_xml.find("text").text

            fraction = answer_xml.get("fraction")

            answer = {
                "answer": (
                    parse_html(answer_text)
                    if not answer_text.replace(".", "", 1).isdigit()
                    else float(answer_text) if "." in answer_text else int(answer_text)
                ),
                "points": float(fraction) if "." in fraction else int(fraction),
                "feedback": parse_html(answer_xml.find("feedback").find("text").text or ""),
            }

            if answer_xml.find("tolerance") is not None:
                answer.update({"tolerance": float(answer_xml.find("tolerance").text)})

            other_tags = {
                e.tag: e.text
                for e in answer_xml
                if e.tag not in ["text", "feedback", "file", "tolerance"]
            }

            answers.append(answer | other_tags)

            Question.handle_file_used_in_text(answer, "answer", question_props["files"])
            Question.handle_file_used_in_text(answer, "feedback", question_props["files"])

        question_props.update({"answers": answers})

        return question_props


class NumericalQuestionAnalysis(QuestionAnalysis):
    pass
