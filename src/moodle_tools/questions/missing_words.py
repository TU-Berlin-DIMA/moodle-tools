import itertools
import re
from dataclasses import dataclass
from typing import cast

import dacite
from loguru import logger

from moodle_tools.enums import ShuffleAnswersEnum
from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import ParsingError, preprocess_text

re_solution_ref_number = re.compile(r"\[\[(\d+)\]\]")
re_id = re.compile(r"""\[\[\"([^\"]*)\"\]\]""")


@dataclass
class OptionItem:
    answer: str
    group: str | int
    ordinal: int = -1
    group_letter: str = ""
    infinite: bool | None = None

    def __hash__(self) -> int:
        return hash((self.answer, self.group))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OptionItem):
            return self.answer == other.answer and self.group == other.group
        return False


class MissingWordsQuestion(Question):
    QUESTION_TYPE = "gapselect"
    XML_TEMPLATE = "missing_words.xml.j2"

    options: list[OptionItem]

    def __init__(
        self,
        *,
        question: str,
        title: str,
        options: list[dict[str, str | int] | OptionItem],
        category: str | None = None,
        grade: float = 1.0,
        general_feedback: str = "",
        correct_feedback: str = "",
        partial_feedback: str = "",
        incorrect_feedback: str = "",
        shuffle_answers: ShuffleAnswersEnum = ShuffleAnswersEnum.SHUFFLE,
        **flags: bool,
    ) -> None:
        super().__init__(question, title, category, grade, general_feedback, **flags)

        if all(isinstance(option, dict) for option in options):
            if any(
                int(option.get("ordinal", 1)) < 1
                for option in cast("list[dict[str, str | int]]", options)
            ):
                raise ValueError("Ordinal values must be larger than 1.")

            self.options = [dacite.from_dict(OptionItem, option) for option in options]  # type: ignore
        elif all(isinstance(option, OptionItem) for option in options):
            self.options = cast("list[OptionItem]", options)
        else:
            raise ValueError(
                "Options must be either a list of dictionaries or a list of OptionItem instances."
            )

        self.correct_feedback = preprocess_text(correct_feedback, **flags)
        self.partial_feedback = preprocess_text(partial_feedback, **flags)
        self.incorrect_feedback = preprocess_text(incorrect_feedback, **flags)
        self.shuffle_answers = ShuffleAnswersEnum.from_str(shuffle_answers)

        if re_solution_ref_number.search(self.question):
            self.solution_reference_number_exists = True

        elif re_id.search(self.question):
            self.solution_reference_number_exists = False
        else:
            logger.error(
                'Found neither solution reference numbers ([[1]]) nor solution IDs [["ABC"]] '
                "in the question text. Did you quote the IDs within the double brackets?"
            )
            raise ValueError("No solution references or IDs found in the question text.")

        self.populate_ordinals()
        self.resolve_ids()
        self.sort_options()
        self.fill_missing_ordinals()

    def populate_ordinals(self) -> None:
        """If not all options contain an ordinal field, add ordinals."""
        # check if all options contain an ordinal field. If so, skip this step
        if not all(option.ordinal >= 0 for option in self.options):
            max_ordinal: int = max(option.ordinal for option in self.options)

            max_ordinal = max(max_ordinal, 0)

            visited_groups: set[str | int] = set()
            for i, option in enumerate(self.options):
                visited_groups.add(option.group)

                # do not add gaps in options if numbers are used for solution references
                option.ordinal = (
                    i + 1 + (len(visited_groups) - 1) * 3 + max_ordinal
                    if not self.solution_reference_number_exists
                    else i + 1
                )  # 1-indexed

        for option in self.options:
            group = option.group
            if isinstance(group, str) and group.isalpha():
                # if group is a letter, parse to number
                option.group = ord(group.lower()) - 96

    def resolve_ids(self) -> None:
        """Resolve IDs in the question text to solution reference numbers as required by moodle."""
        for match in re.finditer(re_id, self.question):
            matching_options = [
                option for option in self.options if option.answer == match.group(1)
            ]

            if len(matching_options) == 0:
                raise ParsingError(f"Option with ID {match.group(1)} not found in the options.")
            if len(matching_options) > 1:
                raise ParsingError(
                    f"Multiple options with ID {match.group(1)} found in the options."
                )

            self.question = self.question.replace(
                match.group(0), f"[[{matching_options[0].ordinal}]]"
            )

    def sort_options(self) -> None:
        """Sort options within groups based on shuffling algorithm."""
        if self.shuffle_answers == ShuffleAnswersEnum.LEXICOGRAPHICAL:
            ordinals_in_group = {}
            for option in self.options:
                if option.group not in ordinals_in_group:
                    ordinals_in_group[option.group] = iter([option.ordinal])
                else:
                    ordinals_in_group[option.group] = itertools.chain(
                        ordinals_in_group[option.group], [option.ordinal]
                    )

            options = sorted(self.options, key=lambda x: (x.group, x.answer))

            for _, option in enumerate(options):
                old_ord = option.ordinal
                new_ord = int(next(ordinals_in_group[option.group]))

                option.ordinal = new_ord
                self.question = re.sub(
                    rf"\[\[{old_ord}\]\]", f"[[!!NEWORD!!{new_ord}]]", self.question
                )

            self.question = self.question.replace("!!NEWORD!!", "")

            self.options = sorted(options, key=lambda x: x.ordinal)

    def fill_missing_ordinals(self) -> None:
        """Fill missing ordinals with blanks."""
        if not all(isinstance(option.group, int) for option in self.options):
            raise ParsingError("Group values must be integers at this stage.")

        # """get all ordinals"""
        ordinals = [option.ordinal for option in self.options]

        options_copy = self.options.copy()

        all_groups = {option.group for option in self.options}
        unused_groups = set(range(1, 20 + 1)) - cast("set[int]", all_groups)

        if len(unused_groups) == 0:
            raise ParsingError(
                "All groups are already used. Cannot insert placeholders with unused group."
            )

        max_unused_group = max(unused_groups, default=20)

        for i in range(1, max(ordinals) + 1):
            if i not in ordinals:
                options_copy.append(OptionItem(answer=".", group=max_unused_group, ordinal=i))

        # """add group_letter field for debugging"""
        for option in options_copy:
            option.group_letter = str(chr(cast("int", option.group) + 64))

        self.options = sorted(options_copy, key=lambda x: x.ordinal)

    def validate(self) -> list[str]:
        errors = super().validate()
        if not self.correct_feedback:
            errors.append("No feedback for correct answer provided.")
        if not self.partial_feedback:
            errors.append("No feedback for partially correct answer provided.")
        if not self.incorrect_feedback:
            errors.append("No feedback for incorrect answer provided.")
        return errors


class MissingWordsQuestionAnalysis(MultipleResponseQuestionAnalysis):
    def __init__(self, question_id: str) -> None:
        super().__init__(question_id, r"{(.*?)}", " ")

    def normalize_answers(self, response: str) -> dict[str, str]:
        answers: dict[str, str] = {}
        if not response:
            return answers
        response += self.separator
        for i, match in enumerate(re.finditer(self.answer_re, response, re.MULTILINE)):
            subquestion_answer = match.group(1)
            subquestion_text = str(i)
            subquestion_answer = self.normalize_response(subquestion_answer.strip())
            answers[subquestion_text] = subquestion_answer
        return answers
