from moodle_tools.enums import ShuffleAnswersEnum
from moodle_tools.questions.question import Question
from moodle_tools.utils import preprocess_text


class MatchingQuestion(Question):
    """General template for a Matching question."""

    QUESTION_TYPE = "matching"
    XML_TEMPLATE = "matching.xml.j2"

    def __init__(
        self,
        *,
        question: str,
        title: str,
        options: list[dict[str, str]],
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

        self.sort_answers()

    def sort_answers(self) -> None:
        if self.shuffle_answers == ShuffleAnswersEnum.LEXICOGRAPHICAL:
            self.options.sort(key=lambda x: x["answer"])

    def validate(self) -> list[str]:
        error_list = super().validate()

        options = [key for option in self.options for key in option]

        if options.count("answer") < 3:
            error_list.append("At least 3 answers are required.")

        if options.count("question") < 2:
            error_list.append("At least 2 questions are required.")

        return error_list
