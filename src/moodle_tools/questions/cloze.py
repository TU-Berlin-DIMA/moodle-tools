import re
import sys
from typing import Any, TypeVar

from loguru import logger

from moodle_tools.enums import ClozeTypeEnum, DisplayFormatEnum, ShuffleAnswersEnum
from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question

T = TypeVar("T", str, int, float, bool)
re_id = re.compile(r"""\[\[\"([^\"]*)\"\]\]""")


class ClozeQuestion(Question):
    """General template for a Cloze question."""

    QUESTION_TYPE = "cloze"
    XML_TEMPLATE = "cloze.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        subquestions: dict[str, dict[str, Any]] | None = None,
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)
        self.subquestions = self.build_cloze(subquestions if subquestions else {})

        self.fill_in_cloze()

    def validate(self) -> list[str]:
        return super().validate()

    def build_cloze(self, subquestions: dict[str, dict[str, Any]]) -> dict[str, str]:
        return {qid: self.__build_subquestion(qid, sq) for qid, sq in subquestions.items()}

    def fill_in_cloze(self) -> None:
        for match in re.finditer(re_id, self.question):
            cloze = self.subquestions.get(match.group(1), "")
            if cloze:
                self.question = self.question.replace(match.group(0), cloze)
            else:
                logger.warning(
                    f"Unable to find matching subquestion for placeholder {match.group(0)}."
                )

    @staticmethod
    def __build_subquestion(subquestion_id: str, question: dict[str, Any]) -> str:
        qtype = ClozeTypeEnum.from_str(question["type"])
        disp_format = DisplayFormatEnum.from_str(question.get("display_format", ""))
        shuffle_answers = ShuffleAnswersEnum.from_str(question.get("shuffle_answers", ""))
        answer_case_sensitive = question.get("answer_case_sensitive", False)

        qtype_final = ClozeQuestion.__determine_qtype(
            qtype, disp_format, shuffle_answers, answer_case_sensitive
        )

        width = question.get("width", 0)
        answers = question["answers"]
        widthanswer = ""

        if width > 0:
            # If width is set
            all_answers = [a["answer"] for a in answers]
            if not any(len(str(a)) >= width for a in all_answers):
                # if all answers have less chars than width,
                # just create a placeholder of lengthwidth
                widthanswer = "9" * width
            elif qtype == ClozeTypeEnum.NUMERICAL:
                # if the question is numerical, the width of the placeholder
                # should be the maximum of the answers + tolerance + 1
                widthanswer = str(max(a["answer"] + a["tolerance"] for a in answers) + 1)
            elif qtype == ClozeTypeEnum.SHORTANSWER:
                # if the question is shortanswer, the width of the placeholder
                # should be either the width or the length of the logest answer + 1
                widthanswer = "a" * max(max(len(str(a["answer"])) for a in answers) + 1, width)

            if widthanswer:
                answers.append({"answer": widthanswer, "points": 0, "feedback": ""})

        if shuffle_answers == ShuffleAnswersEnum.LEXICOGRAPHICAL:
            answers.sort(key=lambda x: x["answer"])

        if not any(a.get("points", 0) == 100 for a in answers):
            logger.error(
                f"In subquestion {subquestion_id}: At least one answer must have 100 points."
            )
            sys.exit(1)

        answers = "~".join([ClozeQuestion.__build_answer(a) for a in answers])

        return f"{{{question.get('weight', '')}:{qtype_final}:{answers}}}"

    @staticmethod
    def __determine_qtype(  # noqa: C901
        qtype: ClozeTypeEnum,
        disp_format: DisplayFormatEnum,
        shuffle_answers: ShuffleAnswersEnum,
        answer_case_sensitive: bool,
    ) -> str:
        disp_warn = False
        shuffle_warn = False
        case_warn = False
        dropdown_warn = False
        qtype_final = f"{qtype}"

        match (qtype, disp_format):
            case (ClozeTypeEnum.NUMERICAL, _):
                disp_warn = disp_format != DisplayFormatEnum.NONE
                shuffle_warn = shuffle_answers != ShuffleAnswersEnum.NONE
                case_warn = answer_case_sensitive
            case (ClozeTypeEnum.SHORTANSWER, _):
                qtype_final += f"{'_C' if answer_case_sensitive else ''}"
                disp_warn = disp_format != DisplayFormatEnum.NONE
                shuffle_warn = shuffle_answers != ShuffleAnswersEnum.NONE
            case (ClozeTypeEnum.MULTICHOICE, DisplayFormatEnum.DROPDOWN) | (
                ClozeTypeEnum.MULTICHOICE,
                DisplayFormatEnum.NONE,
            ):
                qtype_final += f"{'_S' if shuffle_answers == ShuffleAnswersEnum.SHUFFLE else ''}"
                case_warn = answer_case_sensitive
            case (ClozeTypeEnum.MULTICHOICE, DisplayFormatEnum.HORIZONTAL):
                qtype_final += f"_H{'S' if shuffle_answers == ShuffleAnswersEnum.SHUFFLE else ''}"
                case_warn = answer_case_sensitive
            case (ClozeTypeEnum.MULTICHOICE, DisplayFormatEnum.VERTICAL):
                qtype_final += f"_V{'S' if shuffle_answers == ShuffleAnswersEnum.SHUFFLE else ''}"
                case_warn = answer_case_sensitive
            case (
                (ClozeTypeEnum.MULTIRESPONSE, DisplayFormatEnum.VERTICAL)
                | (ClozeTypeEnum.MULTIRESPONSE, DisplayFormatEnum.NONE)
                | (ClozeTypeEnum.MULTIRESPONSE, DisplayFormatEnum.DROPDOWN)
            ):
                qtype_final += f"{'_S' if shuffle_answers == ShuffleAnswersEnum.SHUFFLE else ''}"
                case_warn = answer_case_sensitive
                dropdown_warn = disp_format == DisplayFormatEnum.DROPDOWN
            case (ClozeTypeEnum.MULTIRESPONSE, DisplayFormatEnum.HORIZONTAL):
                qtype_final += f"_H{'S' if shuffle_answers == ShuffleAnswersEnum.SHUFFLE else ''}"
                case_warn = answer_case_sensitive

        if disp_warn:
            logger.warning(f"`display_format` is not supported for {qtype} questions.")
        if shuffle_warn:
            logger.warning(f"`shuffle_answers` is not supported for {qtype} questions.")
        if case_warn:
            logger.warning(f"`answer_case_sensitive` is not supported for {qtype} questions.")
        if dropdown_warn:
            logger.warning(f"`display_format: dropdown` is not supported for {qtype} questions.")

        return qtype_final

    @staticmethod
    def __escape_cloze(text: T, is_answer: bool) -> T:
        """Escape special characters"""
        if not isinstance(text, str):
            return text
        if is_answer:
            return (
                text.replace("}", r"\}")
                .replace("#", r"\#")
                .replace("~", r"\~")
                .replace('"', "&quot;")
                .replace("\\", "\\\\")
                .replace("/", r"\/")
            )
        return text.replace("}", r"\}").replace("~", r"\~").replace("\n", "<br>")

    @staticmethod
    def __build_answer(a: dict[str, Any]) -> str:
        points = str(a["points"])
        answer = str(ClozeQuestion.__escape_cloze(a["answer"], True))
        tolerance = (":" + str(a["tolerance"])) if a.get("tolerance", 0) != 0 else ""
        feedback = (
            "#" + str(ClozeQuestion.__escape_cloze(a["feedback"], False))
            if a["feedback"] != ""
            else ""
        )

        return f"%{points}%{answer}{tolerance}{feedback}"


class ClozeQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_id: str) -> None:
        super().__init__(question_id, r"(.*?): (.*?)", "; ")
