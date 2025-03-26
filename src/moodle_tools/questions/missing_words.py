import itertools
import re
import sys
from typing import cast

from loguru import logger

from moodle_tools.enums import ShuffleAnswersEnum
from moodle_tools.questions.multiple_response import MultipleResponseQuestionAnalysis
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text

re_solution_ref_number = re.compile(r"\[\[(\d+)\]\]")
re_id = re.compile(r"""\[\[\"([^\"]*)\"\]\]""")


class MissingWordsQuestion(Question):
    QUESTION_TYPE = "gapselect"
    XML_TEMPLATE = "missing_words.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        options: list[dict[str, str | int]],
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

        self.options = options
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
        if not all("ordinal" in option for option in self.options):
            if not all(isinstance(option.get("ordinal", 0), int) for option in self.options):
                logger.error("Ordinal values must be integers.")
                sys.exit(1)

            max_ordinal: int = max(
                cast("int", option.get("ordinal", 0)) for option in self.options
            )

            visited_groups: set[str | int] = set()
            for i, option in enumerate(self.options):
                visited_groups.add(option["group"])

                # do not add gaps in options if numbers are used for solution references
                option["ordinal"] = (
                    i + 1 + (len(visited_groups) - 1) * 3 + max_ordinal
                    if not self.solution_reference_number_exists
                    else i + 1
                )  # 1-indexed

        for option in self.options:
            group = option.get("group")
            if isinstance(group, str) and group.isalpha():
                # if group is a letter, parse to number
                option["group"] = ord(group.lower()) - 96

    def resolve_ids(self) -> None:
        """Resolve IDs in the question text to solution reference numbers as required by moodle."""
        for match in re.finditer(re_id, self.question):
            for option in self.options:
                if option["answer"] == match.group(1):
                    self.question = self.question.replace(
                        match.group(0), f"[[{option['ordinal']}]]"
                    )

    def sort_options(self) -> None:
        """Sort options within groups based on shuffling algorithm."""
        if self.shuffle_answers == ShuffleAnswersEnum.LEXICOGRAPHICAL:
            ordinals_in_group = {}
            for option in self.options:
                if option["group"] not in ordinals_in_group:
                    ordinals_in_group[option["group"]] = iter([option["ordinal"]])
                else:
                    ordinals_in_group[option["group"]] = itertools.chain(
                        ordinals_in_group[option["group"]], [option["ordinal"]]
                    )

            options = sorted(self.options, key=lambda x: (x["group"], x["answer"]))

            for _, option in enumerate(options):
                old_ord = option["ordinal"]
                new_ord = int(next(ordinals_in_group[option["group"]]))

                option["ordinal"] = new_ord
                self.question = re.sub(
                    rf"\[\[{old_ord}\]\]", f"[[!!NEWORD!!{new_ord}]]", self.question
                )

            self.question = self.question.replace("!!NEWORD!!", "")

            self.options = sorted(options, key=lambda x: x["ordinal"])

    def fill_missing_ordinals(self) -> None:
        """Fill missing ordinals with blanks."""
        if not all(isinstance(option.get("ordinal", 0), int) for option in self.options):
            logger.error("Ordinal values must be integers.")
            sys.exit(1)

        if not all(isinstance(option.get("group", 0), int) for option in self.options):
            logger.error("Group values must be integers at this stage.")
            sys.exit(1)

        # """get all ordinals"""
        ordinals = [cast("int", option["ordinal"]) for option in self.options]

        if min(ordinals) < 1:
            logger.error("Ordinal values must be positive integers.")
            sys.exit(1)

        options_copy = self.options.copy()

        all_groups = {cast("int", option["group"]) for option in self.options}
        unused_groups = set(range(1, 20 + 1)) - all_groups

        if len(unused_groups) == 0:
            logger.error(
                "All groups are already used. Cannot insert placeholders with unused group."
            )
            sys.exit(1)

        max_unused_group = max(unused_groups, default=20)

        for i in range(1, max(ordinals) + 1):
            if i not in ordinals:
                options_copy.append({"answer": ".", "group": max_unused_group, "ordinal": i})

        # """add group_letter field for debugging"""
        for option in options_copy:
            option["group_letter"] = str(chr(cast("int", option["group"]) + 64))

        self.options = sorted(options_copy, key=lambda x: x["ordinal"])

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
