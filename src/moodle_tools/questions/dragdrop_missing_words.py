from moodle_tools.enums import ShuffleAnswersEnum
from moodle_tools.questions.missing_words import MissingWordsQuestion


class DragDropMissingWordsQuestion(MissingWordsQuestion):
    QUESTION_TYPE = "ddwtos"
    XML_TEMPLATE = "dragdrop_missing_words.xml.j2"

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
        super().__init__(
            question=question,
            title=title,
            options=options,
            category=category,
            grade=grade,
            general_feedback=general_feedback,
            correct_feedback=correct_feedback,
            partial_feedback=partial_feedback,
            incorrect_feedback=incorrect_feedback,
            shuffle_answers=shuffle_answers,
            **flags,
        )
